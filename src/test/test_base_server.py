#!/usr/bin/env python3
"""Test of the base server code.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import json
import logging
import shutil
from unittest import TestCase
from unittest.mock import patch

from flask import Flask

import lib.base_server as bserver
from lib import config
from lib.base_client import UserType
from lib.helpers import get_free_port

test_dir = config.DATA_DIR + "test/"
client = "client"
provider = "provider"
password = "password"
token = "token"


def mock_verify_pw(user_type, user, pw):
    """Mock method for password check with few overhead (without expensive
    hashing)."""
    return (user == client or user == provider) and pw == password


def mock_verify_token(user_type, user, tk):
    """Mock method for password check with few overhead (without expensive
        hashing)."""
    return (user == client or user == provider) and tk == token


class BaseServerTest(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        """Create mock app and remove old test data."""
        logging.getLogger().setLevel(logging.ERROR)
        shutil.rmtree(test_dir, ignore_errors=True)
        cls.app = get_mock_app()
        cls.client = cls.app.test_client()

    def setUp(self) -> None:
        """Enable log-in for testing."""
        self.app.config.update(LOGIN_DISABLED=False)

    def test_is_redis_online(self):
        self.assertFalse(bserver.is_redis_online(get_free_port()))

    def test_disable_login(self):
        with self.app.test_request_context('/'):
            self.app.config.update(LOGIN_DISABLED=True)
            self.assertTrue(bserver.verify_token('client', "user", "token"))

    @patch("lib.base_server.db")
    def test_verify_token(self, mock_db):
        with self.app.test_request_context('/'):
            mock_db.verify_token.side_effect = TypeError()
            with self.assertRaises(TypeError) as e:
                bserver.verify_token("wrong", "user", "token")
            mock_db.verify_token.side_effect = ValueError()
            self.assertFalse(bserver.verify_token(
                UserType.CLIENT, "non-existing-user", "token"))
            self.assertFalse(bserver.verify_token(
                UserType.OWNER, "non-existing-user", "token"))
            mock_db.verify_password.side_effect = None
            mock_db.verify_token = mock_verify_token
            self.assertFalse(bserver.verify_token(UserType.CLIENT, "client",
                                                  "wrong"))
            self.assertFalse(bserver.verify_token(UserType.OWNER,
                                                  "provider", "wrong"))
            self.assertTrue(bserver.verify_token(UserType.CLIENT, "client",
                                                 token))
            self.assertTrue(bserver.verify_token(UserType.OWNER, "provider",
                                                 token))

    @patch("lib.base_server.db")
    def test_verify_client_pw(self, mock_db):
        with self.app.test_request_context('/'):
            mock_db.verify_password.side_effect = ValueError()
            self.assertFalse(bserver.verify_client_pw("non-existing-user",
                                                      "wrong"))
            mock_db.verify_password.side_effect = None
            mock_db.verify_password = mock_verify_pw
            self.assertFalse(bserver.verify_client_pw("client", "wrong"))
            self.assertTrue(bserver.verify_client_pw("client", "password"))
            self.app.config.update(LOGIN_DISABLED=True)
            self.assertTrue(bserver.verify_client_pw("client", "wrong"))
            self.assertTrue(bserver.verify_client_pw("non-existing-user",
                                                     "wrong"))

    @patch("lib.base_server.db")
    def test_verify_provider_pw(self, mock_db):
        with self.app.test_request_context('/'):
            mock_db.verify_password.side_effect = ValueError()
            self.assertFalse(bserver.verify_provider_pw("non-existing-user",
                                                        "wrong"))
            mock_db.verify_password.side_effect = None
            mock_db.verify_password = mock_verify_pw
            self.assertFalse(bserver.verify_provider_pw("provider", "wrong"))
            self.assertTrue(bserver.verify_provider_pw("provider", "password"))
            self.app.config.update(LOGIN_DISABLED=True)
            self.assertTrue(bserver.verify_provider_pw("provider", "wrong"))
            self.assertTrue(bserver.verify_provider_pw("non-existing-user",
                                                       "wrong"))

    @patch("lib.base_server.db")
    def test_gen_token(self, mock_db):
        with self.app.test_request_context('/'):
            # Non existing user
            mock_db.generate_token.side_effect = ValueError(
                'Could not generate token: No user non-existing-user exists.')
            j = json.loads(bserver.gen_token(UserType.CLIENT,
                                             "non-existing-user").data)
            self.assertEqual(j['success'], False)
            self.assertEqual(j['msg'], "Could not generate token: No user "
                                       "non-existing-user exists.")
            j = json.loads(bserver.gen_token(UserType.OWNER,
                                             "non-existing-user").data)
            self.assertEqual(j['success'], False)
            self.assertEqual(j['msg'], "Could not generate token: No user "
                                       "non-existing-user exists.")

            # Success
            mock_db.generate_token.return_value = "new_token"
            mock_db.generate_token.side_effect = None
            j = json.loads(bserver.gen_token(UserType.CLIENT,
                                             "client").data)
            self.assertEqual(j['success'], True)
            self.assertEqual(j['token'], "new_token")
            j = json.loads(bserver.gen_token(UserType.OWNER,
                                             "provider").data)
            self.assertEqual(j['success'], True)
            self.assertEqual(j['token'], "new_token")


def get_mock_app() -> Flask:
    """Return a mock flask app with few overhead."""
    app = Flask(__name__)
    app.config.from_mapping(
        TESTING=True,
        DATA_DIR=test_dir,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_dir}/{config.STORAGE_DB}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False

    )
    return app
