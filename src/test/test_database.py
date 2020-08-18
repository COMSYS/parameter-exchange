#!/usr/bin/env python3
"""Test the key server database.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import contextlib
import logging
import os
from unittest import TestCase

from flask import Flask

from lib import config
from lib import database

test_dir = config.DATA_DIR + '/test/'
mock_app = Flask(__name__)
mock_app.config.from_mapping(
    SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_dir}/{config.KEYSERVER_DB}",
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)


class TestKeyDB(TestCase):

    def setUp(self) -> None:
        logging.getLogger().setLevel(logging.FATAL)
        os.makedirs(test_dir, exist_ok=True)
        with contextlib.suppress(FileNotFoundError):
            os.remove(test_dir + f"{config.KEYSERVER_DB}")
        database.db.init_app(mock_app)

    def test_add_get_task(self):
        with mock_app.test_request_context():
            database.db.create_all()
            t1 = database.Task(user_id="test-user", user_type="bluber",
                               id="123", task_type="nada")
            t2 = database.Task(user_id="test-user", user_type="bluber",
                               id="124", task_type="nada")
            database.add_task("test-user", "bluber", "123", "nada")
            database.add_task("test-user", "bluber", "124", "nada")
            res = database.get_tasks("bluber", "test-user")
            # We can't compare the whole objects because of the timestamps.
            self.assertEqual(t1.user_id, res[0].user_id)
            self.assertEqual(t1.user_type, res[0].user_type)
            self.assertEqual(t1.id, res[0].id)
            self.assertEqual(t1.task_type, res[0].task_type)
            self.assertEqual(t2.user_id, res[1].user_id)
            self.assertEqual(t2.user_type, res[1].user_type)
            self.assertEqual(t2.id, res[1].id)
            self.assertEqual(t2.task_type, res[1].task_type)
            res = database.get_tasks("bluber", "test-user2")
            self.assertEqual([], res)
            # Check representation
            self.assertEqual("<Task 123>", str(t1))
