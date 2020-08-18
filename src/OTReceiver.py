#!/usr/bin/env python3
"""Acts as receiver for OTs.

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

sys.path.append(config.WORKING_DIR + 'cython/ot')
# Python Version of libOTe
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTReceiver  # noqa


configure_root_loger(logging.INFO, config.LOG_DIR + "ot_receiver.log")
log = logging.getLogger()


def main(args: list) -> List[int]:
    """
    Start the OT Receiver based on the given CL args.
    :param args: command line arguments (argv[1:])
    :return: List of received values
    """
    log.info("Starting OT Receiver.")

    parser = argparse.ArgumentParser("OT Receiver")
    parser.add_argument("TotalOTs", help="Number of OTs to perform",
                        type=int, action="store")
    parser.add_argument("-p", "--port", action="store", help="Port of OT "
                                                             "Server",
                        default=1213, type=int)
    parser.add_argument("-n", "--hostname", action="store", help="IP or DNS "
                                                                 "of OT "
                                                                 "Server",
                        default="127.0.0.1", type=str)

    args = parser.parse_args(args=args)
    recv = PyOTReceiver()
    recv.totalOTs = args.TotalOTs
    recv.numChosenMsgs = config.OT_SETSIZE
    recv.hostName = args.hostname
    recv.port = args.port
    recv.rootCA = config.TLS_ROOT_CA

    choices = []

    for x in range(recv.totalOTs):
        choices.append(x)

    time1 = datetime.datetime.now().timestamp()
    result = recv.execute(choices, config.OT_TLS)
    time2 = datetime.datetime.now().timestamp()
    log.info(f"Transmission took {str(time2 - time1)}s.")
    log.info(f"Received: {str(result)}")
    log.info("Finishing OT Receiver.")
    return result


if __name__ == '__main__':  # pragma no cover
    main(sys.argv[1:])
