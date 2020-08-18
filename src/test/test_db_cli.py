#!/usr/bin/env python3
"""Test of User Database CLI.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import io
import logging
import os
import sys
from unittest import TestCase
from unittest.mock import patch

from lib import config
from lib.base_client import UserType
from lib.helpers import captured_output

with patch("lib.user_database.db"), patch("flask.Flask"):
    from lib.db_cli import main

    class DBCLITestWithoutDB(TestCase):

        @classmethod
        def setUpClass(cls) -> None:
            """Disable Logging"""
            logging.getLogger().setLevel(logging.FATAL)

        def test_main(self):
            # no args
            with self.assertRaises(SystemExit):
                with captured_output():
                    main(UserType.CLIENT, [])

        def test_wrong_action(self):
            with self.assertRaises(SystemExit):
                with captured_output():
                    main(UserType.CLIENT, ['-o'])

    class DBCLITest(TestCase):

        @classmethod
        def setUpClass(cls) -> None:
            """Disable Logging"""
            logging.getLogger().setLevel(logging.FATAL)

        def setUp(self) -> None:
            """
            Block output of argparse.
            """
            text_trap = io.StringIO()  # Block print of argparse
            sys.stderr = text_trap
            sys.stdout = text_trap
            self.test_dir = config.DATA_DIR + "test/"
            os.makedirs(self.test_dir, exist_ok=True)

        @patch("lib.db_cli.user_db")
        def test_list(self, d):
            d.get_all_users.return_value = ['userA', 'userB', 'userC']
            # list
            with captured_output() as (out, err):
                main("User", ['-l'], self.test_dir)
                output = out.getvalue().strip()
                self.assertIn("0: userA\n1: userB\n2: userC", output)
            with captured_output() as (out, err):
                main("User", ['--list'], self.test_dir)
                output = out.getvalue().strip()
                self.assertIn("0: userA\n1: userB\n2: userC", output)

        @patch("lib.db_cli.user_db")
        def test_log(self, d):
            d.get_all_users.return_value = ['userA', 'userB', 'userC']
            with captured_output() as (out, err):
                main("User", ['-l'], self.test_dir, no_print=True)
                output = out.getvalue().strip()
                self.assertEqual("", output)

        @patch("lib.db_cli.user_db")
        def test_add(self, d):
            # Add User - Fail
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['-a', 'userD'], self.test_dir)
            self.assertIn("User ID and Password have to defined.",
                              out.getvalue().strip())
            d.add_user.assert_not_called()
            # Add User - Fail
            d.add_user.side_effect = ValueError("Test Error")
            with captured_output() as (out, err):
                main(UserType.CLIENT, [
                     '--add', 'userD', 'short'], self.test_dir)
                self.assertIn("Test Error", out.getvalue().strip())
            # Add User - Success
            d.add_user.side_effect = None
            with captured_output():
                main(UserType.CLIENT, ['-a', 'userD',
                                       'passwordD'], self.test_dir)
            d.add_user.assert_called_with(
                UserType.CLIENT, 'userD', 'passwordD')

        @patch("lib.db_cli.user_db")
        def test_get_token(self, u):
            # Token - Fail
            with self.assertLogs(level=logging.WARNING) as m:
                main(UserType.CLIENT, ['-t', 'userA'], self.test_dir)
                self.assertIn('User ID and Password have to defined.',
                              str(m.output))
            # Token - Fail due to wrong password
            u.verify_password.return_value = False
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['--get_token', 'userA', 'wrong'],
                     self.test_dir)
                self.assertIn('Incorrect password',
                              out.getvalue().strip())
            # Token - Success
            u.verify_password.return_value = True
            with captured_output():
                main(UserType.CLIENT, ['-t', 'userA',
                                       'passwordA'], self.test_dir)
            u.generate_token.assert_called_with(UserType.CLIENT, 'userA')

        @patch("lib.db_cli.user_db")
        def test_new_pw(self, d):
            # New Password - Fail
            with self.assertLogs(level=logging.WARNING) as m:
                main(UserType.CLIENT, [
                     '-n', 'newPassword', 'userA'], self.test_dir)
                self.assertIn('User ID and Password have to defined.',
                              str(m.output))
            # New Password - Fail
            d.update_password.side_effect = ValueError(
                "Password needs to have at least 8 characters")
            with self.assertLogs(level=logging.WARNING) as m:
                main(UserType.CLIENT, ['--new', 'short', 'userA', 'passwordA'],
                     self.test_dir)
                self.assertIn('Password needs to have at least 8 characters',
                              str(m.output))
            # New Password - Success
            d.update_password.side_effect = None
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['-n', 'newPassword', 'userA', 'passwordA'],
                     self.test_dir)
            self.assertTrue(d.verify_password(UserType.CLIENT, "userA",
                                              "newPassword"))

        @patch("lib.db_cli.user_db")
        def test_verify_password(self, d):
            # Verify Password - Fail
            with self.assertLogs(level=logging.WARNING) as m:
                main(UserType.CLIENT, ['--verify', 'userA'], self.test_dir)
                self.assertIn('User ID and Password have to defined.',
                              str(m.output))
            # Verify Password - Fail
            d.verify_password.return_value = False
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['--verify',
                                       'userA', 'wrong'], self.test_dir)
                self.assertIn('Password is not correct.',
                              out.getvalue().strip())
            # Verify Password - Success
            d.verify_password.return_value = True
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['--verify',
                                       'userA', 'passwordA'], self.test_dir)
                self.assertIn('Credentials are correct.',
                              out.getvalue().strip())

        @patch("lib.db_cli.user_db")
        def test_verify_token(self, d):
            # Verify Token - Fail
            with self.assertLogs(level=logging.INFO) as m:
                main(UserType.CLIENT, ['-s', "token"], self.test_dir)
                self.assertIn('User ID has to be defined.',
                              str(m.output))
            # Verify Token - Fail
            d.verify_token.return_value = False
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['--verify-token', 'wrong', 'userA', 'passwordA'],
                     self.test_dir)
                self.assertIn('Bad Token.',
                              out.getvalue().strip())
            # Verify Token - Success
            d.verify_token.return_value = True
            with captured_output() as (out, err):
                main(UserType.CLIENT, ['-s', 'token', 'userA', 'passwordA'],
                     self.test_dir)
                self.assertIn('Token correct. Token destroyed.',
                              out.getvalue().strip())
