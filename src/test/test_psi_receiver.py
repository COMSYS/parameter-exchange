#!/usr/bin/env python3
"""Test Class for PSIReceiver.

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

import PSIReceiver
from lib import config


@mock.patch("lib.config.PSI_SETSIZE", 20)
class PSIReceiverTest(TestCase):
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

    @mock.patch("PSIReceiver.PyPSIReceiver", m2)
    def test_receiving(self):
        res = PSIReceiver.main(["55"])
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.m.execute.assert_called_with("KKRT16",
                                          list(range(55)))

    @mock.patch("PSIReceiver.PyPSIReceiver", m2)
    def test_different_port(self):
        port = 50000
        res = PSIReceiver.main(["-p", "50000"])
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.assertEqual(self.m.port, port)
        self.m.execute.assert_called_with("KKRT16",
                                          list(range(config.PSI_SETSIZE)))

    @mock.patch("PSIReceiver.PyPSIReceiver", m2)
    def test_hostname(self):
        res = PSIReceiver.main(["-n", "localhost"])
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.assertEqual(self.m.hostName, "localhost")
        self.m.execute.assert_called_with("KKRT16",
                                          list(range(config.PSI_SETSIZE)))

    @mock.patch("PSIReceiver.PyPSIReceiver", m2)
    def test_scheme(self):
        res = PSIReceiver.main(["-s", "RR17"])
        self.assertEqual(res, [10, 9, 8, 7, 6, 5, 4, 3, 2, 1])
        self.m.execute.assert_called_with("RR17",
                                          list(range(config.PSI_SETSIZE)))
