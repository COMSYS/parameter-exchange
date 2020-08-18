#!/usr/bin/env python3
"""Test of storage server backend.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
import shutil
from unittest import TestCase, mock
from unittest.mock import Mock, patch

from flask import Flask
from pybloomfilter import BloomFilter

import lib.config as config
import lib.helpers as helpers
import lib.storage_server_backend as server
from lib.record import Record

l1 = [
    ('a', 'ciphertext1', 'owner'),
    ('b', 'ciphertext2', 'owner'),
    ('c', 'ciphertext3', 'owner'),
    ('d', 'ciphertext4', 'owner'),
    ('e', 'ciphertext5', 'owner'),
    ('f', 'ciphertext6', 'owner'),
    ('g', 'ciphertext7', 'owner'),
]
l2 = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
l3 = ['h', 'i', 'j', 'k', 'l', 'm']
test_dir = config.DATA_DIR + "test/"
mock_app = Flask(__name__)
mock_app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_dir}/{config.STORAGE_DB}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)


@patch("lib.config.BLOOM_CAPACITY", 20)
@patch("lib.config.BLOOM_ERROR_RATE", 0.01)
@patch("lib.config.RECORD_LENGTH", 5)
class StorageServerTest(TestCase):
    storage_db_path = test_dir + config.STORAGE_DB
    bloom_path = test_dir + config.BLOOM_FILE

    def setUp(self) -> None:
        """Create testing directories."""
        logging.getLogger().setLevel(logging.FATAL)
        shutil.rmtree(test_dir, ignore_errors=True)
        os.makedirs(test_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove Testing directories"""
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_bloom(self):
        s = server.StorageServer(test_dir)
        self.assertFalse(os.path.exists(self.bloom_path))
        with patch.object(s, "_initialize_bloom_filter") as m:
            b = s.bloom
            m.assert_called_once()
            b = BloomFilter(2, .1, self.bloom_path)
            b.add(5)
            c = s.bloom
            m.assert_called_once()  # No second call
            self.assertIn(5, c)

    def test_init(self):
        # Is Directory created?
        os.rmdir(test_dir)
        self.assertFalse(os.path.exists(test_dir))
        server.StorageServer(test_dir)
        self.assertTrue(os.path.exists(test_dir))

    @patch("lib.storage_server_backend.StoredRecord")
    def test_initialize_bloom_filter(self, m):
        m.query.all.return_value = []
        s = server.StorageServer(test_dir)

        # Update with contents from DB
        mock_records = []
        for l in l2:
            mo = Mock()
            mo.hash = l
            mock_records.append(mo)
        m.query.all.return_value = mock_records
        s._initialize_bloom_filter()
        b = s.bloom
        for e in l2:
            self.assertIn(e, b)
        for e in l3:
            self.assertNotIn(e, b)

    def test_store_record(self):
        s = server.StorageServer(test_dir)
        BloomFilter(20, 0.1, self.bloom_path)  # create bloom filter
        self.assertNotIn('a', s.bloom)
        with patch("lib.storage_server_backend.db") as db:
            s.store_record('a', 'record', 'owner')
        # Check bloom filter
        self.assertIn('a', s.bloom)
        # check db
        db.session.add.assert_called_once()

    def test_batch_store_records_db(self):
        with patch("lib.storage_server_backend.db") as db:
            server.StorageServer.batch_store_records_db(l1)
        # check db
        self.assertEqual(len(l2), db.session.add.call_count)

    def test_batch_store_records_bloom(self):
        s = server.StorageServer(test_dir)
        BloomFilter(20, 0.1, self.bloom_path)  # create bloom filter
        b = s.bloom
        for e in l2:
            self.assertNotIn(e, b)
        s.batch_store_records_bloom(l1)
        # Check bloom filter
        for e in l2:
            self.assertIn(e, b)

    def test_get_record(self):
        with patch.object(server.StorageServer, "batch_get_records") as c:
            server.StorageServer.get_record("hash", "client")
        c.assert_called_once_with(["hash"], "client")
        with self.assertRaises(ValueError) as e:
            with patch.object(server.StorageServer,
                              "batch_get_records",
                              return_value=[]):
                server.StorageServer.get_record('hash', "client")
        self.assertEqual(str(e.exception), "No record for hash exists: 'hash'")

    @patch("lib.storage_server_backend.StorageServer._add_to_billing_db",
           Mock())
    @patch("lib.storage_server_backend.StorageServer._add_to_transaction_db",
           Mock())
    @patch("lib.storage_server_backend.get_user",
           Mock())
    def test_batch_get_record(self):
        server.db.init_app(mock_app)
        with mock_app.test_request_context(), \
             patch.object(server.StorageServer, "bloom", new_callable=Mock()):
            server.db.create_all()
            s = server.StorageServer(test_dir)
            s.batch_store_records_db(l1)
            s.batch_store_records_bloom(l1)
            res = s.batch_get_records(l2[::2], "client")
        self.assertEqual(
            [(h, r) for (h, r, o) in l1[::2]],
            res
        )

    def test_get_bloom_filter(self):
        s = server.StorageServer(test_dir)
        b = BloomFilter(20, 0.01, self.bloom_path)  # create bloom filter
        b.update(l2)
        b64 = s.get_bloom_filter()
        b = BloomFilter.from_base64(f"{test_dir}bloom-test.bloom", b64)
        for e in l2:
            self.assertIn(e, b)
        for e in l3:
            self.assertNotIn(e, b)

    def test_offer_psi(self):
        port = 5555
        s = server.StorageServer()
        set = list(range(20))
        m = Mock()
        with mock.patch("lib.storage_server_backend.PyPSISender",
                        return_value=m):
            with mock.patch.object(server.StorageServer,
                                   "get_all_record_psi_hashes",
                                   return_value=set):
                s.offer_psi(22, port)
            self.assertEqual(config.PSI_SCHEME, m.execute.call_args[0][0])
            self.assertEqual(set, m.execute.call_args[0][1])
            set = list(range(100))
            mock.patch.object(s, "get_all_record_psi_hashes", return_value=set)
            with self.assertRaises(RuntimeError):
                with mock.patch.object(server.StorageServer,
                                       "get_all_record_psi_hashes",
                                       return_value=set):
                    s.offer_psi(22, port=port)

    def test_get_all_record_psi_hashes(self):
        records = []
        correct = []
        for i in range(10):
            r = Record([1, 2, 3, 4, 5])
            r.set_hash_key(b'fake_key')
            m = Mock()
            m.hash = helpers.to_base64(r.get_long_hash())
            records.append(m)
            correct.append(r.get_psi_index())
        with patch("lib.storage_server_backend.StoredRecord") as c:
            c.query.all.return_value = records
            s = server.StorageServer()
            res = s.get_all_record_psi_hashes()
        self.assertEqual(correct, res)

    @patch("lib.storage_server_backend.RecordRetrieval")
    @patch("lib.storage_server_backend.db")
    def test__add_to_transaction_db(self, db, RecordRetrieval):
        r1 = Record([1, 2, 3, 4, 5])
        r2 = Record([1.1, 2, 3, 4, 5])
        r3 = Record([1, 2.2, 3, 4, 5])
        r4 = Record([1.1, 2.2, 3, 4, 5])
        r5 = Record([1.2, 2.22, 3, 4, 5])
        recs = [r1, r2, r3, r4, r5]
        for r in recs:
            r.set_hash_key(b'hash-key')
        hashes = [helpers.to_base64(r.get_long_hash()) for r in recs]
        records = [Mock() for _ in range(5)]
        records[0].hash = helpers.to_base64(r1.get_long_hash())
        records[1].hash = helpers.to_base64(r1.get_long_hash())  # Same
        records[2].hash = helpers.to_base64(r3.get_long_hash())
        records[3].hash = helpers.to_base64(r4.get_long_hash())
        records[4].hash = helpers.to_base64(r5.get_long_hash())
        server.StorageServer._add_to_transaction_db(records, "client", hashes)
        self.assertEqual(1, RecordRetrieval.call_count)  # 2 owners
        expected = {
            "client": "client",
            "enc_keys_by_hash": 5,
            "enc_keys_by_records": 4
        }
        self.assertEqual(expected, RecordRetrieval.call_args[1])

    @patch("lib.storage_server_backend.Owner")
    @patch("lib.storage_server_backend.BillingInfo")
    @patch("lib.storage_server_backend.db")
    def test__add_to_billing_db(self, db: Mock, binfo: Mock, owner: Mock):
        mockA = Mock()
        mockA.owner = "OwnerA"
        mockA.username = "OwnerA"
        mockB = Mock()
        mockB.owner = "OwnerB"
        mockB.username = "OwnerB"
        t_mock = "transaction"
        records = [mockA for _ in range(5)]
        for _ in range(3):
            records.append(mockB)
        owner.query.filter_by.return_value.first = Mock(
            side_effect=[mockA, mockB, None])
        server.StorageServer._add_to_billing_db(records, "client", t_mock)
        self.assertEqual(2, binfo.call_count)  # 2 owners
        expected = [
            ({
                 "provider": mockA,
                 "count": 5,
                 "client": "client",
                 "transaction": "transaction"
            },),
            ({
                 "provider": mockB,
                 "count": 3,
                 "client": "client",
                 "transaction": "transaction"
            },)
        ]
        self.assertEqual(expected, binfo.call_args_list)
        with self.assertRaises(ValueError):
            server.StorageServer._add_to_billing_db(records, "client", t_mock)
