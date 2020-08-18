#!/usr/bin/env python3
"""Testing the client CLI.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import json
import logging
import os
import shutil
import tempfile
from typing import List
from unittest import TestCase
from unittest.mock import patch, Mock, MagicMock

import responses
from pybloomfilter import BloomFilter, b64encode
from responses import GET, POST

import client
from lib import config
from lib.base_client import UserType
from lib.record import Record
from lib.similarity_metrics import RelativeOffsetIterator


@patch("lib.config.RECORD_LENGTH", 5)
@patch("lib.config.BLOOM_CAPACITY", 100)
@patch("lib.config.BLOOM_ERROR_RATE", 10 ** -5)
@patch("lib.config.RECORD_ID_LENGTH", 2)
@patch("lib.config.ROUNDING_VEC", [3, 3])
class ClientTest(TestCase):
    test_dir = config.DATA_DIR + "test/"
    c = client.Client("userA")
    enc_keys = [
        b'\x1b\x8fL+\xd2\xfcLQ\x1a\x03:\xcf\x15\x8a\xc7+'
        for _ in range(10)
    ]
    enc_keys_int = [int.from_bytes(i, 'big') for i in enc_keys]
    hash_key = b'hash_key'

    @classmethod
    @patch("lib.config.RECORD_LENGTH", 5)
    @patch("lib.config.BLOOM_CAPACITY", 100)
    @patch("lib.config.BLOOM_ERROR_RATE", 10 ** -5)
    @patch("lib.config.RECORD_ID_LENGTH", 2)
    @patch("lib.config.ROUNDING_VEC", [3, 3])
    def setUpClass(cls) -> None:
        """Disable logging."""
        logging.getLogger().setLevel(logging.FATAL)
        shutil.rmtree(cls.test_dir, ignore_errors=True)
        os.makedirs(cls.test_dir, exist_ok=True)

        cls.records = [
            Record([0, 0, 0, 0, 0]),  # not in Bloom
            Record([1, 2, 3, 4, 5]),  # in Bloom
            Record([2, 2, 3, 4, 5]),  # in Bloom
            Record([3, 2, 3, 4, 5]),  # in Bloom
            Record([4, 2, 3, 4, 5]),  # not in Bloom
            Record([5, 2, 3, 4, 5]),  # not in Bloom
        ]

        for r in cls.records:
            r.set_hash_key(cls.hash_key)
        b = BloomFilter(100, 0.0001, cls.test_dir + "test.bloom")
        b.update([1, 2, 3, 4, 5, 6, 7, 8, 9, 'a', 'b', 'c'])
        b.add(b64encode(cls.records[1].get_long_hash()).decode())
        b.add(b64encode(cls.records[2].get_long_hash()).decode())
        b.add(b64encode(cls.records[3].get_long_hash()).decode())
        cls.b_encoded = b.to_base64().decode()
        cls.b = b
        cls.psi_ind = [cls.records[1].get_psi_index(),
                       cls.records[2].get_psi_index(),
                       cls.records[3].get_psi_index()
                       ]

    def setUp(self) -> None:
        """
        Deactivate PSI Mode.
        """
        self.c._psi_mode = False

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove Test files."""
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    @patch("lib.base_client.BaseClient.post")
    def test_get_record_success(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/retrieve_record")
        j = {
            'success': True,
            'records': [['hash', 'record1'], ['hash', 'record2']]
        }
        m.return_value.json.return_value = j
        res = self.c.get_record('hash')
        self.assertEqual(res, j['records'])
        m.assert_called_once_with(url, json={'hash': 'hash'})

    @patch("lib.base_client.BaseClient.post")
    def test_get_record_fail(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/retrieve_record")
        j = {
            'success': False,
            'msg': "No record for hash exists: 'record'"
        }
        m.return_value.json.return_value = j
        with self.assertRaises(RuntimeError) as cm:
            self.c.get_record("hash")
        self.assertIn("No record for hash exists: 'record'", str(cm.exception))
        m.assert_called_once_with(url, json={'hash': 'hash'})

    @patch.object(c, "_get_enc_keys", Mock(return_value=enc_keys))
    def test_batch_get_records(self):
        records = self.records[:5]
        enc_records = []
        for i, r in enumerate(records):
            enc_records.append(
                (
                    b64encode(r.get_long_hash()).decode(),
                    json.dumps(r.get_encrypted_record(self.enc_keys[i], b'0'))
                ))
        with patch.object(self.c, "_batch_get_encrpyted_records",
                          Mock(return_value=enc_records)):
            res = self.c.batch_get_records(self.records[:5])
        for r in res:
            # for comparison
            r.set_hash_key(self.hash_key)
        self.assertEqual(records, res)
        # Empty list
        with patch.object(self.c, "_batch_get_encrpyted_records",
                          Mock(return_value=[])):
            self.assertEqual([],
                             self.c.batch_get_records(self.records[:5]))

    @patch("lib.base_client.BaseClient.post")
    def test__batch_get_encrpyted_records_success(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/batch_retrieve_records")
        j = {
            'success': True,
            'records': [['hash1', 'record1'], ['hash2', 'record2']]
        }
        m.return_value.json.return_value = j
        hash_list = ['hash1', 'hash2', 'hash3']
        res = self.c._batch_get_encrpyted_records(hash_list)
        self.assertEqual(res, j['records'])
        m.assert_called_once_with(url, json={'hashes': hash_list})

    @patch("lib.base_client.BaseClient.post")
    def test__batch_get_encrypted_records_fail(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/batch_retrieve_records")
        j = {
            'success': False,
            'msg': "Missing POST value 'hashes'."
        }
        m.return_value.json.return_value = j
        hash_list = ['hash1', 'hash2', 'hash3']
        with self.assertRaises(RuntimeError) as cm:
            self.c._batch_get_encrpyted_records(hash_list)
        self.assertIn("Missing POST value 'hashes'.", str(cm.exception))
        m.assert_called_once_with(url, json={'hashes': hash_list})

    @patch("lib.base_client.BaseClient.get")
    def test_get_bloom_success(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/bloom")
        j = {
            'success': True,
            'bloom': self.b_encoded
        }
        m.return_value.json.return_value = j
        res = self.c._get_bloom_filter()
        res_b = res.to_base64()
        self.assertEqual(res_b, self.b_encoded.encode())
        m.assert_called_once_with(url)

    @patch("lib.base_client.BaseClient.get")
    def test_get_bloom_fail(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/bloom")
        j = {
            'success': False,
            'msg': "Failed to retrieve bloom filter: "
        }
        m.return_value.json.return_value = j
        with self.assertRaises(RuntimeError) as cm:
            self.c._get_bloom_filter()
        self.assertIn("Failed to retrieve bloom filter:", str(cm.exception))
        m.assert_called_once_with(url)

    def test_compute_matches_bloom_success(self):
        for v in [True, False]:
            with patch("lib.config.PARALLEL", v):
                with patch.object(self.c, "_get_bloom_filter", return_value=self.b):
                    rec_list = [self.records[1].record,
                                self.records[2].record,
                                self.records[4].record,
                                self.records[5].record]
                    self.c._hash_key = self.hash_key
                    m = MagicMock()
                    m.__iter__.return_value = rec_list
                    m.split.return_value = [m]
                    res = self.c.compute_matches_bloom(m)
                    self.assertEqual(res, [self.records[1], self.records[2]])
                    m.__iter__.return_value = [self.records[1].record, self.records[2].record,
                                               self.records[3].record, self.records[4].record,
                                               self.records[5].record]
                    res = self.c.compute_matches_bloom(m)
                    self.assertEqual(res, [self.records[1], self.records[2],
                                           self.records[3]])
                    m.__iter__.return_value = [self.records[4].record,
                                               self.records[5].record]
                    res = self.c.compute_matches_bloom(m)
                    self.assertEqual(res, [])

    def test_compute_matches_bloom_fail(self):
        self.c._psi_mode = True
        with patch.object(self.c, "_get_bloom_filter",
                          return_value=[]):
            with self.assertRaises(RuntimeError)as e:
                self.c.compute_matches_bloom(Mock)
            self.assertIn("PSI-Mode is enabled", str(e.exception))

    def test_compute_matches_psi_success(self):
        self.c._psi_mode = True
        self.c._hash_key = self.hash_key
        with patch.object(self.c, "_perform_psi", return_value=self.psi_ind):
            res = self.c.compute_matches_psi(
                [self.records[1].record, self.records[2].record,
                 self.records[4].record, self.records[5].record])
            self.assertEqual(res, [self.records[1], self.records[2]])
            res = self.c.compute_matches_psi(
                [self.records[1].record, self.records[2].record, self.records[3].record,
                 self.records[4].record, self.records[5].record])
            self.assertEqual(res, [self.records[1], self.records[2],
                                   self.records[3]])
            res = self.c.compute_matches_psi(
                [self.records[4].record, self.records[5].record])
            self.assertEqual(res, [])

    @patch("lib.config.RECORD_LENGTH", 10)
    @patch("lib.config.RECORD_ID_LENGTH", 10)
    def test_compute_matches_psi_fail(self):
        # No PSI Mode
        with patch.object(self.c, "_perform_psi",
                          return_value=[]):
            with self.assertRaises(RuntimeError)as e:
                self.c.compute_matches_psi(
                    [])
            self.assertIn("PSI-Mode is not enabled", str(e.exception))
            self.c._psi_mode = True
            with self.assertRaises(RuntimeError) as e:
                self.c.compute_matches_psi(
                    RelativeOffsetIterator(
                        [float(i + 1) for i in range(config.RECORD_LENGTH)],
                        10,
                        [6 for _ in range(config.RECORD_ID_LENGTH)]
                    )
                )
            self.assertIn("too large for PSI", str(e.exception))

    @patch.object(c, "_receive_psi", Mock(return_value=[1, 2, 3]))
    @patch("lib.base_client.BaseClient.get")
    @patch("lib.config.EVAL", False)
    def test__perform_psi(self, m):
        self.assertEqual([], self.c._perform_psi([]))
        url = (
            f"https://{config.STORAGESERVER_HOSTNAME}:"
            f"{config.STORAGE_API_PORT}/client/"
            f"psi")
        for tls in [True, False]:
            with patch("lib.config.PSI_TLS", tls):
                j = {
                    'success': True,
                    'tls': tls,
                    'host': '127.0.0.1',
                    'port': 1234,
                    'setSize': 100,
                    'msg': 'blub'
                }
                m.return_value.json.return_value = j
                res = self.c._perform_psi([1, 2, 3, 4, 5, 6])
                self.assertEqual([1, 2, 3], res)
                m.assert_called_once_with(url)
                m.reset_mock()
                j['success'] = False
                m.return_value.json.return_value = j
                with self.assertRaises(RuntimeError) as e:
                    self.c._perform_psi([1, 2, 3, 4, 5, 6])
                m.assert_called_once_with(url)
                m.reset_mock()
                self.assertEqual("PSI failed: blub", str(e.exception))
                j['success'] = True
                j['setSize'] = 1
                m.return_value.json.return_value = j
                with self.assertRaises(RuntimeError) as e:
                    self.c._perform_psi([1, 2, 3, 4, 5, 6])
                m.assert_called_once_with(url)
                m.reset_mock()
                self.assertEqual("Client Set larger than PSI Setsize.",
                                 str(e.exception))
                j['setSize'] = 100
                j['tls'] = not tls
                m.return_value.json.return_value = j
                with self.assertRaises(RuntimeError) as e:
                    self.c._perform_psi([1, 2, 3, 4, 5, 6])
                m.assert_called_once_with(url)
                m.reset_mock()
                self.assertIn("Mismatch", str(e.exception))

    @patch("lib.similarity_metrics.AbsoluteOffsetIterator")
    def test_compute_candidates(self, m):
        # Default
        r = [1, 2, 3]
        self.c.compute_candidates(r)
        m.assert_called_once_with(r, 1)
        # Non default
        self.c.compute_candidates(r, "offset-7.77")
        m.assert_called_with(r, 7.77)

    def test_parser(self):
        # Just syntax errors
        p = client.get_client_parser()
        self.assertTrue(isinstance(p, argparse.ArgumentParser))

    @responses.activate
    @patch("lib.config.OT_TLS", False)
    @patch("lib.config.EVAL", False)
    @patch("lib.config.OT_SETSIZE", 10)
    @patch("client.Client._receive_ots", Mock(return_value=enc_keys_int[:3]))
    @patch("client.Client.get_token", Mock(return_value="token"))
    def test_full_retrieve(self):
        c = client.Client("userA")
        target = [2.0, 2.0, 3.0, 4.0, 5.0]
        # Server Records:
        sr: List[Record] = [
            [2.01, 2.01, 3.3, 4.4, 5.0],  # Match
            [2.5, 4.4, 3.9, 5.0, 5.0],  # No Match
            [2.0, 7.0, 3.0, 4.0, 5.0],  # No Match
            [2.0, 2.0, 10.6, 10.0, 5.0],  # Match
            [3.0, 2.0, 3.0, 4.0, 5.0],  # No Match
            [2.01, 2.004, 5, 9, 5.0],  # Match
            [2.0, 2.0, 3.0, 4.0, 5.0]  # No Match
        ]
        # Server Bloom Filter
        tmp = tempfile.NamedTemporaryFile(delete=False)
        b = BloomFilter(len(sr), 0.00001, tmp.name)
        c.metric = "offset-0.01"
        for i, r in enumerate(sr):
            sr[i]: Record = Record(r)
            sr[i].set_hash_key(self.hash_key)
        matches = [sr[0], sr[3], sr[5]]
        for m in matches:
            b.add(b64encode(m.get_long_hash()).decode())
        b_encoded = b.to_base64().decode()
        # Responses
        # -----------------------------------------------------------
        # 1. Hash Key
        url = f"https://localhost:" \
              f"{config.KEY_API_PORT}/client/hash_key"
        j = {
            'success': True,
            'hash_key': b64encode(self.hash_key).decode()
        }
        responses.add(responses.GET, url, json=j, status=200)
        # 2. PSI
        url = (
            f"https://{config.STORAGESERVER_HOSTNAME}:"
            f"{config.STORAGE_API_PORT}/client/psi")
        j = {
            'success': True,
            'tls': False,
            'host': '127.0.0.1',
            'port': 1234,
            'setSize': 10
        }
        responses.add(GET, url, status=200, json=j)
        # 2. Bloom filter
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/bloom")
        j = {
            'success': True,
            'bloom': b_encoded
        }
        responses.add(GET, url, status=200, json=j)
        # 3. Encryption Keys
        url = f"https://localhost:" \
              f"{config.KEY_API_PORT}/client/key_retrieval?totalOTs=3"
        j = {
            'success': True,
            'port': 5000,
            'host': "127.0.0.1",
            'totalOTs': 3,
            'tls': False
        }
        responses.add(responses.GET, url, json=j, status=200)
        # 4. Ciphertexts
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.CLIENT}/batch_retrieve_records")
        j = {
            'success': True,
            'records': [
                (b64encode(m.get_long_hash()).decode(),
                 json.dumps(
                     m.get_encrypted_record(self.enc_keys[i], b'0'))
                 )
                for i, m in enumerate(matches)
            ]
        }
        responses.add(POST, url, status=200, json=j)
        # ---------------------------------------------------------------------
        for psi in [True, False]:
            with patch.object(c, "_receive_psi", Mock(return_value=[
                m.get_psi_index()
                for m in matches
            ])):
                c._psi_mode = psi
                res = c.full_retrieve(target)
            # Set hash key for comparison
            for r in res:
                r.set_hash_key(self.hash_key)
            # Compare
            self.assertEqual(matches, res)

    def test_activate_psi_mode(self):
        self.assertEqual(False, self.c._psi_mode)
        self.c.activate_psi_mode()
        self.assertEqual(True, self.c._psi_mode)

    @patch("client.log.debug", Mock(side_effect=RuntimeError))
    def test_full_error(self):
        with self.assertRaises(RuntimeError):
            self.c.full_retrieve([1, 2, 3])
