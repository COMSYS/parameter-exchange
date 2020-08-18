#!/usr/bin/env python3
"""Test user databases, i.e. Client and Data Provider DB.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
import shutil
from time import time
from unittest import TestCase
from unittest.mock import patch, Mock

from flask import Flask

from lib import user_database as ud, config
from lib.base_client import UserType

test_dir = config.DATA_DIR + "test/"


def create_mock_app():
    """Create a low overhead flask app for testing."""
    app = Flask(__name__)
    app.config.from_mapping(
        TESTING=True,
        DATA_DIR=test_dir,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_dir}/{config.STORAGE_DB}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    return app


class UserDBTest(TestCase):

    app = create_mock_app()
    username = "username"
    password = "password"
    token = "token"
    t = ud.Token(value=token)
    tokens = [t]

    @classmethod
    def setUpClass(cls) -> None:
        start = time()
        shutil.rmtree(test_dir, ignore_errors=True)
        os.makedirs(test_dir, exist_ok=True)
        ud.db.init_app(cls.app)
        cls.app.app_context().push()
        ud.db.create_all()
        # Add users
        cls.c = ud.Client(username=cls.username, password=cls.password)
        ud.db.session.add(cls.c)
        ud.db.session.commit()
        # print(f"setUpClass took: {1000 * (time() - start)}  ms")

    def setUp(self) -> None:
        """Clear test directory, remove logging"""
        logging.getLogger().setLevel(logging.ERROR)

    @classmethod
    def tearDownClass(cls) -> None:
        """Remove test directory."""
        shutil.rmtree(test_dir, ignore_errors=True)

    @patch("lib.user_database.generate_password_hash",
           return_value="token_hash")
    def test_generate_token(self, m):
        with self.assertRaises(ValueError):
            # User does not exist
            ud.generate_token(UserType.CLIENT, "bad")
        t = ud.generate_token(UserType.CLIENT, self.username)
        m.assert_called_once_with(t, salt_length=32)

    @patch("lib.user_database.check_password_hash", Mock(return_value=True))
    def test_verify_password(self):
        with self.assertRaises(ValueError):
            ud.verify_password(UserType.CLIENT, "user", "pwd")
        ud.verify_password(UserType.CLIENT, self.username, self.password)

    @patch("lib.user_database.check_password_hash")
    def test_verify_token(self, m):
        with self.assertRaises(ValueError):
            # User does not exist
            ud.verify_token(UserType.CLIENT, "user", "pwd")
        self.c.tokens = []
        ud.db.session.commit()
        with self.assertRaises(ValueError):
            # Token is none
            ud.verify_token(UserType.CLIENT, self.username, "pwd")
        self.c.tokens = self.tokens
        ud.db.session.commit()
        m.return_value = False
        self.assertFalse(
            ud.verify_token(UserType.CLIENT, self.username, self.token))
        m.return_value = True
        self.assertTrue(
            ud.verify_token(UserType.CLIENT, self.username, self.token))
        # Token has been removed
        self.assertEqual([], self.c.tokens)

    def test__generate_token(self):
        token = ud._generate_token()
        self.assertTrue(isinstance(token, str))
        self.assertEqual(len(token), 86)
        # Test "Randomness"
        l1 = []
        for _ in range(10):
            t = ud._generate_token()
            self.assertFalse(t in l1)
            l1.append(t)

    @patch("lib.user_database.check_password_hash")
    @patch("lib.user_database.generate_password_hash")
    def test_update_password(self, gen, m):
        m.return_value = False
        with self.assertRaises(ValueError):
            # Bad Login
            ud.update_password(UserType.CLIENT, self.username, "wrong-pwd",
                               "password")
        m.return_value = True
        with self.assertRaises(ValueError):
            # Pwd too short
            ud.update_password(UserType.CLIENT, self.username, self.password,
                               "pwd")
        gen.return_value = "new-password-hash"
        # change
        ud.update_password(UserType.CLIENT, self.username, self.password,
                           "new-password")
        # Verify
        gen.assert_called_once_with("new-password", salt_length=32)
        self.assertEqual("new-password-hash",
                         ud.Client.query.filter_by(
                             username=self.username).first().password)
        # change back
        self.c.password = self.password
        ud.db.session.commit()

    def test_get_all_users(self):
        res = ud.get_all_users(UserType.CLIENT)
        self.assertEqual([self.username], res)
        res = ud.get_all_users(UserType.OWNER)
        self.assertEqual([], res)

    @patch("lib.user_database.generate_password_hash",
           Mock(return_value="password"))
    def test_add_user(self):
        with self.assertRaises(ValueError):
            # Too Short pw
            ud.add_user(UserType.OWNER, "blub", "short")
        with self.assertRaises(ValueError):
            # User exists
            ud.add_user(UserType.CLIENT, self.username, self.password)
        self.assertEqual(
            None,
            ud.Owner.query.filter_by(username="new-user").first())
        ud.add_user(UserType.OWNER, "new-user", "new-password")
        user = ud.Owner.query.filter_by(username="new-user").first()
        self.assertNotEqual(
            None,
            user)
        ud.db.session.delete(user)
        ud.db.session.commit()

    def test_get_user_type(self):
        with self.assertRaises(TypeError):
            ud.get_user_type("Bad Type")
        self.assertEqual(ud.Client, ud.get_user_type(UserType.CLIENT))
        self.assertEqual(ud.Owner, ud.get_user_type(UserType.OWNER))

    def test_get_user(self):
        with self.assertRaises(ValueError):
            ud.get_user(UserType.CLIENT, "non-existing")
        self.assertEqual(self.c, ud.get_user(UserType.CLIENT, self.username))
