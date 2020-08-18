#!/usr/bin/env python3
"""OT receiver script.

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
from cOTInterface import PyOTReceiver  # noqa

ROOTCA = config.TLS_ROOT_CA
RAM_INTERVAL = 0.5
NUM_THREADS = 1


def get_receiver(port: int, setsize: int, num_ots: int,
                 stat: int, num_threads: int, host: str,
                 mal_secure: bool
                 ) -> PyOTReceiver:
    """Return configured receiver."""
    recv = PyOTReceiver()
    recv.totalOTs = num_ots
    recv.numThreads = num_threads
    recv.hostName = host
    recv.port = port
    recv.rootCA = ROOTCA
    if mal_secure:
        recv.maliciousSecure = True
        recv.inputBitCount = 76
    else:
        recv.maliciousSecure = False
        recv.inputBitCount = 128
    recv.statSecParam = stat
    recv.numChosenMsgs = setsize
    return recv


if __name__ == "__main__":
    error = ""
    p = argparse.ArgumentParser("OT Receiver")
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
    recv = get_receiver(a.port, a.set_size, a.num_ots, a.stat, NUM_THREADS,
                        a.host,
                        a.malicious)
    choices = [random.randint(0, a.set_size - 1) for _ in range(a.num_ots)]

    start = time.monotonic()
    mem, res = memory_usage((recv.execute, (choices, a.tls)),
                            interval=RAM_INTERVAL,
                            include_children=True,
                            retval=True,
                            max_iterations=1
                            )
    runtime = time.monotonic() - start
    print(f"{runtime}:{json.dumps(mem)}:{error}")
