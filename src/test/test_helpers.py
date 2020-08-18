#!/usr/bin/env python3
"""Test class for helper functions.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import os
import shutil
import socket
import ssl
from unittest import TestCase
import multiprocessing as mp

import lib.config as config
import lib.helpers as helpers


class HelpersTest(TestCase):

    # noinspection DuplicatedCode
    def test_create_data_dir(self):
        testdir = config.DATA_DIR + '/test/'
        shutil.rmtree(testdir, ignore_errors=True)
        self.assertFalse(os.path.exists(testdir))
        self.assertFalse(os.path.exists(testdir + '/logs/'))
        helpers.create_data_dir(testdir)
        self.assertTrue(os.path.exists(testdir))
        self.assertTrue(os.path.exists(testdir + '/logs/'))

    def test_parse_list(self):
        l1_s = "[1,2,3,4,5]"
        l1 = [1., 2., 3., 4., 5.]
        l2_s = "[1,2.4123,3.45, 4.884231,5]\n"
        l2 = [1., 2.4123, 3.45, 4.884231, 5.]
        self.assertEqual(l1, helpers.parse_list(l1_s))
        self.assertEqual(l2, helpers.parse_list(l2_s))

    def test_port_free(self):
        self.assertTrue(helpers.port_free(60000))

    def test_port_free_false(self):
        for port in range(50000, 65535):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind(('', port))
            except OSError as e:  # pragma no cover
                if e.errno is 98 or e.errno is 48:
                    s.close()
                else:
                    raise e
            self.assertFalse(helpers.port_free(port))
            s.close()
            break
        with self.assertRaises(TypeError):
            helpers.port_free("string")

    def test_get_tls_context(self):
        ctx = helpers.get_tls_context(config.STORAGE_TLS_CERT,
                                      config.STORAGE_TLS_KEY)
        self.assertTrue(isinstance(ctx, ssl.SSLContext))

    def test_generate_auth_header(self):
        self.assertEqual(helpers.generate_auth_header("user", "pwd"),
                         [('Authorization', 'Basic dXNlcjpwd2Q=')])

    def test_base64(self):
        b = b'Test'
        self.assertEqual(b,
                         helpers.from_base64(helpers.to_base64(b)))

    def test_keys_to_int(self):
        ints = [1, 2, 3, 4, 5, 6, 7, 8]
        self.assertEqual(
            ints,
            helpers.keys_to_int(helpers.encryption_keys_from_int(ints))
        )

    def test_print_time(self):
        t = 10.0 / 1000
        self.assertEqual(
            "10.0ms",
            helpers.print_time(t)
        )
        t = 5.555
        self.assertEqual(
            "5.55s",
            helpers.print_time(t)
        )
        t = 340.600
        self.assertEqual(
            "5min 40.6s",
            helpers.print_time(t)
        )
        t = 8113.000
        self.assertEqual(
            "2h 15min 13.0s",
            helpers.print_time(t)
        )

    def test_queue_to_list(self):
        q = mp.Queue()
        q.put("A")
        q.put("B")
        q.put("C")
        self.assertEqual(
            ["A", "B", "C"],
            helpers.queue_to_list(q)
        )

    def test_get_temp_file(self):
        tmp = helpers.get_temp_file()
        self.assertIn(
            config.TEMP_DIR,
            tmp
        )
