#!/usr/bin/env python3
"""Test Cython Port of libPSI.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import multiprocessing
import sys
from unittest import TestCase, skip

from lib import config

# Python Version of libPSI
from lib.helpers import get_free_port

sys.path.append(config.WORKING_DIR + 'cython/psi')
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSISender  # noqa
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSIReceiver  # noqa


# Constants
SETSIZE = 10
HOSTNAME = "127.0.0.1"


class PSITest(TestCase):
    server_set = list(range(SETSIZE))
    client_set = [i + SETSIZE * (i % 2) for i in server_set]
    result_set = [i for i in server_set if i % 2 == 0]

    def setUp(self) -> None:
        """Create receiver and Sender."""
        self.port = get_free_port()
        self.recv = self.get_receiver(self.port)
        self.sender = self.get_sender(self.port)

    def psi_sender(self, scheme: str, tls: bool):  # pragma no cover
        """Act as PSI Sender to test receivers."""
        sender = self.get_sender(self.port)
        sender.tls = tls
        sender.execute(scheme, self.server_set)

    def psi_receiver(self, queue: multiprocessing.Queue, scheme: str,
                     tls: bool):  # pragma no  cover
        """Act as PSI Receiver to test senders."""
        receiver = self.get_receiver(self.port)
        receiver.tls = tls
        r = receiver.execute(scheme, self.client_set)
        queue.put(r)

    @classmethod
    def get_sender(cls, port) -> PyPSISender:
        """Return a configured PSISender."""
        sender = PyPSISender()
        sender.setSize = SETSIZE
        sender.hostName = HOSTNAME
        sender.port = port
        sender.numThreads = 1
        sender.serverCert = config.KEY_TLS_CERT
        sender.serverKey = config.KEY_TLS_KEY
        return sender

    @classmethod
    def get_receiver(cls, port) -> PyPSIReceiver:
        """Return a configured PSIReceiver."""
        recv = PyPSIReceiver()
        recv.setSize = SETSIZE
        recv.hostName = HOSTNAME
        recv.port = port
        recv.numThreads = 1
        recv.rootCA = config.TLS_ROOT_CA
        return recv

    def test_KKRT16_recv(self):
        tls = False
        self.recv.tls = tls
        scheme = "KKRT16"
        p = multiprocessing.Process(target=self.psi_sender,
                                    args=(scheme, tls))
        p.start()
        res = self.recv.execute(scheme, self.client_set)
        p.join()
        self.assertEqual(set(res), set(self.result_set))

    def test_KKRT16_recv_tls(self):
        tls = True
        self.recv.tls = tls
        scheme = "KKRT16"
        p = multiprocessing.Process(target=self.psi_sender,
                                    args=(scheme, tls))
        p.start()
        res = self.recv.execute(scheme, self.client_set)
        p.join()
        self.assertEqual(set(res), set(self.result_set))

    @skip("Very slow")
    def test_RR16_recv(self):  # pragma no cover
        tls = False
        self.recv.tls = tls
        scheme = "RR16"
        p = multiprocessing.Process(target=self.psi_sender,
                                    args=(scheme, tls))
        p.start()
        res = self.recv.execute(scheme, self.client_set)
        p.join()
        self.assertEqual(set(res), set(self.result_set))

    @skip("Very slow")
    def test_RR16_recv_tls(self):  # pragma no cover
        tls = True
        self.recv.tls = tls
        scheme = "RR16"
        p = multiprocessing.Process(target=self.psi_sender,
                                    args=(scheme, tls))
        p.start()
        res = self.recv.execute(scheme, self.client_set)
        p.join()
        self.assertEqual(set(res), set(self.result_set))

    @skip("Failes for large sets.")
    def test_RR17_recv(self):  # pragma no cover
        tls = False
        self.recv.tls = tls
        scheme = "RR17"
        p = multiprocessing.Process(target=self.psi_sender,
                                    args=(scheme, tls))
        p.start()
        res = self.recv.execute(scheme, self.client_set)
        p.join()
        self.assertEqual(set(res), set(self.result_set))

    @skip("Not used in project.")
    def test_RR17_recv_tls(self):  # pragma no cover
        tls = True
        self.recv.tls = tls
        scheme = "RR17"
        p = multiprocessing.Process(target=self.psi_sender,
                                    args=(scheme, tls))
        p.start()
        res = self.recv.execute(scheme, self.client_set)
        p.join()
        self.assertEqual(set(res), set(self.result_set))

    @skip("Implicitelly tested via receive above.")
    def test_KKRT16_send(self):  # pragma no cover
        tls = False
        self.sender.tls = tls
        scheme = "KKRT16"
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.psi_receiver, args=(q,
                                                                    scheme,
                                                                    tls))
        p.start()
        self.sender.execute(scheme, self.server_set)
        p.join()
        result = q.get()
        self.assertEqual(set(result), set(self.result_set))

    @skip("Implicitelly tested via receive above.")
    def test_KKRT16_send_tls(self):  # pragma no cover
        tls = True
        self.sender.tls = tls
        scheme = "KKRT16"
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.psi_receiver, args=(q,
                                                                    scheme,
                                                                    tls))
        p.start()
        self.sender.execute(scheme, self.server_set)
        p.join()
        result = q.get()
        self.assertEqual(set(result), set(self.result_set))

    @skip("Very slow and not needed in production code.")
    def test_RR16_send(self):  # pragma no cover
        tls = False
        self.sender.tls = tls
        scheme = "RR16"
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.psi_receiver, args=(q,
                                                                    scheme,
                                                                    tls))
        p.start()
        self.sender.execute(scheme, self.server_set)
        p.join()
        result = q.get()
        self.assertEqual(set(result), set(self.result_set))

    @skip("Very slow and not needed in production code.")
    def test_RR16_send_tls(self):  # pragma no cover
        tls = True
        self.sender.tls = tls
        scheme = "RR16"
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.psi_receiver, args=(q,
                                                                    scheme,
                                                                    tls))
        p.start()
        self.sender.execute(scheme, self.server_set)
        p.join()
        result = q.get()
        self.assertEqual(set(result), set(self.result_set))

    @skip("Not used in project.")
    def test_RR17_send(self):  # pragma no cover
        tls = False
        self.sender.tls = tls
        scheme = "RR17"
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.psi_receiver, args=(q,
                                                                    scheme,
                                                                    tls))
        p.start()
        self.sender.execute(scheme, self.server_set)
        p.join()
        result = q.get()
        self.assertEqual(set(result), set(self.result_set))

    @skip("Not used in project.")
    def test_RR17_send_tls(self):  # pragma no cover
        tls = True
        self.sender.tls = tls
        scheme = "RR17"
        q = multiprocessing.Queue()
        p = multiprocessing.Process(target=self.psi_receiver, args=(q,
                                                                    scheme,
                                                                    tls))
        p.start()
        self.sender.execute(scheme, self.server_set)
        p.join()
        result = q.get()
        self.assertEqual(set(result), set(self.result_set))
