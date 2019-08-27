# pykeepass_remote

pykeepass_remote is a support library for [pykeepass](http://github.com/pschmitt/pykeepass).  It is a drop-in replacement for `pykeepass.PyKeePass` which caches databases in a background process to make database access faster.

This is useful in situations where the program is terminated between invocations (e.g. CLI scripts).  The background process will automatically shut down after 300 seconds.

### Usage

Use as a drop-in replacement for `pykeepass.PyKeePass`:

``` python
>>> from pykeepass_remote import PyKeePass
>>> kp = PyKeePass('test.kdbx', 'password', 'keyfile.key')
```

Significant speedup on database open times:

``` python
# initial open.  database decryption takes a long time
>>> timeit.timeit('from pykeepass_remote import PyKeePass;PyKeePass(\'test3.kdbx\', \'password\', \'test3.key\')', number=1)
1.2734863759251311

# database is now cached in background process and opening is nearly instantaneous
>>> timeit.timeit('from pykeepass_remote import PyKeePass;PyKeePass(\'test3.kdbx\', \'password\', \'test3.key\')', number=1)
0.006465494981966913
```

Configure background server timeout, socket path:

``` python
>>> kp = PyKeePass('test.kdbx', 'password', 'keyfile.key', timeout=60, socket_path='/tmp/pykeepass.sock)
```

### Tests

`python tests/tests.py`
