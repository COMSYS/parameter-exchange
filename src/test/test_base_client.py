#!/usr/bin/env python3
"""Test of base client.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
from unittest import TestCase, mock
from unittest.mock import Mock, patch

import requests
import responses

from lib import base_client as bc
from lib import config
from lib.base_client import KEYSERVER, STORAGESERVER, ServerType
from lib.helpers import to_base64, encryption_keys_from_int


class Mockclient(bc.BaseClient):
    """Mock base client to test abstract base class."""
    type = 'mock'


class BaseClientTest(TestCase):
    choices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    int_keys = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    keys = encryption_keys_from_int(int_keys)
    m: Mockclient = None

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging."""
        logging.getLogger().setLevel(logging.FATAL)

    def setUp(self) -> None:
        self.m = Mockclient("testuser")

    def test_init(self):
        m = Mockclient("User1")
        self.assertEqual(m.type, "mock")
        self.assertEqual(m.user, "User1")

    @responses.activate
    @patch("lib.base_client.BaseClient.get_token", Mock(return_value="token"))
    def test_get_hash_key(self):
        url = f"{KEYSERVER}/mock/hash_key"
        j = {
            'success': True,
            'hash_key': to_base64(int(1).to_bytes(16, 'big'))
        }
        responses.add(responses.GET, url, json=j, status=200)

        # Success
        key = self.m.get_hash_key()
        self.assertEqual(int(1).to_bytes(16, 'big'), key)

    @patch("lib.base_client.BaseClient._receive_ots",
           Mock(return_value=int_keys))
    @patch("lib.base_client.BaseClient.get")
    @patch("lib.config.EVAL", False)
    @patch("lib.config.PARALLEL", False)
    def test_get_enc_keys(self, m):
        port = 50000
        url = f"{KEYSERVER}/mock/key_retrieval?totalOTs=10"

        # Failed retrieval
        j = {
            'success': False,
            'msg': 'Key retrieval failed: No total OT defined.'
        }
        m.return_value.json.return_value = j
        with self.assertRaises(RuntimeError):
            self.m._get_enc_keys(self.choices)
        # Called in different process
        m.assert_called_once_with(url)
        m.reset_mock()
        # TLS Mismatch
        config.OT_TLS = True
        j = {
            'success': True,
            'port': port,
            'host': "127.0.0.1",
            'totalOTs': 20,
            'tls': False
        }
        m.return_value.json.return_value = j
        with self.assertRaises(RuntimeError) as e:
            self.m._get_enc_keys(self.choices)
        m.reset_mock()
        self.assertIn(
            "Mismatch of server and client TLS settings.",
            str(e.exception))

        # Success empty list
        res = self.m._get_enc_keys([])
        self.assertEqual([], res)

        # Success with TLS
        j = {
            'success': True,
            'port': port,
            'host': "127.0.0.1",
            'totalOTs': 10,
            'tls': True
        }
        m.return_value.json.return_value = j

        res = self.m._get_enc_keys(self.choices)
        m.assert_called_once_with(url)
        m.reset_mock()
        # p.join()
        self.assertEqual(res, self.keys)

        # Success without TLS
        config.OT_TLS = False
        j = {
            'success': True,
            'port': port,
            'host': "127.0.0.1",
            'totalOTs': 10,
            'tls': False
        }
        m.return_value.json.return_value = j
        res = self.m._get_enc_keys(self.choices)
        m.assert_called_once_with(url)
        m.reset_mock()
        self.assertEqual(res, self.keys)

    @patch("lib.base_client.BaseClient._receive_ots")
    @patch("lib.base_client.BaseClient.get")
    @patch("lib.config.EVAL", False)
    @patch("lib.config.PARALLEL", True)
    @patch("lib.config.OT_MAX_NUM", 1)  # force parallel
    def test_parallel_enc_keys(self, m, _receive_ots):
        port = 50000
        url = f"{KEYSERVER}/mock/key_retrieval?totalOTs=10"

        # Failed retrieval
        j = {
            'success': False,
            'msg': 'Key retrieval failed: No total OT defined.'
        }
        m.return_value.json.return_value = j
        # Parallel execution
        config.OT_TLS = False
        j = {
            'success': True,
            'port': port,
            'host': "127.0.0.1",
            'totalOTs': 10,
            'tls': False
        }

        def mocked_receive(inds, h, p, tls):  # pragma no cover
            # (Thread)
            return [self.int_keys[j] for j in inds]

        _receive_ots.side_effect = mocked_receive

        m.return_value.json.return_value = j
        res = self.m._get_enc_keys(self.choices)
        self.assertEqual(res, self.keys)

    def test_receive_ots_without_tls(self):
        host = "127.0.0.1"
        port = 50000
        tls = False
        m = Mock()
        m.execute.return_value = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        with mock.patch("lib.base_client.PyOTReceiver", return_value=m):
            res = Mockclient._receive_ots(self.choices, host, port, tls,
                                          num_chosen_msgs=20)
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])

    def test_receive_ots_with_tls(self):
        host = "127.0.0.1"
        port = 50000
        tls = True
        m = Mock()
        m.execute.return_value = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        with mock.patch("lib.base_client.PyOTReceiver", return_value=m):
            res = Mockclient._receive_ots(self.choices, host, port, tls,
                                          num_chosen_msgs=20)
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])

    def test_receive_psi(self):
        m = Mock()
        m.execute.return_value = range(10)
        with mock.patch("lib.base_client.PyPSIReceiver", return_value=m):
            res = Mockclient._receive_psi(sorted(self.choices, reverse=True),
                                          "localhost", 5000, True)
        self.assertEqual(res, [9, 8, 7, 6, 5, 4, 3, 2, 1, 0])

    def test_set_password(self):
        m = Mockclient("client")
        self.assertIsNone(m.password)
        m.set_password("password")
        self.assertEqual(m.password, "password")

    @responses.activate
    def test_get_token_success(self):
        urlA = f"{KEYSERVER}/mock/gen_token"
        urlB = f"{STORAGESERVER}/mock/gen_token"
        j = {
            'success': True,
            'token': 'XIu2a9SDGURRTzQnJdDg19Ii_CS7wy810s3_Lrx-TY7Wvh2Hf0U4xLH'
                     'NwnY_byYJ71II3kfUXpSZHOqAxA3zrw'
        }
        responses.add(responses.GET, urlA, json=j, status=200)
        responses.add(responses.GET, urlB, json=j, status=200)

        # Success keyserver
        self.m.set_password("password")
        res = self.m.get_token(ServerType.KeyServer)
        self.assertEqual(res, j['token'])

        # Success storage server
        self.m.set_password("password")
        res = self.m.get_token(ServerType.StorageServer)
        self.assertEqual(res, j['token'])

    @responses.activate
    def test_get_token_fail(self):
        with self.assertRaises(ValueError):
            # no password defined
            self.m.get_token(ServerType.KeyServer)
        self.m.set_password("password")
        # Bad server type
        with self.assertRaises(ValueError):
            self.m.get_token("Bad-type")
        # Server Error
        url = f"{KEYSERVER}/mock/gen_token"
        j = {
            'success': False,
            'msg': "Not enough entropy."
        }
        responses.add(responses.GET, url, json=j, status=200)
        with self.assertRaises(RuntimeError):
            self.m.get_token(ServerType.KeyServer)

    @responses.activate
    @patch("lib.base_client.BaseClient.get_auth_data",
           Mock(return_value=("a", "b")))
    def test_get(self):
        url = "http://url"
        body = b"Test"
        auth = ("user", "password")
        method = responses.GET
        # Success via 200
        responses.add(method, url, body, status=200)
        res = self.m.get(url)  # Without auth
        self.assertEqual(body, res.content)
        # success via 202
        responses.replace(method, url, body, status=202)
        res = self.m.get(url, auth)
        self.assertEqual(body, res.content)
        # Authentication failed - 401
        responses.replace(method, url, body, status=401)
        with self.assertRaises(RuntimeError) as e:
            self.m.get(url, auth)
        self.assertIn("Authentication failed", str(e.exception))
        # Internal Server Error - 500
        responses.replace(method, url, body, status=500)
        with self.assertRaises(requests.exceptions.HTTPError):
            self.m.get(url, auth)

    @responses.activate
    @patch("lib.base_client.BaseClient.get_auth_data",
           Mock(return_value=("a", "b")))
    def test_post(self):
        url = "http://url"
        body = b"Test"
        auth = ("user", "password")
        json = {}
        method = responses.POST
        # Success via 200
        responses.add(method, url, body, status=200)
        res = self.m.post(url, json)  # without auth
        self.assertEqual(body, res.content)
        # success via 202
        responses.replace(method, url, body, status=202)
        res = self.m.post(url, json, auth)
        self.assertEqual(body, res.content)
        # Authentication failed - 401
        responses.replace(method, url, body, status=401)
        with self.assertRaises(RuntimeError) as e:
            self.m.post(url, json, auth)
        self.assertIn("Authentication failed", str(e.exception))
        # Internal Server Error - 500
        responses.replace(method, url, body, status=500)
        with self.assertRaises(requests.exceptions.HTTPError):
            self.m.post(url, json, auth)

    @patch("lib.base_client.BaseClient.get_token",
                  Mock(return_value='token'))
    def test_get_auth_data(self):
        with self.assertRaises(ValueError):
            self.m.get_auth_data("bad-url")
        self.assertEqual(
            (self.m.user, "token"),
            self.m.get_auth_data(KEYSERVER + "/something")
        )
        self.assertEqual(
            (self.m.user, "token"),
            self.m.get_auth_data(STORAGESERVER + "/something")
        )
