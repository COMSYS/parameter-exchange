#!/usr/bin/env python3
"""This monument contains the CLI to interact with the client DB.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import sys

from lib import db_cli, config
from lib.base_client import UserType
from lib.logging import configure_root_loger

if __name__ == '__main__':  # pragma no cover
    configure_root_loger(logging.INFO, config.LOG_DIR + "client_db.log")
    log = logging.getLogger()
    db_cli.main(UserType.CLIENT, sys.argv[1:])
