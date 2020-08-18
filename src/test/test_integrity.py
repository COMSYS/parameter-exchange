#! /usr/bin/env python3
"""Integrity Test for client application.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import contextlib
import json
import logging
import os
import shutil
import warnings
from typing import List
from unittest import TestCase
from unittest.mock import patch, Mock

from requests_flask_adapter import Session

import client
import data_provider
import key_server
import storage_server
from lib import config
from lib.helpers import to_base64
from lib.key_server_backend import KeyServer
from lib.record import Record
from lib.storage_server_backend import StorageServer
from lib.user_database import Client, Owner, db as user_db

test_dir = config.DATA_DIR + "test/"
loglvl = logging.ERROR


def mock_verify(pwhash, password):
    return pwhash == "pwd-hash"


def mock_insert(records):
    StorageServer(test_dir).batch_store_records_bloom(records)
    return Mock()


@patch("lib.config.EVAL", False)
@patch("lib.config.RECORD_ID_LENGTH", 2)
@patch("lib.config.ROUNDING_VEC", [3, 3])
@patch("lib.config.RECORD_LENGTH", 5)
@patch("lib.config.OT_TLS", True)
@patch("lib.config.BLOOM_CAPACITY", 100)
@patch("lib.config.BLOOM_ERROR_RATE", 10 ** -5)
@patch("lib.config.OT_SETSIZE", 10)
@patch("lib.config.PSI_SETSIZE", 450)  # 441 Candidates
@patch("key_server.connector.execute_ot", Mock())
@patch("storage_server.client.execute_psi", Mock())
@patch("storage_server.connector.insert_bloom.delay", mock_insert)
@patch("lib.user_database.generate_password_hash",
       Mock(return_value="pwd-hash"))
@patch("lib.user_database.check_password_hash", mock_verify)
@patch("lib.database.add_task", Mock())
class ClientIntegrityTest(TestCase):
    """
    Full integrity test, only OT and PSI mocked.
    """
    target = [1.0, 2.0, 3.0, 4.0, 5.5]
    # Server Records:

    enc_keys = [
        b'\x1b\x8fL+\xd2\xfcLQ\x1a\x03:\xcf\x15\x8a\xc7+'
        for _ in range(10)
    ]
    enc_keys_int = [int.from_bytes(i, 'big') for i in enc_keys]
    user = "testuser"
    provider = "testprovider"
    password = "password"
    test_config = {
        'TESTING': True,
        'DATA_DIR': test_dir,
        'CELERY_ALWAYS_EAGER': True  # Celery synchronous execution
    }

    @classmethod
    @patch("lib.config.OT_SETSIZE", 10)
    @patch("lib.config.RECORD_LENGTH", 5)
    @patch("lib.config.RECORD_ID_LENGTH", 2)
    @patch("lib.config.ROUNDING_VEC", [3, 3])
    def setUpClass(cls) -> None:
        """Disable logging."""

        logging.getLogger().setLevel(loglvl)
        warnings.filterwarnings("ignore", category=ResourceWarning)
        warnings.filterwarnings("ignore", category=ImportWarning)

        # Clear directory
        shutil.rmtree(test_dir, ignore_errors=True)
        os.makedirs(test_dir, exist_ok=True)

        # Records
        cls.sr: List[Record] = [
            Record([1.1, 2.01, 3.3, 4.4, 5.5]),  # Match
            Record([1.5, 4.4, 3.9, 5.0, 5.5]),  # No Match
            Record([1.0, 7.0, 3.0, 4.0, 5.5]),  # No Match
            Record([1.0, 2.0, 10.6, 10.0, 5.5]),  # Match
            Record([3.0, 2.0, 3.0, 4.0, 5.5]),  # No Match
            Record([1.1, 2.104, 5, 9, 5.5]),  # Match
            Record([2.0, 2.0, 3.0, 4.0, 5.5])  # No Match
        ]
        cls.matches = [
            cls.sr[0],
            cls.sr[3],
            cls.sr[5]
        ]

        # Generate hash and encryption keys
        key_backend = KeyServer(test_dir)
        cls.hash_key = key_backend._hash_key
        for r in cls.sr:
            r.set_hash_key(cls.hash_key)

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove Test files."""
        shutil.rmtree(test_dir, ignore_errors=True)

    @patch("lib.config.OT_TLS", True)
    @patch("lib.config.BLOOM_CAPACITY", 100)
    @patch("lib.config.BLOOM_ERROR_RATE", 10 ** -5)
    def setUp(self) -> None:
        with contextlib.suppress(FileNotFoundError):
            os.remove(test_dir + config.BLOOM_FILE)
            os.remove(test_dir + config.STORAGE_DB)
            os.remove(test_dir + config.KEYSERVER_DB)
        # Flask apps
        self.str_app = storage_server.create_app(
            self.test_config,
            logging_level=loglvl)
        self.key_app = key_server.create_app(self.test_config,
                                             logging_level=loglvl)
        Session.register('https://localhost:5000', self.key_app)
        Session.register('https://localhost:5001', self.str_app)
        # Create Fake users for Key Server
        with self.key_app.app_context():
            c = Client(username=self.user, password="pwd-hash")
            p = Owner(username=self.provider, password="pwd-hash")
            user_db.session.add(c)
            user_db.session.add(p)
            user_db.session.commit()
        # Create Fake users for Storage Server
        with self.str_app.app_context():
            c = Client(username=self.user, password="pwd-hash")
            p = Owner(username=self.provider, password="pwd-hash")
            user_db.session.add(c)
            user_db.session.add(p)
            user_db.session.commit()

    @patch("lib.storage_server_backend.StorageServer._add_to_billing_db",
           Mock())
    @patch("lib.config.PSI_MODE", False)
    def test_client_integrity_bpe(self):
        # Full Integrity Test including flask
        self.c = client.Client(self.user)
        self.c.set_password(self.password)
        self.c.metric = "offset-0.1"
        # Redirect requests to flask
        target = self.target
        # Server Records:
        matches: List[Record] = self.matches
        str_backend = StorageServer(test_dir)
        with self.str_app.app_context():
            for m in matches:
                str_backend.store_record(
                    to_base64(m.get_long_hash()),
                    json.dumps(m.get_encrypted_record(self.enc_keys[0])),
                    'OwnerA'
                )
        # PSI Matches
        psi_matches = []
        for m in matches:
            psi_matches.append(m.get_psi_index())

        s = Session(True)
        with patch("requests.get", s.get), \
                patch("requests.post", s.post), \
                patch.object(self.c, "_receive_ots",
                             Mock(return_value=self.enc_keys_int[:3])):
            res = self.c.full_retrieve(target)
        # Set hash key for comparison
        for r in res:
            r.set_hash_key(self.hash_key)
        # Compare without order
        for m in matches:
            self.assertIn(m, res)
        for r in res:
            self.assertIn(r, matches)

    @patch("lib.storage_server_backend.StorageServer._add_to_billing_db",
           Mock())
    @patch("lib.config.PSI_MODE", True)
    def test_client_integrity_psi(self):
        # Full Integrity Test including flask
        self.c = client.Client(self.user)
        self.c.set_password(self.password)
        self.c.metric = "offset-0.1"
        # Redirect requests to flask
        target = self.target
        # Server Records:
        matches: List[Record] = self.matches
        str_backend = StorageServer(test_dir)
        with self.str_app.app_context():
            for m in matches:
                str_backend.store_record(
                    to_base64(m.get_long_hash()),
                    json.dumps(m.get_encrypted_record(self.enc_keys[0])),
                    'OwnerA'
                )
        # PSI Matches
        psi_matches = []
        for m in matches:
            psi_matches.append(m.get_psi_index())

        s = Session(True)
        with patch("requests.get", s.get), \
                patch("requests.post", s.post), \
                patch.object(self.c, "_receive_psi",
                             Mock(return_value=psi_matches)), \
                patch.object(self.c, "_receive_ots",
                             Mock(return_value=self.enc_keys_int[:3])):
            res = self.c.full_retrieve(target)
        # Set hash key for comparison
        for r in res:
            r.set_hash_key(self.hash_key)
        # Compare without order
        for m in matches:
            self.assertIn(m, res)
        for r in res:
            self.assertIn(r, matches)

    @patch("lib.storage_server_backend.StorageServer._add_to_billing_db",
           Mock())
    @patch("lib.storage_server_backend.StorageServer._add_to_transaction_db",
           Mock())
    @patch("lib.storage_server_backend.get_user",
           Mock())
    def test_data_provider_int(self):
        # Full integrity Test including flask
        self.dp = data_provider.DataProvider(self.provider)
        self.dp.set_password(self.password)
        str_backend = StorageServer(test_dir)
        with self.str_app.app_context():
            for r in self.sr:
                # check that bloom filter is empty
                b = str_backend.bloom
                self.assertNotIn(to_base64(r.get_long_hash()), b)
            # Check that DB empty
            res = str_backend.batch_get_records(
                [to_base64(r.get_long_hash()) for r in self.sr],
                "client"
            )
        # Decrypt
        result = [
            Record.from_ciphertext(json.loads(r), self.enc_keys[0])
            for h, r in res
        ]
        self.assertEqual([], result)

        s = Session(True)
        with patch("requests.get", s.get), \
             patch("requests.post", s.post), \
             patch.object(self.dp, "_receive_ots",
                          Mock(return_value=self.enc_keys_int[:len(self.sr)])):
            self.dp.store_records(self.sr)

        str_backend = StorageServer(test_dir)
        with self.str_app.app_context():
            for r in self.sr:
                # check that records are in bloom filter
                b = str_backend.bloom
                self.assertIn(to_base64(r.get_long_hash()), b)
            # Check records in db
            res = str_backend.batch_get_records(
                [to_base64(r.get_long_hash()) for r in self.sr],
                "client"
            )
        # Decrypt
        result = [
            Record.from_ciphertext(json.loads(r), self.enc_keys[0])
            for h, r in res
        ]
        for m in self.sr:
            self.assertIn(m, result)
        for r in result:
            self.assertIn(r, self.sr)
