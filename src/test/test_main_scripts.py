#!/usr/bin/env python3
"""Hacky test for coverage of main files.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import os
import tempfile
import random_record_generator
import setuptools
from unittest import TestCase, mock, skip

import logging
from unittest.mock import patch


class TestMain(TestCase):

    def setUp(self) -> None:
        logging.getLogger().setLevel(logging.ERROR)

    def test_record_gen(self):
        f = tempfile.NamedTemporaryFile(delete=False)
        random_record_generator.main(["1", "-o", f"{f.name}"])
        os.remove(f.name)

    def test_setup(self):
        import warnings
        warnings.filterwarnings("ignore", category=ImportWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        with mock.patch.object(setuptools, "setup"):
            import setup
            self.assertIn("2019-ma-buchholz-code", setup.readme)
            self.assertIn("flask", setup.requirements)

    @skip("Slow an trivial.")
    @patch("lib.config.LOGLEVEL", logging.ERROR)
    def test_celery(self):  # pragma no cover
        import key_server.celery as c1
        import storage_server.celery as c2
        self.assertEqual('key_server', c1.app.name)
        self.assertEqual('storage_server', c2.app.name)
