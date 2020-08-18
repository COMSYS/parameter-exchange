#!/usr/bin/env python3
"""Argument Parser for DB CLIs.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""

import argparse


def get_db_parser() -> argparse.ArgumentParser:
    """Return an argument parser for the DB CLIs."""
    db_parser = argparse.ArgumentParser(description="DB CLI")
    action_group = db_parser.add_mutually_exclusive_group(required=True)
    db_parser.add_argument("ID", help="ID of User", type=str,
                           action="store", nargs='?')
    db_parser.add_argument("password", help="Password of User", type=str,
                           action="store", nargs='?')
    action_group.add_argument("-a", "--add", action='store_true',
                              help="Add User with given ID and password to DB."
                              )
    action_group.add_argument("-t", "--get_token", action='store_true',
                              help="Retrieve get_token for user with given "
                                   "ID.")
    action_group.add_argument("--verify", action='store_true',
                              help="Verfiy that password is correct.")
    action_group.add_argument("-n", "--new", action="store", type=str,
                              dest="new",
                              help="Replace password for user with given ID.")
    action_group.add_argument("-l", "--list", action="store_true",
                              help="List all existing users.")
    action_group.add_argument("-s", "--verify-token", action='store',
                              dest='token_val',
                              help="Verfiy that get_token is correct. ("
                                   "Destroys token, for testing only.)",
                              type=str)
    return db_parser
