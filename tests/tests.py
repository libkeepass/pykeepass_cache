# -*- coding: utf-8 -*-

import unittest
from pykeepass_remote import PyKeePass as PyKeePass_orig
from pykeepass_remote import cached_databases as cached_databases_orig
import timeit
import os

base_dir = os.path.dirname(os.path.realpath(__file__))

def PyKeePass(filename, password=None, keyfile=None):
    return PyKeePass_orig(
        os.path.join(base_dir, filename),
        password=password,
        keyfile=os.path.join(base_dir, keyfile) if keyfile else None,
        socket_path='/tmp/pykeepass_test.sock',
        timeout=5
    )

def cached_databases():
    return cached_databases_orig(
        socket_path='/tmp/pykeepass_test.sock',
        timeout=5
    )

timeit_str = """
import os
from pykeepass_remote import PyKeePass
base_dir = os.path.dirname(os.path.realpath('{}'))
PyKeePass(
    os.path.join(base_dir, 'test4.kdbx'),
    password='password',
    keyfile=os.path.join(base_dir, 'test4.key'),
    socket_path='/tmp/pykeepass_test.sock',
    timeout=5
)
""".format(__file__)


class Tests(unittest.TestCase):

    # this test needs to run first
    def test_0_speedup(self):
        # test that database is cached and second opening is faster

        time1 = timeit.timeit(timeit_str, number=1)
        time2 = timeit.timeit(timeit_str, number=1)

        self.assertTrue(time2 < time1 / 4)

    def test_save(self):
        # test saving cached database

        kp = PyKeePass(
            'test4.kdbx',
            password='password',
            keyfile='test4.key',
        )

        kp.save(os.path.join(base_dir, 'test4_new.kdbx'))

        kp2 = PyKeePass(
            'test4_new.kdbx',
            password='password',
            keyfile='test4.key',
        )

    def test_cached_databases(self):
        kp = PyKeePass(
            'test4.kdbx',
            password='password',
            keyfile='test4.key',
        )

        self.assertTrue(
            os.path.join(base_dir, 'test4.kdbx') in cached_databases().keys()
        )

    def tearDown(self):
        path = os.path.join(base_dir, 'test4_new.kdbx')
        if os.path.exists(path):
            os.remove(path)

if __name__ == '__main__':
    unittest.main()
