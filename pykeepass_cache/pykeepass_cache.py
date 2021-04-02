#!/usr/bin/env python
# Evan Widloski - 2019-08-27
# pykeepass-cache - transparent caching for pykeepass

import rpyc
from rpyc.utils.server import ThreadedServer
from rpyc.utils.factory import unix_connect
from rpyc.lib.compat import get_exc_errno
from os.path import getmtime, abspath, expanduser, expandvars
from datetime import datetime
import daemon
import time

import socket
import sys
import os
import stat
import errno
import traceback

import logging

log = logging.getLogger('pykeepass_cache')

class MyService(rpyc.Service):

    databases = {}
    opentimes = {}

    def exposed_PyKeePass(self, filename, password=None, keyfile=None,
                 transformed_key=None):

        # expand filename to full path
        filename = abspath(expanduser(expandvars(filename)))

        # import pykeepass here to avoid importing all support libs clientside
        from pykeepass import PyKeePass

        # if database has not yet been opened or has been modified externally
        # open it
        mtime = datetime.fromtimestamp(getmtime(filename))
        if not filename in self.databases.keys() or mtime > self.opentimes[filename]:
            kp = PyKeePass(filename, password, keyfile)
            self.databases[filename] = kp
            self.opentimes[filename] = datetime.now()

        return self.databases[filename]

class MyServer(ThreadedServer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.service.server = self
        self.socket_path = kwargs['socket_path']
        self.listener_timeout = kwargs['listener_timeout']

    def accept(self):
        """ Copied from rpyc server.py
        Modified to shutdown server when socket times out and reset
        socket timer when client connects
        """

        while self.active:
            try:
                sock, addrinfo = self.listener.accept()
                # set/reset timeout after client connects
                self.listener.settimeout(self.listener_timeout)
            except socket.timeout:
                self.close()
            except socket.error:
                ex = sys.exc_info()[1]
                if get_exc_errno(ex) in (errno.EINTR, errno.EAGAIN):
                    pass
                else:
                    raise EOFError()
            else:
                break

        sock.setblocking(True)
        self.logger.info("accepted %s with fd %s", addrinfo, sock.fileno())
        self.clients.add(sock)
        self._accept_method(sock)

    def close(self):
        # remove socket and quit
        super().close()
        os.remove(self.socket_path)
        sys.exit()


def _fork_and_run(func, *, timeout, socket_path, no_start=False):
    """
    Connect to server and execute `func` remotely. Start server if not already running.

    Args:
        timeout (int): seconds until server shuts down, use None to run forever
        socket_path (str): desired path of socket for backend communication
        no_start (bool): don't start the background server

    Returns:
        return value of `func`
    """

    starting_path = os.getcwd()

    # if server is running, connect to it
    try:
        conn = unix_connect(
            socket_path,
        )
        return func(conn)

    except (FileNotFoundError, ConnectionRefusedError) as e:

        # if no_start provided and server not running, do nothing
        if no_start:
            raise e

        # handle ConnectionRefusedError - clean up old socket
        if os.path.exists(socket_path):
            if stat.S_ISSOCK(os.stat(socket_path).st_mode):
                os.remove(socket_path)
            else:
                log.warning('Encountered regular file at {}'.format(socket_path))

        # otherwise, fork server, then connect to it
        pid = os.fork()

        # parent process, run server as unix daemon
        if pid == 0:
            try:
                with daemon.DaemonContext():
                    os.chdir(starting_path)
                    server = MyServer(
                        MyService,
                        socket_path=socket_path,
                        protocol_config={
                            'allow_all_attrs': True,
                            'allow_setattr': True,
                            'allow_getattr': True,
                        },
                        # initial timeout before any client connects
                        listener_timeout=timeout
                    )
                    server.start()
            except Exception:
                import traceback
                open('/tmp/pykeepass_server_exception', 'w').write(traceback.format_exc())

        # child process
        else:
            # FIXME: is there a more robust way to start the client after the server?
            while not os.path.exists(socket_path):
                time.sleep(0.05)
            conn = unix_connect(
                socket_path,
            )
            return func(conn)


def cached_databases(timeout=600, socket_path='/tmp/pykeepass.sock'):
    """
    Return a dict of cached databases on the server

    Args:
        timeout (int): seconds until server shuts down, use None to run forever
        socket_path (str): desired path of socket for backend communication

    Returns:
        dictionary of currently opened PyKeePass databases on server,
            keyed by the full path to the database
    """

    func = lambda conn: conn.root.databases
    return _fork_and_run(func, timeout=timeout, socket_path=socket_path)


def PyKeePass(filename, password=None, keyfile=None, transformed_key=None,
              timeout=600, socket_path='/tmp/pykeepass.sock'):
    """
    Cache and open a PyKeePass database.  Drop-in replacement for pykeepass.PyKeePass.

    If the server isn't running, it will be started automatically.  If the
    database is already open (as determined by the full path to the database),
    it will be returned and the given credentials will not be used.


    Args:
        filename (str): same as pykeepass.PyKeePass
        password (str): same as pykeepass.PyKeePass
        keyfile (str): same as pykeepass.PyKeePass
        transformed_key (str): same as pykeepass.PyKeePass

        timeout (int): seconds until server shuts down
        socket_path (str): desired path of socket for backend communication

    Returns:
        PyKeePass object
    """

    func = lambda conn: conn.root.PyKeePass(filename, password, keyfile, transformed_key)
    return _fork_and_run(func, timeout=timeout, socket_path=socket_path)


def close(timeout=600, socket_path='/tmp/pykeepass.sock'):
    """
    Shut down background server

    Args:
        timeout (int): seconds until server shuts down, use None to run forever
        socket_path (str): desired path of socket for backend communication
    """

    func = lambda conn: conn.root.server.close()
    try:
        _fork_and_run(
            func,
            timeout=timeout,
            socket_path=socket_path,
            no_start=True
        )
    except EOFError:
        pass
