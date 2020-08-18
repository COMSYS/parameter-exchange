#!/usr/bin/env python3
"""Test the key server backend.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
import pickle
import shutil
from unittest import TestCase, mock
from unittest.mock import Mock, patch

import lib.config as config
import lib.key_server_backend as key_server

logging.getLogger(config.KEY_LOGNAME).setLevel(logging.ERROR)
test_dir = config.DATA_DIR + "test/"


@patch("lib.config.DATA_DIR", test_dir)
@patch("lib.config.OT_SETSIZE", 20)
class TestKeyServer(TestCase):

    def setUp(self) -> None:
        """Clear test dir."""
        shutil.rmtree(test_dir, ignore_errors=True)

    @classmethod
    def setUpClass(cls) -> None:
        """Clear test directory."""
        shutil.rmtree(test_dir, ignore_errors=True)

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove test files."""
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_init(self):
        self.assertFalse(os.path.exists(test_dir))
        self.assertFalse(
            os.path.exists(test_dir + config.KEY_HASHKEY_PATH))
        self.assertFalse(os.path.exists(test_dir + config.KEY_ENCKEY_PATH))
        k = key_server.KeyServer(test_dir)  # generate new files
        generated_hash_key = k._hash_key
        generated_enc_keys = k._enc_keys
        # check that Files are created
        self.assertTrue(os.path.exists(test_dir + config.KEY_HASHKEY_PATH))
        self.assertTrue(os.path.exists(test_dir + config.KEY_ENCKEY_PATH))
        # Check that stored keys are same
        with open(test_dir + config.KEY_HASHKEY_PATH, 'rb') as fd:
            loaded_hash_key = pickle.load(fd)
        with open(test_dir + config.KEY_ENCKEY_PATH, 'rb') as fd:
            loaded_enc_keys = pickle.load(fd)
        self.assertEqual(generated_hash_key, loaded_hash_key)
        self.assertEqual(generated_enc_keys, loaded_enc_keys)
        # Test loading
        k2 = key_server.KeyServer(test_dir)
        self.assertEqual(generated_hash_key, k2._hash_key)

    def test_gen_key(self):
        with self.assertRaises(ValueError):
            # Keys should have byte length
            key_server.KeyServer._gen_key(5)
        self.assertTrue(isinstance(key_server.KeyServer._gen_key(16), bytes))

    def test_generate_hash_key(self):
        self.assertFalse(os.path.exists(test_dir))
        k = key_server.KeyServer(test_dir)
        old_hash_key = k._hash_key
        k._generate_hash_key()
        self.assertNotEqual(old_hash_key, k._hash_key)
        with open(test_dir + config.KEY_HASHKEY_PATH, 'rb') as fd:
            loaded_key = pickle.load(fd)
        self.assertEqual(k._hash_key, loaded_key)

    def test_generate_enc_keys(self):
        self.assertFalse(os.path.exists(test_dir))
        k = key_server.KeyServer(test_dir)
        old_enc_keys = k._enc_keys
        k._generate_enc_keys()
        self.assertNotEqual(old_enc_keys, k._enc_keys)
        with open(test_dir + config.KEY_ENCKEY_PATH, 'rb') as fd:
            loaded_keys = pickle.load(fd)
        self.assertEqual(k._enc_keys, loaded_keys)

    def test_offerOT(self):
        with patch("lib.config.OT_SETSIZE", 20):
            total_ots = 10
            port = 55555
            k = key_server.KeyServer(test_dir)
            m = Mock()
            with mock.patch("lib.key_server_backend.PyOTSender",
                            return_value=m):
                k.offer_ot(total_ots, port)
            int_keys = [int.from_bytes(i, 'big') for i in k._enc_keys]
            self.assertEqual(m.executeSame.call_args[0][0], int_keys)
        with patch("lib.config.OT_SETSIZE", 1000):
            with self.assertRaises(RuntimeError):
                config.OT_SETSIZE = 1000
                k.offer_ot(total_ots, port)

    @patch("lib.key_server_backend.KeyServer.__init__", Mock(return_value=None))
    def test_get_hash_key(self):
        k = key_server.KeyServer(test_dir)
        with self.assertRaises(RuntimeError):
            k.get_hash_key()
        k._hash_key = 5
        self.assertEqual(5, k.get_hash_key())
