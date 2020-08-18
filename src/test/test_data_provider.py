#!/usr/bin/env python3
"""Testing the data provider's CLI.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import json
import logging
import tempfile
from unittest import TestCase
from unittest.mock import patch

import responses

import data_provider as dp
from lib import config
from lib.base_client import UserType
from lib.helpers import to_base64
from lib.record import Record


@patch("lib.config.RECORD_LENGTH", 5)
class DataProviderTest(TestCase):
    d = dp.DataProvider('userA')

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        logging.getLogger().setLevel(logging.FATAL)

    @patch("lib.base_client.BaseClient.post")
    def test_store_record_fail(self, m):
        # Fail due to bad owner
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.OWNER}/store_record")
        j = {
            'success': False,
            'msg': f"Invalid POST data: Owner in JSON not authenticated owner."
        }
        m.return_value.json.return_value = j
        with self.assertRaises(RuntimeError) as cm:
            self.d._store_record_on_server(b"hash", "record",
                                           "non-existing-owner")
        m.assert_called_once()
        self.assertEqual(url, m.call_args[0][0])
        self.assertIn("Invalid POST",
                      str(cm.exception))

    @patch("lib.base_client.BaseClient.post")
    def test_store_record_success(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.OWNER}/store_record")
        j = {
            'success': True,
            'msg': None
        }
        m.return_value.json.return_value = j
        self.d._store_record_on_server(b"hash", {'cipher': "record"},
                                       "userA")
        m.assert_called_once()
        expected = json.dumps({
            'hash': to_base64(b"hash"),
            'record': {'cipher': "record"},
            'owner': 'userA'
        }).encode()
        m.called_with(url, json=expected)

    @patch("lib.base_client.BaseClient.post")
    def test_batch_store_records_fail(self, m):
        # Fail due to bad owner
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.OWNER}/batch_store_records")
        j = {
            'success': False,
            'msg': f"Invalid POST data: Owner in JSON not authenticated owner."
        }
        m.return_value.json.return_value = j
        with self.assertRaises(RuntimeError) as cm:
            self.d._batch_store_records_on_server([])
        m.assert_called_once_with(url, json=[])
        self.assertIn("Invalid POST",
                      str(cm.exception))

    @patch("lib.base_client.BaseClient.post")
    def test_batch_store_records_success(self, m):
        url = (f"https://{config.STORAGESERVER_HOSTNAME}:"
               f"{config.STORAGE_API_PORT}/"
               f"{UserType.OWNER}/batch_store_records")
        j = {
            'success': True,
            'msg': None
        }
        m.return_value.json.return_value = j
        self.d._batch_store_records_on_server([("hash",
                                                "record",
                                                "userA")])
        expected = [("hash", "record", "userA")]
        m.assert_called_once_with(url, json=expected)

    @responses.activate
    @patch("lib.config.EVAL", False)
    def test_store_records(self):
        """Kind of integrity test, we only mock the server responses."""
        # Define server response
        # 1 - Get token
        url = (f"https://{config.KEYSERVER_HOSTNAME}"
               f":{config.KEY_API_PORT}/provider/gen_token")
        j = {
            'success': True,
            'token': 'XIu2a9SDGURRTzQnJdDg19Ii_CS7wy810s3_Lrx-TY7Wvh2Hf0U4xLH'
                     'NwnY_byYJ71II3kfUXpSZHOqAxA3zrw'
        }
        responses.add(responses.GET, url, json=j, status=200)
        # 2 - Hash Key
        url = f"{self.d.KEYSERVER}/hash_key"
        hash_key = to_base64(int(1).to_bytes(16, 'big'))
        j = {
            'success': True,
            'hash_key': hash_key
        }
        responses.add(responses.GET, url, json=j, status=200)

        # 3 - Encryption Keys
        j = {
            'success': True,
            'port': 50000,
            'host': "127.0.0.1",
            'totalOTs': 10,
            'tls': config.OT_TLS
        }
        url = f"https://localhost:" \
              f"{config.KEY_API_PORT}/provider/key_retrieval?totalOTs=3"
        responses.add(responses.GET, url, json=j, status=200)
        # Remember to mock the OT

        r1 = Record([1.0, 2.1, 3.3, 4.4, 5.0])
        r2 = Record([1.0532, 2.15423, 3.3453, 4.4, 5.0])
        r3 = Record([1.52340, 2.1523, 3.35423, 4.4, 5.0])
        records = [r1, r2, r3]
        # Log in user
        self.d.set_password("password")

        with patch.object(self.d, "_receive_ots", return_value=[10, 9, 8]):
            # Mock OT
            with patch.object(self.d, "_batch_store_records_on_server",
                              return_value=True):
                self.d.store_records(records)

    def test_parser(self):
        # Just syntax errors
        p = dp.get_provider_parser()
        self.assertTrue(isinstance(p, argparse.ArgumentParser))

    def test_store_from_file(self):
        res = [
            Record([1, 2, 3, 4, 5]),
            Record([1, 2, 3, 5, 6])
        ]
        with patch.object(self.d, "store_records") as m:
            with tempfile.NamedTemporaryFile() as fd:
                fd.write(b'[1,2,3,4, 5]\n')
                fd.write(b'[1,2,3,5, 6]\n')
                fd.seek(0)
                self.d.store_from_file(fd.name)
            m.assert_called_with(res)
