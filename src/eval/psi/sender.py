#!/usr/bin/env python3
"""PSI Sender script

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import json
import sys
import time

from memory_profiler import memory_usage

from lib import config

sys.path.append(config.WORKING_DIR + 'cython/psi')
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSISender  # noqa

SERVERCERT = config.KEY_TLS_CERT
SERVERKEY = config.KEY_TLS_KEY
RAM_INTERVAL = 0.5


def get_sender(port, setSize: int, stat: int,
               tls: bool, host: str = 'localhost') -> PyPSISender:
    """Return a configured PSISender."""
    sender = PyPSISender()
    sender.setSize = setSize
    sender.hostName = host
    sender.port = port
    sender.numThreads = 1
    sender.tls = tls
    sender.statSecParam = stat
    sender.serverCert = SERVERCERT
    sender.serverKey = SERVERKEY
    return sender


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
    sender = get_sender(a.port, a.set_size, a.stat, a.tls, a.host)
    if a.malicious:
        protocol = "RR16"
    else:
        protocol = "KKRT16"

    server_set = list(range(a.set_size))
    start = time.monotonic()
    mem = memory_usage((sender.execute, (protocol, server_set)),
                       interval=RAM_INTERVAL,
                       include_children=True,
                       max_iterations=1)
    runtime = time.monotonic() - start
    print(f"{runtime}:{json.dumps(mem)}:{error}")
