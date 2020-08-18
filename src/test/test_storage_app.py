#!/usr/bin/env python3
"""Test storage server frontend flask application.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
import shutil
import warnings
from datetime import datetime, timedelta
from unittest import TestCase, skip
from unittest.mock import patch, Mock

from flask import g, current_app

import storage_server
from lib import config
from lib.base_client import UserType
from lib.database import Task
from lib.helpers import generate_auth_header
from storage_server import connector, client
from storage_server.connector import TaskType

test_dir = config.DATA_DIR + "test/"
correct_user = 'correct_user'
correct_pw = "correct_pw"
correct_tk = 'correct_token'
test_config = {
        'TESTING': True,
        'DATA_DIR': test_dir
}


def mock_verify_token(user_type, user, token):
    """Inexpensive mock version of verify token."""
    if 'LOGIN_DISABLED' in current_app.config and current_app.config[
            'LOGIN_DISABLED']:
        return True
    return user == correct_user and token == correct_tk and user_type in [
        UserType.OWNER, UserType.CLIENT
    ]


def mock_verify_pw(user, pw):
    """Inexpensive mock version of verify password."""
    return user == correct_user and pw == correct_pw


@patch("lib.config.BLOOM_CAPACITY", 100)
@patch("lib.config.BLOOM_ERROR_RATE", 10 ** -5)
class StorageAppTest(TestCase):
    user = correct_user
    tk = correct_tk
    pw = correct_pw

    @classmethod
    @patch("lib.config.BLOOM_CAPACITY", 100)
    @patch("lib.config.BLOOM_ERROR_RATE", 10 ** -5)
    def setUpClass(cls) -> None:
        """Disable logging, create test app and pre-generate auth headers."""
        logging.getLogger().setLevel(logging.FATAL)
        shutil.rmtree(test_dir, ignore_errors=True)
        os.makedirs(test_dir, exist_ok=True)
        cls.auth_header = generate_auth_header(correct_user, correct_tk)
        cls.auth_header_cor_pw = generate_auth_header(correct_user, correct_pw)
        cls.auth_header_wrong_user = generate_auth_header("wrong",
                                                          correct_tk)
        cls.auth_header_wrong_pw = generate_auth_header(correct_user,
                                                        "wrong")
        cls.app = storage_server.create_app(
            test_config,
            logging_level=logging.FATAL,
            data_dir=test_dir)
        cls.client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove tempfiles."""
        shutil.rmtree(test_dir, ignore_errors=True)

    def setUp(self) -> None:
        """Enable log-in."""
        self.app.config.update(LOGIN_DISABLED=False)

    # -------------------------------------------------------------------------
    # main.py------------------------------------------------------------------

    @patch("storage_server.main.is_redis_online", Mock(return_value=False))
    @patch("storage_server.main.render_template", Mock(return_value="Text"))
    @patch("storage_server.main.is_celery_online", Mock(return_value=False))
    def test_main_true(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"Text", res.data)

    @patch("storage_server.celery_app")
    def test_celery_status(self, m):
        m.control.inspect.return_value.ping.return_value = 1
        res = self.client.get('/celery')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"True", res.data)
        m.control.inspect.return_value.ping.return_value = None
        res = self.client.get('/celery')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"False", res.data)

    @patch("storage_server.main.is_redis_online", Mock(return_value=False))
    @patch("storage_server.main.render_template", Mock(return_value="Text"))
    @patch("storage_server.main.is_celery_online", Mock(return_value=False))
    def test_main_false(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(b"Text", res.data)

    def test_favicon(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        # Bug of flask for unittests that leads to a 'ResourceWarning'
        res = self.client.get('/favicon.ico')
        self.assertEqual(res.status_code, 200)

    # -------------------------------------------------------------------------
    # connector.py-------------------------------------------------------------
    @patch.object(connector, "StorageServer", Mock)
    def test_get_storageserver_backend(self):
        with self.app.test_request_context('/'):
            self.assertFalse('storageserver' in g)
            connector.get_storageserver_backend()
            self.assertTrue('storageserver' in g)

    @patch.object(connector, "StorageServer")
    @patch.object(connector, "insert_bloom")
    @patch.object(connector, "database")
    def test__batch_store_records(self, d, i, m):
        connector._batch_store_records([["test"]], self.user)
        m.batch_store_records_db.assert_called_once_with(
            [["test"]]
        )
        i.delay.assert_called_once_with([["test"]])
        d.add_task.assert_called_once()

    @skip("Slow b/c of celery and trivial.")
    @patch("storage_server.connector.StorageServer")
    def test_execute_psi(self, m):  # pragma no cover
        port = 50000
        with self.app.test_request_context('/'):
            connector.execute_psi.apply(args=(port,))
        m.offer_psi.assert_called_once_with(port=port)

    @patch.object(connector.Tasks['PSI'], "AsyncResult")
    @patch("storage_server.connector.render_template", Mock())
    def test_status_overview(self, om):
        om.return_value.info = "blub"
        om.return_value.state = "FAILURE"
        om.return_value.id = "a"
        date1 = datetime.now()
        date2 = (datetime.now() + timedelta(days=1))
        for user_type in [UserType.CLIENT, UserType.OWNER]:
            mock_tasks = [
                Task(id='a', user_id="userA", task_type=TaskType.PSI,
                     user_type=user_type, timestamp=date1),
                Task(id='b', user_id="userA", task_type=TaskType.PSI,
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
                        'type': TaskType.PSI,
                        'time': date2,
                        'error': "blub",
                        'task_url': f"/{user_type}/PSI/status/a",
                        'kill_url': f"/{user_type}/PSI/kill/a"
                    },
                    {
                        'id': 'a',
                        'status': "FAILURE",
                        'type': TaskType.PSI,
                        'time': date1,
                        'error': "blub",
                        'task_url': f"/{user_type}/PSI/status/a",
                        'kill_url': f"/{user_type}/PSI/kill/a"
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

    @patch.object(connector.Tasks['PSI'], "AsyncResult")
    @patch.object(connector, "get_storageserver_backend", Mock())
    def test_status(self, pm):
        # Bad type
        self.assertIn("404 Not Found", connector.task_status("bad", "a")[0])
        self.assertEqual(404, connector.task_status("bad", "a")[1])
        task = Mock()
        task.id = "a"
        task.info = "blub"
        pm.return_value = task
        for t in [TaskType.PSI]:
            task.state = "PENDING"
            r = connector.task_status(t, "a")
            self.assertEqual(r, {'state': "PENDING"})
            task.state = "SUCCESS"
            r = connector.task_status(t, "a")
            self.assertEqual(r, {'state': "SUCCESS"})
            task.state = "FAILURE"
            r = connector.task_status(t, "a")
            self.assertEqual(r,
                             {'state': "FAILURE", 'status': "blub"})

    @patch.object(connector.Tasks['PSI'], "AsyncResult")
    @patch.object(connector, "get_storageserver_backend", Mock())
    def test_kill(self, pm):
        # Bad type
        self.assertIn("404 Not Found", connector.kill_task("bad", "a")[0])
        self.assertEqual(404, connector.kill_task("bad", "a")[1])
        task = Mock()
        task.id = "a"
        task.info = "blub"
        pm.return_value = task
        for t in [TaskType.PSI]:
            task.state = "PENDING"
            r = connector.kill_task(t, "a")
            self.assertEqual(
                {'success': False, 'msg': 'Task not running.'}, r
            )
            task.state = "STARTED"
            r = connector.kill_task(t, "a")
            self.assertEqual(
                {'success': True, 'msg': None}, r
            )

    # -------------------------------------------------------------------------
    # client.py----------------------------------------------------------------
    @patch("storage_server.client.verify_token", mock_verify_token)
    @patch("storage_server.client.get_storageserver_backend")
    def test_client_verify_token(self, m):
        # Mock bloom filter
        m.return_value.get_bloom_filter.return_value.decode.return_value = 1

        # No authentication info provided
        res = self.client.get('/client/bloom')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Non existing User
        auth_head = self.auth_header_wrong_user
        res = self.client.get('/client/bloom', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Bad Token
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/bloom', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Correct
        auth_head = self.auth_header
        res = self.client.get('/client/bloom', headers=auth_head)
        self.assertEqual(res.status_code, 200)

    # noinspection DuplicatedCode
    @patch("storage_server.client.gen_token")
    def test_client_gen_token(self, m):
        m.return_value = {
            'success': True,
            'token': 'new-token'
        }
        from storage_server.client import client_pw
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
        self.assertEqual(res.json['token'], "new-token")

    @patch("storage_server.client.verify_token", mock_verify_token)
    @patch("storage_server.client.get_storageserver_backend")
    @patch("storage_server.client._track_bloom_access", Mock())
    def test_client_get_bloom(self, m):
        # Mock bloom filter
        m.return_value.get_bloom_filter.return_value.decode.return_value = 1

        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/bloom', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        auth_head = self.auth_header
        res = self.client.get('/client/bloom', headers=auth_head)
        self.assertEqual(res.status_code, 200)
        self.assertEqual({
            'success': True,
            'bloom': 1
        }, res.json)

    @patch("storage_server.client.verify_token", mock_verify_token)
    @patch("storage_server.client.StorageServer")
    def test_client_retrieve_record(self, m):

        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.post('/client/retrieve_record', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        self.app.config.update(LOGIN_DISABLED=True)
        # Empty POST
        res = self.client.post('/client/retrieve_record')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Missing POST value 'hash'."
        })
        # Bad POST - Wrong Key
        res = self.client.post('/client/retrieve_record', json={'T': False})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Missing POST value 'hash'."
        })
        # Success
        m.get_record.return_value = [['hash5', 'record5']]
        j = {'hash': 'hash5'}
        res = self.client.post('/client/retrieve_record', json=j)
        self.assertEqual(res.json, {
            'success': True,
            'records': [['hash5', 'record5']]
        })
        # Non existing hash
        m.get_record.side_effect = ValueError(
            "No record for hash exists: bad-hash")
        j = {'hash': 'bad-hash'}
        res = self.client.post('/client/retrieve_record', json=j)
        self.assertEqual(res.json, {
            'success': False,
            'msg': 'No record for hash exists: bad-hash'
        })

    @patch("storage_server.client.verify_token", mock_verify_token)
    @patch("storage_server.client.StorageServer")
    def test_client_batch_retrieve(self, m):
        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.post('/client/batch_retrieve_records',
                               headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        self.app.config.update(LOGIN_DISABLED=True)
        # Empty POST
        res = self.client.post('/client/batch_retrieve_records')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Missing POST value 'hashes'."
        })
        # Bad POST - Wrong Key
        res = self.client.post('/client/batch_retrieve_records',
                               json={'T': False})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Missing POST value 'hashes'."
        })
        # Success
        m.batch_get_records.return_value = [
            ['hash1', 'record1'],
            ['hash3', 'record3'],
            ['hash5', 'record5']
        ]
        j = {'hashes': ['hash1', 'hash3', 'hash5']}
        res = self.client.post('/client/batch_retrieve_records', json=j)
        self.assertEqual({
            'success': True,
            'records': [
                ['hash1', 'record1'],
                ['hash3', 'record3'],
                ['hash5', 'record5']
            ]
        }, res.json)
        # Non existing hash
        m.batch_get_records.return_value = []
        j = {'hashes': 'bad-hash'}
        res = self.client.post('/client/batch_retrieve_records', json=j)
        self.assertEqual(res.json, {
            'success': True,
            'records': []
        })

    @patch("storage_server.client.verify_token", mock_verify_token)
    @patch("storage_server.client._track_PSI_access", Mock())
    @patch("lib.database.add_task", Mock())
    def test_client_psi(self):
        # Test authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.get('/client/psi', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Success
        with patch("storage_server.client.execute_psi") as m:
            auth_head = self.auth_header
            res = self.client.get('/client/psi', headers=auth_head)
            self.assertEqual(res.status_code, 200)

    @patch("storage_server.client.get_user", Mock(return_value="user"))
    @patch("storage_server.client.BloomAccess", return_value="test")
    @patch("storage_server.client.db")
    def test__track_bloom_access(self, db, ba):
        with self.assertRaises(ValueError):
            client._track_bloom_access("bad_type", self.user)
        client._track_bloom_access(UserType.CLIENT, self.user)
        ba.assert_called_once_with(client="user")
        db.session.add.assert_called_once_with("test")
        db.session.commit.assert_called_once()

    @patch("storage_server.client.get_user", Mock(return_value="user"))
    @patch("storage_server.client.PSIAccess", return_value="test")
    @patch("storage_server.client.db")
    def test__track_psi_access(self, db, pa):
        with self.assertRaises(ValueError):
            client._track_PSI_access("bad_type", self.user)
        client._track_PSI_access(UserType.CLIENT, self.user)
        pa.assert_called_once_with(client="user")
        db.session.add.assert_called_once_with("test")
        db.session.commit.assert_called_once()

    # -------------------------------------------------------------------------
    # provider.py--------------------------------------------------------------
    @patch("storage_server.provider.verify_token", mock_verify_token)
    @patch("storage_server.provider.get_storageserver_backend", Mock())
    def test_provider_verify_token(self):
        # No authentication info provided
        res = self.client.post('/provider/store_record')
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Non existing User
        auth_head = self.auth_header_wrong_user
        res = self.client.post('/provider/store_record', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Bad Token
        auth_head = self.auth_header_wrong_pw
        res = self.client.post('/provider/store_record', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        # Correct
        auth_head = self.auth_header
        res = self.client.post('/provider/store_record', headers=auth_head)
        self.assertEqual(res.status_code, 200)

    # noinspection DuplicatedCode
    @patch("storage_server.provider.gen_token")
    def test_provider_gen_token(self, m):
        m.return_value = {
            'success': True,
            'token': 'new-token'
        }
        from storage_server.provider import provider_pw
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

    @patch("storage_server.provider.verify_token", mock_verify_token)
    def test_provider_store_record_failed(self):
        # Test Authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.post('/provider/store_record', headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        self.app.config.update(LOGIN_DISABLED=True)
        # Empty POST
        res = self.client.post('/provider/store_record')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Invalid POST data: Empty POST JSON."
        })
        # Bad POST - Missing 'hash'
        j = {'ciphertext': 'new-record', 'owner': 'userA'}
        res = self.client.post('/provider/store_record', json=j)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Invalid POST data: Require 'hash', 'ciphertext' and 'owner'."
        })
        # Bad POST - Missing 'ciphertext'
        j = {'hash': 'new-hash', 'owner': 'userA'}
        res = self.client.post('/provider/store_record', json=j)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Invalid POST data: Require 'hash', 'ciphertext' and 'owner'."
        })
        # Bad POST - Missing 'owner'
        j = {'hash': 'new-hash', 'ciphertext': 'new-record'}
        res = self.client.post('/provider/store_record', json=j)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Invalid POST data: Require 'hash', 'ciphertext' and 'owner'."
        })
        # Bad POST - wrong owner
        self.app.config.update(LOGIN_DISABLED=False)
        auth_head = self.auth_header
        j = {'hash': 'new-hash', 'ciphertext': 'new-record', 'owner': 'owner1'}
        res = self.client.post('/provider/store_record',
                               json=j, headers=auth_head)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Invalid POST data: Owner in JSON not authenticated owner."
        })

    @patch("storage_server.provider.verify_token", mock_verify_token)
    @patch("storage_server.provider.get_storageserver_backend")
    def test_provider_store_record_success(self, m):
        # Success
        auth_head = self.auth_header
        j = {'hash': 'new-hash', 'ciphertext': 'new-record', 'owner':
             'correct_user'}
        res = self.client.post('/provider/store_record',
                               json=j, headers=auth_head)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': True,
            'msg': None
        })
        m.return_value.store_record.assert_called_once_with(
            j['hash'],
            j['ciphertext'],
            j['owner']
        )
        # Exception
        m.return_value.store_record.side_effect = RuntimeError("Blub")
        res = self.client.post('/provider/store_record',
                               json=j, headers=auth_head)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Blub"
        })

    @patch("storage_server.provider.verify_token", mock_verify_token)
    def test_provider_batch_store_record_fail(self):
        # Test Authentication
        auth_head = self.auth_header_wrong_pw
        res = self.client.post('/provider/batch_store_records',
                               headers=auth_head)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data, bytes('Unauthorized Access',
                                         encoding='UTF-8'))
        self.app.config.update(LOGIN_DISABLED=True)
        # Empty POST
        res = self.client.post('/provider/batch_store_records')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Missing POST values."
        })
        # Non List POST
        j = {}
        res = self.client.post('/provider/batch_store_records', json=j)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "batch_store_records received non list: {}"
        })
        # Bad item to short
        j = [
            ('new-hash2', 'new-record2')
        ]
        res = self.client.post('/provider/batch_store_records', json=j)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Record list contained bad item: ['new-hash2', "
                   "'new-record2']"
        })
        # Bad item type
        j = [
            ('new-hash2', 'new-record2', 8)
        ]
        res = self.client.post('/provider/batch_store_records', json=j)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Record list contained bad item: ['new-hash2', "
                   "'new-record2', 8]"
        })
        # Wrong owner
        self.app.config.update(LOGIN_DISABLED=False)
        records = [
            ('new-hash2', 'new-record2', 'userA'),
            ('new-hash1', 'new-record1', 'owner'),
        ]
        auth_head = self.auth_header
        res = self.client.post('/provider/batch_store_records',
                               headers=auth_head, json=records)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json, {
            'success': False,
            'msg': "Different owner in record than authenticated owner!"
        })

    @patch("storage_server.provider.verify_token", mock_verify_token)
    @patch("storage_server.provider._batch_store_records")
    def test_provider_batch_store_record_success(self, m):
        # Success
        records = [
            ['new-hash1', 'new-record1', 'correct_user'],
            ['new-hash2', 'new-record2', 'correct_user'],
            ['new-hash3', 'new-record3', 'correct_user']
        ]
        auth_head = self.auth_header
        res = self.client.post('/provider/batch_store_records',
                               headers=auth_head, json=records)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(True, res.json['success'])
        self.assertEqual(None, res.json['msg'])
        m.assert_called_once_with(records, 'correct_user')

    @patch("storage_server.client.status_overview")
    @patch("storage_server.provider.status_overview")
    def test_user_status(self, m, m2):
        # client and Provider
        m.return_value = "Test"
        m2.return_value = "Test"
        from storage_server.client import client_pw
        from storage_server.provider import provider_pw
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

    @patch("storage_server.client.task_status")
    @patch("storage_server.provider.task_status")
    def test_task_status(self, m, m2):
        # client and Provider
        d = {'test': 'test'}
        m.return_value = d
        m2.return_value = d
        from storage_server.client import client_pw
        from storage_server.provider import provider_pw
        client_pw.verify_password(mock_verify_pw)  # Mock PW function
        provider_pw.verify_password(mock_verify_pw)

        for user_type in [UserType.CLIENT, UserType.OWNER]:
            # Test authentication
            auth_head = self.auth_header_wrong_pw
            res = self.client.get(f'/{user_type}/{TaskType.PSI}/status/a',
                                  headers=auth_head)
            self.assertEqual(401, res.status_code)
            self.assertEqual(res.data, bytes('Unauthorized Access',
                                             encoding='UTF-8'))
            # Success
            auth_head = self.auth_header_cor_pw
            res = self.client.get(f'/{user_type}/{TaskType.PSI}/status/a',
                                  headers=auth_head)
            self.assertEqual(200, res.status_code)
            self.assertEqual(d, res.json)

    @patch("storage_server.client.kill_task")
    @patch("storage_server.provider.kill_task")
    def test_task_kill(self, m, m2):
        # client and Provider
        d = {'test': 'test'}
        m.return_value = d
        m2.return_value = d
        from storage_server.client import client_pw
        from storage_server.provider import provider_pw
        client_pw.verify_password(mock_verify_pw)  # Mock PW function
        provider_pw.verify_password(mock_verify_pw)

        for user_type in [UserType.CLIENT, UserType.OWNER]:
            # Test authentication
            auth_head = self.auth_header_wrong_pw
            res = self.client.get(f'/{user_type}/{TaskType.PSI}/kill/a',
                                  headers=auth_head)
            self.assertEqual(res.status_code, 401)
            self.assertEqual(res.data, bytes('Unauthorized Access',
                                             encoding='UTF-8'))
            # Success
            auth_head = self.auth_header_cor_pw
            res = self.client.get(f'/{user_type}/{TaskType.PSI}/kill/a',
                                  headers=auth_head)
            self.assertEqual(200, res.status_code)
            self.assertEqual(d, res.json)
