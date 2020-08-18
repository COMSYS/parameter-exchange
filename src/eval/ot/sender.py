#!/usr/bin/env python3
"""OT Sender script.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import json
import random
import sys
import time

from memory_profiler import memory_usage

from lib import config

sys.path.append(config.WORKING_DIR + 'cython/ot')
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTSender  # noqa

SERVERCERT = config.KEY_TLS_CERT
SERVERKEY = config.KEY_TLS_KEY
MAX_VALUE = 2 ** 100
RAM_INTERVAL = 0.5
NUM_THREADS = 1


def get_sender(port: int, setsize: int, num_ots: int,
                 stat: int, num_threads: int, host: str,
                 mal_secure: bool
               ) -> PyOTSender:
    """Return configured sender."""
    sender = PyOTSender()
    sender.totalOTs = num_ots
    sender.numThreads = num_threads
    sender.hostName = host
    sender.port = port
    sender.serverKey = SERVERKEY
    sender.serverCert = SERVERCERT
    if mal_secure:
        sender.maliciousSecure = True
        sender.inputBitCount = 76
    else:
        sender.maliciousSecure = False
        sender.inputBitCount = 128
    sender.statSecParam = stat
    sender.numChosenMsgs = setsize
    return sender


if __name__ == "__main__":
    error = ""
    p = argparse.ArgumentParser("OT Sender")
    p.add_argument('-t', '--tls', action='store_true',
                   help="TLS")
    p.add_argument('-m', '--malicious', action='store_true',
                   help="Use OOS16?", default=False)
    p.add_argument('-s', '--set_size', required=True,
                   help="Setsize.", action='store', type=int)
    p.add_argument('-n', '--num_ots', required=True,
                   help="# OTs to perform.", action='store', type=int)
    p.add_argument('--statsecparam', dest='stat',
                   help="Statistical Sec. Parameters",
                   action='store', type=int, default=40)
    p.add_argument('--host', type=str, help="Host", default="localhost")
    p.add_argument('-p', '--port', type=int, help="Port", required=True)
    p.add_argument('-r', '--round', type=int, help="Round")
    p.add_argument('-l', '--latency', type=int, help="Latency")
    p.add_argument('-o', '--out', type=str, action='store',
                   help="ram_path!")
    a = p.parse_args()
    sender = get_sender(a.port, a.set_size, a.num_ots, a.stat, NUM_THREADS,
                        a.host, a.malicious)
    server_set = [
        random.randint(0, MAX_VALUE) for _ in range(a.set_size)]
    start = time.monotonic()
    mem = memory_usage((sender.executeSame, (server_set, a.tls)),
                       interval=RAM_INTERVAL,
                       include_children=True,
                       max_iterations=1
                       )
    runtime = time.monotonic() - start
    print(f"{runtime}:{json.dumps(mem)}:{error}")
