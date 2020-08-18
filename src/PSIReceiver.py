#!/usr/bin/env python3
"""Acts as receiver for PSIs.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import datetime
import logging
import sys
from typing import List

import lib.config as config
from lib.logging import configure_root_loger

sys.path.append(config.WORKING_DIR + 'cython/psi')
# Python Version of libPSI
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSIReceiver  # noqa


configure_root_loger(logging.INFO, config.LOG_DIR + "psi_receiver.log")
log = logging.getLogger()


def main(args: list) -> List[int]:
    """
    Start the PSI Receiver based on the given CL args.
    :param args: command line arguments (argv[1:])
    :return: List of received values
    """
    log.info("Starting PSI Receiver.")

    parser = argparse.ArgumentParser("PSI Receiver")
    parser.add_argument("SetSize", help="Size of PSI Set.",
                        type=int, action="store", default=config.PSI_SETSIZE,
                        metavar="setSize", nargs='?')
    parser.add_argument("-p", "--port", action="store",
                        help="Port of PSI Server",
                        default=config.PSI_PORT, type=int)
    parser.add_argument("-n", "--hostname", action="store",
                        help="IP or DNS of PSI Server",
                        default=config.PSI_HOST, type=str)
    parser.add_argument("-s", "--scheme", action="store", type=str,
                        help="PSI Scheme to use", default=config.PSI_SCHEME)

    args = parser.parse_args(args=args)
    recv = PyPSIReceiver()

    recv.statSecParam = config.PSI_STATSECPARAM
    recv.setSize = args.SetSize

    recv.hostName = args.hostname
    recv.port = args.port
    recv.numThreads = config.PSI_THREADS
    recv.tls = config.PSI_TLS
    recv.rootCA = config.TLS_ROOT_CA

    set = list(range(recv.setSize))

    time1 = datetime.datetime.now().timestamp()
    result = recv.execute(args.scheme, set)
    time2 = datetime.datetime.now().timestamp()
    log.info(f"Transmission took {str(time2 - time1)}s.")
    log.info(f"Received: {str(result)}")
    log.info("Finishing PSI Receiver.")
    return result


if __name__ == '__main__':  # pragma no cover
    main(sys.argv[1:])
