#!/usr/bin/env python3
"""Test Cython Port of libOTe.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import multiprocessing
import sys
from unittest import TestCase, skip

from lib import config
from lib.helpers import get_free_port

config.OT_SETSIZE = 20  # noqa
# Necessary to overwrite because number of OTs problematic.

# Python Version of libOTe
sys.path.append(config.WORKING_DIR + 'cython/ot')
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTSender  # noqa
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTReceiver  # noqa


class OTTest(TestCase):
    values = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0, 1, 2, 3, 4, 5, 6, 7, 8,
              9]
    choices = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    def setUp(self) -> None:
        """Create receiver and Sender."""
        port = get_free_port()
        self.recv = self.get_receiver(port, False)
        self.sender = self.get_sender(port, False)
        self.port = port

    def ot_sender(self, port: int, tls: bool, mal_secure: bool):  # pragma no cover
        """Act as OT Sending Server to test receivers."""
        sender = PyOTSender()
        sender.totalOTs = len(self.choices)
        sender.port = port
        sender.numChosenMsgs = len(self.values)
        sender.serverKey = config.KEY_TLS_KEY
        sender.serverCert = config.KEY_TLS_CERT
        if mal_secure:
            sender.maliciousSecure = True
            sender.inputBitCount = 76
        else:
            sender.maliciousSecure = False
            sender.inputBitCount = 128
        sender.executeSame(self.values, tls)

    def ot_receiver(self, queue, tls: bool, mal_secure: bool):  # pragma no cover
        """Act as OT Reciever and write result into queue."""
        recv = PyOTReceiver()

        recv.totalOTs = len(self.choices)
        recv.numChosenMsgs = len(self.values)
        recv.hostName = "127.0.0.1"
        recv.port = self.port
        recv.rootCA = config.TLS_ROOT_CA
        if mal_secure:
            recv.maliciousSecure = True
            recv.inputBitCount = 76
        else:
            recv.maliciousSecure = False
            recv.inputBitCount = 128
        res = recv.execute(self.choices, tls)
        queue.put(res)

    @classmethod
    def get_receiver(cls, port: int, mal_secure: bool) -> PyOTReceiver:
        """Return configured receiver."""
        recv = PyOTReceiver()
        recv.totalOTs = len(cls.choices)
        recv.numThreads = config.OT_THREADS
        recv.hostName = "127.0.0.1"
        recv.port = port
        recv.rootCA = config.TLS_ROOT_CA
        if mal_secure:  # pragma no cover
            recv.maliciousSecure = True
            recv.inputBitCount = 76
        else:
            recv.maliciousSecure = False
            recv.inputBitCount = 128
        recv.statSecParam = config.OT_STATSECPARAM
        recv.numChosenMsgs = len(cls.values)
        return recv

    @classmethod
    def get_sender(cls, port: int, mal_secure: bool) -> PyOTSender:
        """Return configured sender."""
        sender = PyOTSender()
        sender.totalOTs = len(cls.choices)
        sender.port = port
        sender.numChosenMsgs = len(cls.values)
        sender.serverKey = config.KEY_TLS_KEY
        sender.serverCert = config.KEY_TLS_CERT
        if mal_secure:  # pragma no cover
            sender.maliciousSecure = True
            sender.inputBitCount = 76
        else:
            sender.maliciousSecure = False
            sender.inputBitCount = 128
        return sender

    def test_kkrt_receiving_with_tls(self):
        tls = True
        p = multiprocessing.Process(target=self.ot_sender,
                                    args=(self.port, tls, False))
        p.start()
        res = self.recv.execute(self.choices, tls)
        p.join()
        self.assertEqual(res, self.values[:10])

    def test_kkrt_receiving_without_tls(self):
        tls = False
        p = multiprocessing.Process(target=self.ot_sender,
                                    args=(self.port, tls, False))
        p.start()
        res = self.recv.execute(self.choices, tls)
        p.join()
        self.assertEqual(res, self.values[:10])

    @skip("Implicitelly tested via receive above.")
    def test_kkrt_sending_without_tls(self):  # pragma no cover
        tls = False
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.ot_receiver,
                                    args=(q, tls, False))
        p.start()
        self.sender.executeSame(self.values, tls)
        p.join()
        result = q.get()
        self.assertEqual(result, self.values[:10])

    @skip("Implicitelly tested via receive above.")
    def test_kkrt_sending_with_tls(self):  # pragma no cover
        tls = True
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.ot_receiver,
                                    args=(q, tls, False))
        p.start()
        self.sender.executeSame(self.values, tls)
        p.join()
        result = q.get()
        self.assertEqual(result, self.values[:10])

    def test_oos_receiving_with_tls(self):
        tls = True
        p = multiprocessing.Process(target=self.ot_sender,
                                    args=(self.port, tls, True))
        p.start()
        self.recv.maliciousSecure = True
        with self.assertRaises(RuntimeError):
            # Bad inputbitcount
            self.recv.execute(self.choices, tls)
        self.recv.inputBitCount = 76
        res = self.recv.execute(self.choices, tls)
        p.join()
        self.assertEqual(res, self.values[:10])

    def test_oos_receiving_without_tls(self):
        tls = False
        p = multiprocessing.Process(target=self.ot_sender,
                                    args=(self.port, tls, True))
        p.start()
        self.recv.maliciousSecure = True
        with self.assertRaises(RuntimeError):
            # Bad inputbitcount
            self.recv.execute(self.choices, tls)
        self.recv.inputBitCount = 76
        res = self.recv.execute(self.choices, tls)
        p.join()
        self.assertEqual(res, self.values[:10])

    @skip("Implicitelly tested via receive above.")
    def test_oos_sending_without_tls(self):  # pragma no cover
        tls = False
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.ot_receiver,
                                    args=(q, tls, True))
        p.start()
        self.sender.maliciousSecure = True
        with self.assertRaises(RuntimeError):
            # Bad inputbitcount
            self.sender.executeSame(self.values, tls)
        self.sender.inputBitCount = 76
        self.sender.executeSame(self.values, tls)
        p.join()
        result = q.get()
        self.assertEqual(result, self.values[:10])

    @skip("Implicitelly tested via receive above.")
    def test_oos_sending_with_tls(self):  # pragma no cover
        tls = True
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.ot_receiver,
                                    args=(q, tls, True))
        p.start()
        self.sender.maliciousSecure = True
        with self.assertRaises(RuntimeError):
            # Bad inputbitcount
            self.sender.executeSame(self.values, tls)
        self.sender.inputBitCount = 76
        self.sender.executeSame(self.values, tls)
        p.join()
        result = q.get()
        self.assertEqual(result, self.values[:10])
