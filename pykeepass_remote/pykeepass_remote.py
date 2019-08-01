import rpyc
from rpyc.utils.server import ThreadedServer
from os.path import getmtime
from datetime import datetime
import daemon
import time

import socket
import sys
import os
import errno
from rpyc.lib.compat import get_exc_errno

import logging

logger = logging.getLogger(__name__)

# class MyService(rpyc.Service):

#     databases = {}
#     opentimes = {}

#     def exposed_PyKeePass(self, filename, password=None, keyfile=None,
#                  transformed_key=None):

#         # if database has not yet been opened or has been modified externally
#         # open it
#         mtime = datetime.fromtimestamp(getmtime(filename))
#         if not filename in self.databases.keys() or mtime > self.opentimes[filename]:
#             kp = PyKeePass(filename, password, keyfile)
#             self.databases[filename] = kp
#             self.opentimes[filename] = datetime.now()

#         return self.databases[filename]
class MyService(rpyc.Service):

    databases = {}
    opentimes = {}

    def exposed_PyKeePass(self, filename, password=None, keyfile=None,
                 transformed_key=None):

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

    def __init__(self, listener_timeout=None, *args, **kwargs):
        super().__init__(*args, listener_timeout=listener_timeout, **kwargs)
        lkj
        # self.listener_timeout = listener_timeout

    def accept(self):
        """Copied from rpyc server.py"""

        while self.active:
            try:
                sock, addrinfo = self.listener.accept()
                # timeout after client connects
                self.listener.settimeout(self.listener_timeout)
            except socket.timeout:
                # instead of passing, quit
                sys.exit()
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


def PyKeePass(filename, password=None, keyfile=None, transformed_key=None,
              timeout=60, host='127.0.0.1', port=4444):

    starting_path = os.getcwd()

    # if server is running, connect to it
    try:
        conn = rpyc.connect(host, port)
        return conn.root.PyKeePass(filename, password, keyfile, transformed_key)

    except ConnectionRefusedError:

        # otherwise, fork server, then connect to it
        pid = os.fork()

        # parent process, run server() as unix daemon
        if pid == 0:

            with daemon.DaemonContext():
                os.chdir(starting_path)
                server = MyServer(
                    MyService,
                    port=port,
                    protocol_config={"allow_all_attrs": True},
                    # initial timeout before any client connects
                    listener_timeout=timeout
                )
                server.start()
        # child process
        else:
            time.sleep(1)
            conn = rpyc.connect(host, port)
            return conn.root.PyKeePass(filename, password, keyfile, transformed_key)
