#!/usr/bin/env python3
"""Test key server frontend flask application.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import json
import logging
import os
import socket
import warnings
from datetime import datetime, timedelta
from unittest import TestCase, skip
from unittest.mock import Mock, patch

from flask import g, current_app

import key_server
from key_server import connector
from key_server.connector import TaskType
from lib import config
from lib.base_client import UserType
from lib.database import Task
from lib.helpers import generate_auth_header, to_base64

test_dir = config.DATA_DIR + "test/"
correct_user = 'correct_user'
correct_pw = "correct_pw"
correct_tk = 'correct_token'


def mock_verify_token(user_type, user, token):
    """Inexpensive mock version of verify token."""
    if 'LOGIN_DISABLED' in current_app.config and current_app.config[
            'LOGIN_DISABLED']:
        return True  # pragma no cover
    return user == correct_user and token == correct_tk and user_type in [
        UserType.CLIENT, UserType.OWNER
    ]


def mock_verify_pw(user, pw):
    """Inexpensive mock version of verify password."""
    return user == correct_user and pw == correct_pw


class KeyCompTest(TestCase):
    user = correct_user
    tk = correct_tk
    pw = correct_pw

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging, create dummy flask app and pre-generate
        auth-headers"""
        logging.getLogger().setLevel(logging.ERROR)
        os.makedirs(test_dir, exist_ok=True)
        test_config = {
            'TESTING': True,
            'DATA_DIR': test_dir
        }
        cls.app = key_server.create_app(test_config,
                                        logging_level=logging.FATAL)
        cls.client = cls.app.test_client()
        cls.auth_header = generate_auth_header(correct_user,
                                               correct_tk)
        cls.auth_header_cor_pw = generate_auth_header(correct_user,
                                                      correct_pw)
        cls.auth_header_wrong_user = generate_auth_header("wrong",
                                                          correct_tk)
        cls.auth_header_wrong_pw = generate_auth_header(correct_user,
                                                        "wrong")

    def setUp(self) -> None:
        """Reset Login to be enabled."""
        self.app.config.update(LOGIN_DISABLED=False)

    # -------------------------------------------------------------------------
    # main.py------------------------------------------------------------------

    @patch("key_server.main.is_redis_online", Mock(return_value=False))
    @patch("key_server.main.render_template", Mock(return_value="Text"))
    @patch("key_server.main.is_celery_online", Mock(return_value=False))
    def test_main_true(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"Text", res.data)

    @patch("key_server.main.is_redis_online", Mock(return_value=False))
    @patch("key_server.main.render_template", Mock(return_value="Text"))
    @patch("key_server.main.is_celery_online", Mock(return_value=False))
    def test_main_false(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"Text", res.data)

    @patch("key_server.celery_app")
    def test_celery_status(self, m):
        m.control.inspect.return_value.ping.return_value = 1
        res = self.client.get('/celery')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"True", res.data)
        m.control.inspect.return_value.ping.return_value = None
        res = self.client.get('/celery')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"False", res.data)

    def test_favicon(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        # Bug of flask for unittests that leads to a 'ResourceWarning'
        res = self.client.get('/favicon.ico')
        self.assertEqual(res.status_code, 200)

    # -------------------------------------------------------------------------
    # connector.py-------------------------------------------------------------

    @patch.object(connector, "KeyServer", Mock)
    def test_get_keyserver_backend(self):
        with self.app.test_request_context('/'):
            self.assertFalse('keyserver' in g)
            connector.get_keyserver_backend()
            self.assertTrue('keyserver' in g)

    @patch.object(connector, "get_keyserver_backend")
    @patch.object(connector, "_add_to_hash_key_db", Mock())
    def test_get_hash_key(self, m):
        key = int(1).to_bytes(int(config.HASHKEY_LEN / 8), 'big')
        m.return_value.get_hash_key.return_value = key
        with self.app.test_request_context():
            res = connector.get_hash_key(UserType.CLIENT, "client")
            j = {
                'success': True,
                'hash_key': to_base64(key)
            }
            self.assertEqual(res, j)

    @patch("key_server.connector.execute_ot", Mock())
    @patch("key_server.database.db", Mock())
    @patch("key_server.connector._add_to_key_retrieval_db", Mock())
    def test_retrieve_keys(self):
        port = 1213
        host = "127.0.0.1"
        total_ots = 10
        tls = config.OT_TLS
        j = {
            'success': True,
            'port': port,
            'host': host,
            'totalOTs': total_ots,
            'tls': tls
        }
        with self.app.test_request_context('/'):
            # No total OTs argument defined
            res = connector.retrieve_keys(UserType.CLIENT, "client")
            self.assertFalse(res['success'])
            self.assertEqual(res['msg'], "No total OTs defined.")
        with self.app.test_request_context(f'/?totalOTs={total_ots}'):
            for user_type in [UserType.OWNER, UserType.CLIENT]:
                # Normal process without randomization
                self.app.config.update(KEY_RANDOMIZE_PORTS=False)
                res = connector.retrieve_keys(user_type, "client")
                # self.assertEqual(j, res)
                # Block port 1213
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.bind(('', 1213))
                except OSError:  # pragma no cover
                    # Already blocked
                    pass
                res = connector.retrieve_keys(user_type, "client")
                self.assertNotEqual(res['port'], 1213)
                s.close()
                # Normal process without randomization
                self.app.config.update(KEY_RANDOMIZE_PORTS=True)
                res = connector.retrieve_keys(user_type, "client")
                self.assertNotEqual(res['port'], 1213)
                self.assertEqual(res['success'], True)
                self.assertEqual(res['host'], host)
                self.assertEqual(res['totalOTs'], total_ots)
                self.assertEqual(res['tls'], tls)

    @skip("Slow b/c of celery and trivial")
    @patch.object(connector, "get_keyserver_backend")  # pragma no cover
    def test_execute_ot(self, m):
        mock_backend = Mock()
        m.return_value = mock_backend

        port = 50000
        total_ots = 10
        setsize = 20
        with self.app.test_request_context('/'):
            config.OT_SETSIZE = setsize
            connector.execute_ot.apply(args=(total_ots, port))
        mock_backend.offer_ot.assert_called_once_with(total_ots, port)

    # -------------------------------------------------------------------------
    # client.py----------------------------------------------------------------
    @patch("key_server.client.verify_token", mock_verify_token)
    @patch("key_server.client.get_hash_key", Mock(return_value=1))
    def test_client_verify_token(self):
        self.app.config.update(LOGIN_DISABLED=False)
        # No authentication info provided
        res = self.client.get('/client/hash_key')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Non existing User
        auth_head = self.auth_header_wrong_user
        res = self.client.get('/client/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Bad Token
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Correct
        auth_head = self.auth_header
        res = self.client.get('/client/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 200)

    # noinspection DuplicatedCode
    @patch("key_server.client.gen_token")
    def test_client_gen_token(self, m):
        m.return_value = {
            'success': True,
            'token': 'new-token'
        }
        from key_server.client import client_pw
        client_pw.verify_password(mock_verify_pw)  # Mock PW function

        # Test authentication bad PW
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/gen_token', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Test authentication bad username
        auth_head = self.auth_header_wrong_user
        res = self.client.get('/client/gen_token', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        auth_head = self.auth_header_cor_pw
        res = self.client.get('/client/gen_token', headers=auth_head)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['success'], True)
        self.assertEqual(res.json['token'], 'new-token')

    @patch("key_server.client.verify_token", mock_verify_token)
    @patch("key_server.client.get_hash_key", Mock(return_value=1))
    def test_client_get_hash_key(self):
        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        correct_json = 1
        auth_head = self.auth_header
        res = self.client.get('/client/hash_key', headers=auth_head)
        res_json = json.loads(res.data)
        self.assertEqual(res_json, correct_json)

    @patch("key_server.client.verify_token", mock_verify_token)
    @patch("key_server.client.retrieve_keys",
           Mock(return_value={'success': True}))
    def test_client_retrieve_keys(self):
        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/key_retrieval', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        auth_head = self.auth_header
        res = self.client.get('/client/key_retrieval', headers=auth_head)
        self.assertEqual(res.status_code, 200)

    @patch.object(connector.Tasks['OT'], "AsyncResult")
    @patch("key_server.connector.render_template", Mock())
    def test_status_overview(self, om):
        om.return_value.info = "blub"
        om.return_value.state = "FAILURE"
        om.return_value.id = "a"
        date1 = datetime.now()
        date2 = (datetime.now() + timedelta(days=1))
        for user_type in [UserType.CLIENT, UserType.OWNER]:
            mock_tasks = [
                Task(id='a', user_id="userA", task_type=TaskType.OT,
                     user_type=user_type, timestamp=date1),
                Task(id='b', user_id="userA", task_type=TaskType.OT,
                     user_type="client", timestamp=date2),
                Task(id='c', user_id="userA", task_type="Bad Task",
                     user_type=user_type, timestamp=date1)
            ]
            with patch("lib.database.get_tasks",
                       Mock(return_value=mock_tasks)):
                res = [
                    {
                        'id': 'b',
                        'status': "FAILURE",
                        'type': TaskType.OT,
                        'time': date2,
                        'error': "blub",
                        'task_url': f"/{user_type}/OT/status/a",
                        'kill_url': f"/{user_type}/OT/kill/a"
                    },
                    {
                        'id': 'a',
                        'status': "FAILURE",
                        'type': TaskType.OT,
                        'time': date1,
                        'error': "blub",
                        'task_url': f"/{user_type}/OT/status/a",
                        'kill_url': f"/{user_type}/OT/kill/a"
                    }
                ]
                with self.app.test_request_context('/'):
                    with self.assertRaises(ValueError):
                        # Bad User Type
                        connector.status_overview("bad_type")
                    with self.assertRaises(ValueError):
                        # Bad Task Type
                        connector.status_overview(user_type)
                    del (mock_tasks[2])
                    connector.status_overview(user_type)
                    self.assertEqual(res, g.tasks)

    @patch.object(connector.Tasks['OT'], "AsyncResult")
    @patch.object(connector, "get_keyserver_backend", Mock())
    def test_status(self, m):
        # Bad type
        self.assertIn("404 Not Found", connector.task_status("bad", "a")[0])
        self.assertEqual(404, connector.task_status("bad", "a")[1])
        m.return_value.id = "a"
        m.return_value.info = "blub"
        for t in [TaskType.OT]:
            m.return_value.state = "PENDING"
            r = connector.task_status(t, "a")
            self.assertEqual(r, {'state': "PENDING"})
            m.return_value.state = "SUCCESS"
            r = connector.task_status(t, "a")
            self.assertEqual(r, {'state': "SUCCESS"})
            m.return_value.state = "FAILURE"
            r = connector.task_status(t, "a")
            self.assertEqual(r,
                             {'state': "FAILURE", 'status': "blub"})

    @patch.object(connector.Tasks['OT'], "AsyncResult")
    @patch.object(connector, "get_keyserver_backend", Mock())
    def test_kill(self, m):
        # Bad type
        self.assertIn("404 Not Found", connector.kill_task("bad", "a")[0])
        self.assertEqual(404, connector.kill_task("bad", "a")[1])
        m.return_value.id = "a"
        m.return_value.info = "blub"
        for t in [TaskType.OT]:
            m.return_value.state = "PENDING"
            r = connector.kill_task(t, "a")
            self.assertEqual(
                {'success': False, 'msg': 'Task not running.'}, r
            )
            m.return_value.state = "STARTED"
            r = connector.kill_task(t, "a")
            self.assertEqual(
                {'success': True, 'msg': None}, r
            )

    # -------------------------------------------------------------------------
    # provider.py--------------------------------------------------------------
    @patch("key_server.provider.verify_token", mock_verify_token)
    @patch("key_server.provider.get_hash_key", Mock(return_value=1))
    def test_provider_verify_token(self):
        self.app.config.update(LOGIN_DISABLED=False)
        # No authentication info provided
        res = self.client.get('/provider/hash_key')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Non existing User
        auth_head = self.auth_header_wrong_user
        res = self.client.get('/provider/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Bad Token
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/provider/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Correct
        auth_head = self.auth_header
        res = self.client.get('/provider/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 200)

    # noinspection DuplicatedCode
    @patch("key_server.provider.gen_token")
    def test_provider_gen_token(self, m):
        m.return_value = {
            'success': True,
            'token': 'new-token'
        }
        from key_server.provider import provider_pw
        provider_pw.verify_password(mock_verify_pw)  # Mock PW function

        # Test authentication bad PW
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/provider/gen_token', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Test authentication bad username
        auth_head = self.auth_header_wrong_user
        res = self.client.get('/provider/gen_token', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        auth_head = self.auth_header_cor_pw
        res = self.client.get('/provider/gen_token', headers=auth_head)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['success'], True)

    @patch("key_server.provider.verify_token", mock_verify_token)
    @patch("key_server.provider.get_hash_key", Mock(return_value=1))
    def test_provider_get_hash_key(self):
        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/provider/hash_key', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        correct_json = 1
        auth_head = self.auth_header
        res = self.client.get('/provider/hash_key', headers=auth_head)
        res_json = json.loads(res.data)
        self.assertEqual(res_json, correct_json)

    @patch("key_server.provider.verify_token", mock_verify_token)
    def test_provider_retrieve_keys(self):
        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/provider/key_retrieval', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        with patch("key_server.provider.retrieve_keys") as m:
            m.return_value = {'success': True}
            auth_head = self.auth_header
            res = self.client.get('/provider/key_retrieval', headers=auth_head)
            self.assertEqual(res.status_code, 200)

    @patch("key_server.client.status_overview")
    @patch("key_server.provider.status_overview")
    def test_user_status(self, m, m2):
        # client and Provider
        m.return_value = "Test"
        m2.return_value = "Test"
        from key_server.client import client_pw
        from key_server.provider import provider_pw
        client_pw.verify_password(mock_verify_pw)  # Mock PW function
        provider_pw.verify_password(mock_verify_pw)

        for user_type in [UserType.CLIENT, UserType.OWNER]:
            # Test authentication
            auth_head = self.auth_header_wrong_pw
            res = self.client.get(f'/{user_type}/status', headers=auth_head)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.data, bytes('Unauthorized Access',
                                             encoding='UTF-8'))
            # Success
            auth_head = self.auth_header_cor_pw
            res = self.client.get(f'/{user_type}/status', headers=auth_head)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data, b"Test")

    @patch("key_server.client.task_status")
    @patch("key_server.provider.task_status")
    def test_task_status(self, m, m2):
        # client and Provider
        d = {'test': 'test'}
        m.return_value = d
        m2.return_value = d
        from key_server.client import client_pw
        from key_server.provider import provider_pw
        client_pw.verify_password(mock_verify_pw)  # Mock PW function
        provider_pw.verify_password(mock_verify_pw)

        for user_type in [UserType.CLIENT, UserType.OWNER]:
            # Test authentication
            auth_head = self.auth_header_wrong_pw
            res = self.client.get(f'/{user_type}/{TaskType.OT}/status/a',
                                  headers=auth_head)
            self.assertEqual(401, res.status_code)
            self.assertEqual(res.data, bytes('Unauthorized Access',
                                             encoding='UTF-8'))
            # Success
            auth_head = self.auth_header_cor_pw
            res = self.client.get(f'/{user_type}/{TaskType.OT}/status/a',
                                  headers=auth_head)
            self.assertEqual(200, res.status_code)
            self.assertEqual(d, res.json)

    @patch("key_server.client.kill_task")
    @patch("key_server.provider.kill_task")
    def test_task_kill(self, m, m2):
        # client and Provider
        d = {'test': 'test'}
        m.return_value = d
        m2.return_value = d
        from key_server.client import client_pw
        from key_server.provider import provider_pw
        client_pw.verify_password(mock_verify_pw)  # Mock PW function
        provider_pw.verify_password(mock_verify_pw)

        for user_type in [UserType.CLIENT, UserType.OWNER]:
            # Test authentication
            auth_head = self.auth_header_wrong_pw
            res = self.client.get(f'/{user_type}/{TaskType.OT}/kill/a',
                                  headers=auth_head)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.data, bytes('Unauthorized Access',
                                             encoding='UTF-8'))
            # Success
            auth_head = self.auth_header_cor_pw
            res = self.client.get(f'/{user_type}/{TaskType.OT}/kill/a',
                                  headers=auth_head)
            self.assertEqual(200, res.status_code)
            self.assertEqual(d, res.json)

    @patch("key_server.connector.HashKeyRetrieval", return_value="transaction")
    @patch("key_server.connector.get_user", Mock(return_value="user"))
    @patch("key_server.connector.db")
    def test__add_to_hash_key_db(self, db, h):
        with self.assertRaises(ValueError):
            connector._add_to_hash_key_db("bad_type", "blub")
        # Client
        connector._add_to_hash_key_db(UserType.CLIENT, "blub")
        h.assert_called_once_with(client="user")
        db.session.add.assert_called_once()
        self.assertEqual("transaction", db.session.add.call_args[0][0])
        db.session.commit.assert_called_once()
        h.reset_mock()
        db.reset_mock()
        # Provider
        connector._add_to_hash_key_db(UserType.OWNER, "blub")
        h.assert_called_once_with(provider="user")
        db.session.add.assert_called_once()
        self.assertEqual("transaction", db.session.add.call_args[0][0])
        db.session.commit.assert_called_once()

    @patch("key_server.connector.KeyRetrieval", return_value="transaction")
    @patch("key_server.connector.get_user", Mock(return_value="user"))
    @patch("key_server.connector.db")
    def test__add_to_key_retrieval_db(self, db, h):
        with self.assertRaises(ValueError):
            connector._add_to_key_retrieval_db("bad_type", "blub", 5)
        # Client
        connector._add_to_key_retrieval_db(UserType.CLIENT, "blub", 5)
        h.assert_called_once_with(client="user", retrieved_keys=5)
        db.session.add.assert_called_once()
        self.assertEqual("transaction", db.session.add.call_args[0][0])
        db.session.commit.assert_called_once()
        h.reset_mock()
        db.reset_mock()
        # Provider
        connector._add_to_key_retrieval_db(UserType.OWNER, "blub", 5)
        h.assert_called_once_with(provider="user", retrieved_keys=5)
        db.session.add.assert_called_once()
        self.assertEqual("transaction", db.session.add.call_args[0][0])
        db.session.commit.assert_called_once()
