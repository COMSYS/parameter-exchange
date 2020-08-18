#!/usr/bin/env python3
"""Client Application of data provider type end-users.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import json
import logging
import os
import pickle
import sys
import time
from typing import List, Tuple, Iterable

from memory_profiler import memory_usage

import lib.config as config
from lib.base_client import BaseClient, UserType, ServerType
from lib.helpers import parse_list, to_base64, print_time
from lib.logging import configure_root_loger
from lib.record import Record

configure_root_loger(logging.INFO, config.LOG_DIR + "data_provider.log")
log = logging.getLogger()


class DataProvider(BaseClient):
    """Data Provider Client for end users."""

    type = UserType.OWNER

    def _store_record_on_server(self, hash_val: bytes, ciphertext: dict,
                                owner: str) -> None:
        """
        Store the given record on the storage server.
        :param hash_val: [Bytes] Long hash of record as returned by records

        :param ciphertext: [Dict] encrypted record as returned by records
                                  object
        :param owner: [str] owner of record as string
        :return:
        """
        j = {
            'hash': to_base64(hash_val),
            'ciphertext': ciphertext,
            'owner': owner
        }
        r = self.post(f"{self.STORAGESERVER}/store_record", json=j)
        suc = r.json()['success']
        if suc:
            log.info("Successfully stored record.")
        else:
            msg = r.json()['msg']
            raise RuntimeError(f"Failed to store record: {msg}")

    def _batch_store_records_on_server(
            self,
            records: Iterable[Tuple[str, str, str]]) -> None:
        """
        Store all records in the list on the storage server.
        :param records: List of records in following form:
        [
            ('Base64-1', json.dumps(ciphertext1), 'owner1'),
            ('Base64-2', json.dumps(ciphertext2), 'owner2')
        ]
        :return: Task ID
        """
        r = self.post(f"{self.STORAGESERVER}/batch_store_records",
                      json=records)
        self.eval['cx_sizes'] = [len(rec[1]) for rec in records]
        self.eval['json_length'] = len(json.dumps(records))
        suc = r.json()['success']
        if suc:
            log.info("Successfully stored requests.")
        else:
            msg = r.json()['msg']
            raise RuntimeError(f"Failed to store records: {msg}")

    def store_records(self, records: List[Record]) -> None:
        """Prepare all records in the list with hashing and encryption and
        store them on the storage server."""
        start = time.monotonic()
        log.debug("Store Records called.")
        # 1: Retrieve Hash Key
        log.info("1: Retrieve Hash Key")

        hash_key = self.get_hash_key()

        self.eval['hash_key_time'] = time.monotonic()
        log.info(
            f"1: Retrieve Hash Key took: {print_time(time.monotonic()-start)}")
        start = time.monotonic()
        # 2: Update hash_keys of record
        log.info("2: Compute Hashes")

        for r in records:
            r.set_hash_key(hash_key)

        self.eval['hash_set_time'] = time.monotonic()
        log.info(f"2: Set Hash Key took: {print_time(time.monotonic()-start)}")
        start = time.monotonic()
        # 3: Get OT hashes
        log.info("3: Get OT Indizes")

        ot_indices = [r.get_ot_index() for r in records]

        self.eval['ot_index_time'] = time.monotonic()
        log.info(
            f"3: Get OT Indizes took: {print_time(time.monotonic()-start)}")
        start = time.monotonic()
        # 4: Request encryption keys
        log.info("4: Request Encryption Keys")

        enc_keys = self._get_enc_keys(ot_indices)

        self.eval['key_retrieve_time'] = time.monotonic()
        log.info(f"4: Request Encryption Keys took:"
                 f"{print_time(time.monotonic()-start)}")
        start = time.monotonic()
        # 5: Encrypt records
        log.info("5: Set encryption keys")

        for i, r in enumerate(records):
            r.set_encryption_key(enc_keys[i])
            r.owner = self.user

        self.eval['set_key_time'] = time.monotonic()
        # 6: Create record list
        log.info("6: Create record list [Includes Encryption].")

        record_list = [
            r.get_upload_format() for r in records
        ]

        self.eval['encryption_time'] = time.monotonic()
        log.info(
            f"6: Create record list took: {print_time(time.monotonic()-start)}")
        start = time.monotonic()
        log.info("7: Send encrypted records to server")

        self._batch_store_records_on_server(record_list)

        self.eval['send_time'] = time.monotonic()
        log.info(f"7: Send encrypted records to server took:"
                 f"{print_time(time.monotonic()-start)}")

    def store_from_file(self, file: str) -> None:
        """
        Return all records from file and store at storage server
        :param file: path to the file containing the records
        :return: Task ID of storage command
        """
        self.eval['start_time'] = time.monotonic()

        records = []
        with open(file, "r") as fd:
            for line in fd:
                records.append(Record(parse_list(line)))
        self.eval['parsed_list_time'] = time.monotonic()
        log.info(f"Parsed {len(records)} records.")
        self.store_records(records)


def get_provider_parser() -> argparse.ArgumentParser:
    """Return an argument parser for the data provider CLI."""
    dp_parser = argparse.ArgumentParser(description="Data Provider Client")
    action_group = dp_parser.add_mutually_exclusive_group(required=False)
    dp_parser.add_argument("id", help="ID of User", type=str,
                           action="store")
    dp_parser.add_argument("password", help="Password of User", type=str,
                           action="store")
    dp_parser.add_argument('-v', '--verbose', action='count', default=0,
                           help="Increase verbosity. (-v INFO, -vv DEBUG)")
    action_group.add_argument("-t", "--get_token", action='store_true',
                              help="Retrieve get_token for user with given "
                                   "ID.")
    action_group.add_argument("-f", "--load_file", action='store',
                              help="Store all records in file on storage "
                                   "server.", dest="file")
    action_group.add_argument("-a", "--add",
                              help="String representation of record to add.",
                              )
    dp_parser.add_argument('-e', "--eval", help="Eval communication file",
                           type=str, action="store", required=config.EVAL)
    return dp_parser


if __name__ == '__main__':  # pragma no cover
    parser = get_provider_parser()
    args = parser.parse_args()

    # Logging
    if args.verbose == 1:
        log.setLevel(logging.INFO)
    elif args.verbose == 2:
        log.setLevel(logging.DEBUG)

    dp = DataProvider(args.id)
    dp.set_password(args.password)

    # Test credentials
    try:
        t = dp.get_token(ServerType.KeyServer)
        print("> Log-in successful.")
    except RuntimeError as e:
        if "Authentication failed" in str(e):
            print("> Username or password is not corect! Exiting.")
        else:
            log.error(str(e), exc_info=True)
            print("> Authentication failed.")
        sys.exit()

    # Perform action
    try:
        if args.get_token:
            print(f"> Generated token at Key-Server:\n> {t}")
        elif args.file:
            if not os.path.exists(args.file):
                msg = f"The given file does not exist: {args.file}"
                log.error(msg)
                print(f"> {msg}")
            else:
                if config.EVAL:
                    com_file = args.eval

                    def execDP():
                        """Execute store from file

                        :return: result, error
                        """
                        try:
                            return dp.store_from_file(args.file), None
                        except Exception as err:
                            err = str(err)
                            log.exception(err)
                            return None, err

                    ram_usage, (result, error) = memory_usage(
                        (execDP,),
                        interval=config.RAM_INTERVAL,
                        include_children=True,
                        retval=True,
                    )
                    dp.eval['result'] = result
                    dp.eval['ram_usage'] = ram_usage
                    dp.eval['error'] = error
                    with open(com_file, "wb") as fd:
                        pickle.dump(dp.eval, fd)
                else:
                    dp.store_from_file(args.file)
                print("> Successfully stored records on server.")
        elif args.add:
            string = args.add
            r_list = string.strip('][').split(',')
            r_list = [float(i) for i in r_list]
            log.debug(f"Got: {str(r_list)}")
            r = Record(r_list)
            dp.store_records([r])
            print("> Successfully stored records on server.")
    except Exception as e:
        log.error(str(e), exc_info=True)
        sys.exit()
