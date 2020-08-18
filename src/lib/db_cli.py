#!/usr/bin/env python3
"""DB CLI for user DB.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
from typing import List

from flask import Flask

from lib import config
from lib.db_argparser import get_db_parser
from lib.user_database import db
import lib.user_database as user_db


NO_PRINT = False
log: logging.Logger = logging.getLogger(__name__)


def output(*args: str) -> None:
    """Print either via print or via logging."""
    if not NO_PRINT:
        print(*args)
    else:
        log.info(" ".join([str(i) for i in args]))


def main(user_type: str, args: List[str], data_dir: str = config.DATA_DIR,
         no_print: bool = False) -> \
        None:
    """
    Manage the database according to the given CL arguments.
    (Update both databases)

    :param user_type: Type of database that shall be managed
    :param args: Command line arguments. (argv[1:])
    :param data_dir: [optional] Directory where SQLite files are located.
    :param no_print: [optional] Use log instead of print
    """
    global NO_PRINT
    NO_PRINT = no_print
    if len(args) > 0 and (args[0] == "-l" or args[0] == "--list"):
        # We want to skip mandatory args.
        show_list = True
    else:
        show_list = False
        args = get_db_parser().parse_args(args)
    databases = {
        'storage': config.STORAGE_DB,
        'key': config.KEYSERVER_DB
    }
    for d in databases:
        db_file = databases[d]
        app = Flask(__name__)
        app.config.from_mapping(
            SQLALCHEMY_DATABASE_URI=f"sqlite:///{data_dir}/{db_file}",
            SQLALCHEMY_TRACK_MODIFICATIONS=False
        )
        db.init_app(app)
        with app.app_context():
            # Init DB
            db.create_all()
            if show_list:
                users = user_db.get_all_users(user_type)
                output(f"> Result for {d.capitalize()}-Database: "
                       f"({len(users)} Users found.)")
                for i, user in enumerate(users):
                    output(f"{i}: {user}")
            else:
                if args.add:
                    try:
                        if args.ID is None or args.password is None:
                            raise ValueError(
                                "User ID and Password have to defined.")
                        user_db.add_user(user_type, args.ID, args.password)
                        output(f"> {d.capitalize()}: Successfully added user "
                               f"{args.ID}.")
                    except ValueError as e:
                        output(f"> {d.capitalize()}: Add user failed: {e}")
                elif args.get_token:
                    try:
                        if args.ID is None or args.password is None:
                            raise ValueError(
                                "User ID and Password have to defined.")
                        if user_db.verify_password(user_type, args.ID,
                                                   args.password):
                            output(f"> {d.capitalize()} database: ",
                                   user_db.generate_token(user_type, args.ID))
                        else:
                            output(f"> {d.capitalize()}: Incorrect password!")
                    except ValueError as e:
                        log.error(f"{d.capitalize()}: Token generation"
                                  f" failed: {e}")
                elif args.new is not None:
                    try:
                        if args.ID is None or args.password is None:
                            raise ValueError(
                                "User ID and Password have to defined.")
                        user_db.update_password(user_type, args.ID,
                                                args.password, args.new)
                        output(
                            f"> {d.capitalize()}: Successfully updated"
                            f"password for user {args.ID}.")
                    except ValueError as e:
                        log.error(f"{d.capitalize()}: "
                                  f"Password update failed: {e}")
                elif args.verify:
                    try:
                        if args.ID is None or args.password is None:
                            raise ValueError(
                                "User ID and Password have to defined.")
                        if user_db.verify_password(user_type, args.ID,
                                                   args.password):
                            output(f"> {d.capitalize()}: "
                                   f"Credentials are correct.")
                        else:
                            output(f"> {d.capitalize()}: "
                                   f"Password is not correct.")
                    except ValueError as e:
                        log.error(f"{d.capitalize()}: Password verfication"
                                  f"failed: {e}")
                elif args.token_val is not None:
                    try:
                        if args.ID is None:
                            raise ValueError("User ID has to be defined.")
                        if user_db.verify_token(user_type,
                                                args.ID, args.token_val):
                            output(f"> {d.capitalize()}: Token correct. "
                                   f"Token destroyed.")
                        else:
                            output(f"> {d.capitalize()}: Bad Token.")
                    except ValueError as e:
                        log.error(f"{d.capitalize()}: "
                                  f"Token verfication failed: {e}")
