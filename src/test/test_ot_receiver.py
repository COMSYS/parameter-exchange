#!/usr/bin/env python3
"""Test Class for OTReceiver

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import io
import logging
import sys
from unittest import TestCase, mock
from unittest.mock import Mock

import OTReceiver
from lib.helpers import captured_output


class OTReceiverTest(TestCase):

    m = Mock()
    m2 = Mock(return_value=m)

    @classmethod
    def setUpClass(cls) -> None:
        """Disable logging"""
        logging.getLogger().setLevel(logging.FATAL)
        cls.m.execute.return_value = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    def setUp(self) -> None:
        """Trap print output"""
        text_trap = io.StringIO()  # Block print of argparse
        sys.stderr = text_trap

    def test_main(self):
        with self.assertRaises(SystemExit):
            with captured_output():
                OTReceiver.main([])

    @mock.patch("OTReceiver.PyOTReceiver", m2)
    def test_receiving(self):
        total_ots = 10
        res = OTReceiver.main([str(total_ots)])
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])

    @mock.patch("OTReceiver.PyOTReceiver", m2)
    def test_different_port(self):
        total_ots = 10
        port = 50000
        res = OTReceiver.main([str(total_ots), "-p", "50000"])
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.assertEqual(self.m.port, port)
