#!/usr/bin/env python3
"""PSI receiver script.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import json
import logging
import sys
import time

from memory_profiler import memory_usage

from lib import config

sys.path.append(config.WORKING_DIR + 'cython/psi')
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSIReceiver  # noqa

ROOTCA = config.TLS_ROOT_CA
RAM_INTERVAL = 0.5
log = logging.getLogger()


def get_receiver(port, setSize: int, stat: int,
                 tls: bool, host: str = 'localhost') -> PyPSIReceiver:
    """Return a configured PSIReceiver."""
    recv = PyPSIReceiver()
    recv.setSize = setSize
    recv.hostName = host
    recv.port = port
    recv.numThreads = 1
    recv.statSecParam = stat
    recv.tls = tls
    recv.rootCA = ROOTCA
    return recv


if __name__ == "__main__":
    error = ""
    p = argparse.ArgumentParser("PSI Receiver")
    p.add_argument('-t', '--tls', action='store_true',
                   help="TLS", default=False)
    p.add_argument('-m', '--malicious', action='store_true',
                   help="Use RR16?", default=False)
    p.add_argument('-s', '--set_size', required=True,
                   help="Setsize.", action='store', type=int)
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

    if a.malicious:
        protocol = "RR16"
    else:
        protocol = "KKRT16"
    recv = get_receiver(a.port, a.set_size, a.stat, a.tls, a.host)

    client_set = [i + a.set_size * (i % 2) for i in range(a.set_size)]

    start = time.monotonic()
    mem, res = memory_usage((recv.execute, (protocol, client_set)),
                            interval=RAM_INTERVAL,
                            include_children=True,
                            retval=True,
                            max_iterations=1)
    runtime = time.monotonic() - start
    # Check result
    if set(res) != set([i for i in range(a.set_size) if i % 2 == 0]):
        error = "Result incorrect!"
        log.error("Bad result.")
    print(f"{runtime}:{json.dumps(mem)}:{error}")
