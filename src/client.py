#!/usr/bin/env python3
"""Client Application of client type end-users.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import atexit
import copy
import json
import logging
import multiprocessing
import pickle
import pprint
import shutil
import sys
import time
from itertools import tee
from typing import List

# noinspection PyUnresolvedReferences
from memory_profiler import profile, memory_usage
from pybloomfilter import BloomFilter

from lib import config, helpers
from lib.base_client import BaseClient, UserType, ServerType
from lib.helpers import parse_list, to_base64, print_time, from_base64
from lib.logging import configure_root_loger
from lib.record import Record, hash_to_index
from lib.similarity_metrics import map_metric, RecordIterator, \
    SimilarityMetricIterator

configure_root_loger(logging.INFO, config.LOG_DIR + "client.log")
log = logging.getLogger()


class Client(BaseClient):
    """Client Application for end users."""

    type = UserType.CLIENT
    metric = "offset-1"
    _psi_mode = config.PSI_MODE

    def get_record(self, h: str) -> List[Record]:
        """Retrieve record with given hash."""
        j = {'hash': h}
        resp = self.post(f"{self.STORAGESERVER}/retrieve_record",
                         json=j)
        suc = resp.json()['success']
        if suc:
            log.debug("Successfully retrieved record.")
            return resp.json()['records']
        else:
            msg = resp.json()['msg']
            raise RuntimeError(f"Failed to retrieve record: {msg}")

    def _batch_get_encrpyted_records(self, hash_list: List[str]) -> \
            List[str]:
        """
        Retrieve record with given hash.
        :param hash_list: List of **base64**-encoded hashes
        :return: List of encrypted records as json.dumps(dict)
        """
        j = {'hashes': hash_list}
        resp = self.post(f"{self.STORAGESERVER}/batch_retrieve_records",
                         json=j)
        suc = resp.json()['success']
        if suc:
            log.debug("Successfully retrieved records.")
            return resp.json()['records']
        else:
            msg = f"Failed to retrieve record: {resp.json()['msg']}"
            raise RuntimeError(msg)

    def batch_get_records(self, candidates: List[Record]) -> List[Record]:
        """
        Retrieve the records for all hashes in the list

        :param candidates: Record objects for all candidates (hash_set)
        :return: List of retrieved records (decyrpted)
        """
        log.info("4.1 Retrieve encryption keys.")
        start = time.monotonic()
        ot_indices = []
        # No duplicates
        for r in candidates:
            if r.get_ot_index() not in ot_indices:
                ot_indices.append(r.get_ot_index())

        enc_keys = self._get_enc_keys(ot_indices)
        # Create mapping
        enc_keys = dict(zip(
            ot_indices,
            enc_keys
        ))
        self.eval['key_retrieve_time'] = time.monotonic()
        log.info(
            f"4.1 - Retrieve keys took: {print_time(time.monotonic() - start)}")
        log.info("4.2 Retrieve encrypted records.")
        start = time.monotonic()
        hash_list = [to_base64(r.get_long_hash()) for r in candidates]
        records = self._batch_get_encrpyted_records(hash_list)
        if not records:
            self.eval['record_retrieve_time'] = time.monotonic()
            self.eval['decryption_time'] = time.monotonic()
            return []
        res_list = []
        self.eval['record_retrieve_time'] = time.monotonic()
        log.info(
            f"4.2 - Retrieve records: {print_time(time.monotonic() - start)}")
        log.info("4.3 Decrypting.")
        start = time.monotonic()
        for h, c in records:
            c = json.loads(c)
            key = enc_keys[hash_to_index(from_base64(h), config.OT_INDEX_LEN)]
            log.debug(
                f"Using key {key} for record {h}.")
            res_list.append(Record.from_ciphertext(c, key))
        self.eval['decryption_time'] = time.monotonic()
        log.info(
            f"4.3 - Decryption took: {print_time(time.monotonic() - start)}")
        return res_list

    def _get_bloom_filter(self) -> BloomFilter or None:
        """
        Retrieve the bloom filter from storage server
        :return: Bloom filter
        """
        resp = self.get(f"{self.STORAGESERVER}/bloom")
        suc = resp.json()['success']
        if suc:
            log.debug("Successfully retrieved bloom filter.")
            tmp = helpers.get_temp_file() + '.bloom'
            b = BloomFilter.from_base64(tmp,
                                        resp.json()['bloom'].encode())
            atexit.register(shutil.rmtree, tmp, True)  # Remove and ignore
            # errors
            return b
        else:
            msg = resp.json()['msg']
            raise RuntimeError(f"Failed to retrieve bloom filter: {msg}")

    # noinspection PyUnboundLocalVariable
    def _perform_psi(self, client_set: List[int]) -> List[int]:
        log.debug("Perform PSI.")
        if len(client_set) == 0:
            return []
        r = self.get(f"{self.STORAGESERVER}/psi")
        d = r.json()
        if not d['success']:
            raise RuntimeError(f"PSI failed: {d['msg']}")
        log.debug("Retrieved PSI connection information.")
        if d['tls'] != config.PSI_TLS:
            log.error("Server TLS setting mismatch.")
            raise RuntimeError("Mismatch of server and client TLS "
                               "settings.")
        host = d['host']
        port = d['port']
        set_size = d['setSize']
        if set_size < len(client_set):
            raise RuntimeError("Client Set larger than PSI Setsize.")
        # Padding - KKRT16 does not allow for duplicates
        client_set = list(set(client_set))  # Remove duplicates
        # log.debug(f"Client set without dummies: {str(client_set)}")
        dummy = config.PSI_DUMMY_START_CLIENT
        while len(client_set) < set_size:
            client_set.append(dummy)
            dummy += 1
        if d['tls']:
            tls = "with"
        else:
            tls = "without"
        log.info(f"Connecting for PSI to host {host} on port {port} {tls} "
                 f"TLS. Setsize: {set_size}")

        if config.EVAL:  # pragma no cover
            to_svr, tsvr_file = helpers.start_trans_measurement(
                port, direction="dst", sleep=False)
            from_svr, fsvr_file = helpers.start_trans_measurement(
                port, direction="src", sleep=False)
            self.eval['psi_tcpdump_sent'].append(tsvr_file)
            self.eval['psi_tcpdump_recv'].append(fsvr_file)
            time.sleep(1)  # Wait for startup of tcpdump

        matches = self._receive_psi(client_set, host, port, d['tls'])

        log.debug(f"Completed PSI.")
        log.debug(f"Matches: {str(matches)}")
        # Remove dummies
        matches = [m for m in matches if m < config.PSI_DUMMY_START_CLIENT]
        return matches

    def compute_matches_bloom(self,
                              candidate_iterator: SimilarityMetricIterator) \
            -> List[Record]:
        """
        Compute list of records stored on server side using a bloom filter.
        :param candidate_iterator: Iterator over candidates
        :return: List of Records found on server side.
        """
        if self._psi_mode:
            raise RuntimeError("Matches cannot be computed with bloom filter "
                               "because PSI-Mode is enabled.")
        log.info(f"3.1 Retrieve bloom filter.")
        b = self._get_bloom_filter()

        self.eval['bloom_filter_retrieve_time'] = time.monotonic()
        log.info(f"3.2 Compute matches with Bloom Filter.")
        if config.PARALLEL:
            # parallel
            num_procs = multiprocessing.cpu_count()
            its = candidate_iterator.split(num_procs)
            num_procs = len(its)
            log.debug(
                f"Using {num_procs} parallel processes for bloom matching.")
            processes = []
            m = multiprocessing.Manager()
            output = m.list()

            def matching(client_set: RecordIterator,
                         i: int):  # pragma no cover
                """Compute matching with given part of client set."""
                log.debug(
                    f"Proc {i} iterating over {len(client_set)} elements.")
                m = [i for i in client_set if to_base64(
                    i.get_long_hash()) in b]
                output.extend(m)

            for i in range(num_procs):
                client_set = RecordIterator(its[i], self._hash_key)
                p = multiprocessing.Process(target=matching,
                                            args=(client_set, i))
                processes.append(p)
                p.start()
                atexit.register(p.terminate)
            for i, p in enumerate(processes):
                p.join()
                atexit.unregister(p.terminate)
            matches = list(output)
            log.debug("All processes terminated.")
        else:
            client_set = RecordIterator(candidate_iterator,
                                        self.get_hash_key())
            matches = [i for i in client_set if to_base64(
                i.get_long_hash()) in b]

        self.eval['bloom_matching_time'] = time.monotonic()
        return matches

    def compute_matches_psi(self,
                            candidate_iterator: SimilarityMetricIterator) -> \
            List[Record]:
        """
        Compute list of records stored on server side using a bloom filter.
        :param candidate_iterator: Iterator over candidates
        :return: List of Records found on server side.
        """
        if not self._psi_mode:
            raise RuntimeError("Matches cannot be computed with PSI "
                               "because PSI-Mode is not enabled.")
        if len(candidate_iterator) > config.PSI_SETSIZE:
            raise RuntimeError("Candidate Set is too large for PSI! "
                               f"Candidates: {len(candidate_iterator)} "
                               f"PSI Setsize: {config.PSI_SETSIZE}")
        log.info(f"3.1 Compute matches via PSI.")
        client_set = RecordIterator(candidate_iterator, self.get_hash_key())

        it1, it2 = tee(client_set)
        psi_indizes = list(set([r.get_psi_index() for r in it1]))
        # for r in it1:
        #     if r.get_psi_index() not in psi_indizes:
        #         psi_indizes.append(r.get_psi_index())

        log.debug("Created PSI client set.")
        self.eval['psi_preparation_time'] = time.monotonic()

        matching_indizes = self._perform_psi(psi_indizes)

        self.eval['psi_execution_time'] = time.monotonic()

        matches = [r for r in it2
                   if r.get_psi_index() in matching_indizes]

        self.eval['psi_set_construction_time'] = time.monotonic()

        return matches

    def compute_candidates(self, target: List[float],
                           metric_name: str = None
                           ) -> SimilarityMetricIterator:
        """
        Return all similarity candidates for the given target by using the
        provided similarity metric.
        :param target: The target list to compute similarity for.
        :param metric_name: Name of the similarity metric to use.
        :return:
        """
        if metric_name is None:
            metric_name = self.metric
        metric, args = map_metric(metric_name)
        log.debug(f"Compute candidates using {metric_name}.")
        return metric(target, *args)

    # @profile(stream=f)
    def full_retrieve(self, target: List[float]) -> List[Record]:
        """
        Perform a full retrieval
        :param target: The target vector to retrieve similar values for
        :return: The list of retrieved candidates.
        """
        self.eval['start_time'] = time.monotonic()
        try:
            log.debug(f"Retrieve matches for: {target}")
            log.info(f"1. Compute candidates.")

            candidate_iterator = self.compute_candidates(target)
            self.eval['compute_candidates_time'] = time.monotonic()
            log.info(f"1 - Computed {len(candidate_iterator)} candidates.")
            log.info(f"2. Retrieve hash secret.")
            start = time.monotonic()

            self._hash_key = self.get_hash_key()

            self.eval['hash_key_time'] = time.monotonic()
            log.info(
                f"2 - Retrieval of Hash Secret took: "
                f"{print_time(time.monotonic() - start)}")
            log.info(f"3. Compute Matches.")
            start = time.monotonic()

            if not config.EVAL:
                if self._psi_mode:
                    matches = self.compute_matches_psi(candidate_iterator)
                else:
                    matches = self.compute_matches_bloom(candidate_iterator)
            else:  # pragma no cover
                # Do BOTH PSI and BLOOM if PSI Mode enabled.
                candidate_iterator2 = copy.deepcopy(candidate_iterator)
                if self._psi_mode:
                    psi_matches = self.compute_matches_psi(candidate_iterator)
                    self.eval['psi_matches'] = len(psi_matches)
                else:
                    self.eval['psi_matches'] = 0
                    self.eval['psi_preparation_time'] = 0
                    self.eval['psi_execution_time'] = 0
                    self.eval['psi_set_construction_time'] = 0
                    # For Debugging only:
                    # for i in candidate_iterator:
                    #     print(i)
                    # print("Real Length:", len([i for i in candidate_iterator]))
                    # for r in RecordIterator(candidate_iterator, self.get_hash_key()):
                    #     print(to_base64(r.get_long_hash()))
                self._psi_mode = False
                bloom_matches = self.compute_matches_bloom(candidate_iterator2)
                self.eval['bloom_matches'] = len(bloom_matches)
                matches = bloom_matches
                self.eval['num_matches'] = len(matches)

            log.info(f"3 - Computed {len(matches)} matches.")
            # log.debug(str([r.record for r in matches]))
            log.info(
                f"3 - Matching took: {print_time(time.monotonic() - start)}")
            log.info(f"4. Retrieve records.")

            result = self.batch_get_records(matches)
            log.info(f"Found {len(result)} result vectors.")

            return result
        except Exception as e:
            log.exception(str(e))
            raise e

    def activate_psi_mode(self):
        """Enables PSI Mode."""
        self._psi_mode = True


def get_client_parser() -> argparse.ArgumentParser:
    """Return an argparser for the client application."""
    c_parser = argparse.ArgumentParser(description="Client App")
    action_group = c_parser.add_mutually_exclusive_group(required=False)
    c_parser.add_argument("id", help="ID of User", type=str,
                          action="store")
    c_parser.add_argument("password", help="Password of User", type=str,
                          action="store")
    c_parser.add_argument('-m', "--metric", help="Name of similarity metric",
                          type=str, action="store")
    c_parser.add_argument('-e', "--eval", help="Eval communication file",
                          type=str, action="store", required=config.EVAL)
    c_parser.add_argument('-p', "--psi", help="Use PSI Mode.",
                          action="store_true")
    c_parser.add_argument('-v', '--verbose', action='count', default=0,
                          help="Increase verbosity. (-v INFO, -vv DEBUG)")
    action_group.add_argument("-t", "--get_token", action='store_true',
                              help="Retrieve get_token for user with given "
                                   "ID.")
    action_group.add_argument('--hash_key', action='store_true',
                              help='Retrieve hash key from server.')
    action_group.add_argument('-g', '--get_record', type=str, action='store',
                              help="Retrieve record with given hash ["
                                   "Base64].", metavar="HASH", dest='hash')
    action_group.add_argument('-s', '--similar', action='store', type=str,
                              help="Compute a list of suitable candidates.")
    action_group.add_argument('-r', '--retrieve_matches', action='store',
                              type=str, dest="target",
                              help="Retrieve all possibly helpful values.")
    return c_parser


if __name__ == '__main__':  # pragma no cover
    parser = get_client_parser()
    args = parser.parse_args()

    # Logging
    if args.verbose == 1:
        log.setLevel(logging.INFO)
    elif args.verbose == 2:
        log.setLevel(logging.DEBUG)

    c = Client(args.id)
    c.set_password(args.password)
    # Test credentials
    try:
        t = c.get_token(ServerType.KeyServer)
        print("> Log-in successful.")
    except RuntimeError as e:
        if "Authentication failed" in str(e):
            print("> Username or password is not corect! Exiting.")
        else:
            log.error(str(e), exc_info=True)
            print("> Authentication failed.")
        sys.exit()

    if args.metric is not None:
        try:
            map_metric(args.metric)
        except ValueError as e:
            log.error("Metric could not be interpreted", exc_info=True)
            sys.exit()
        c.metric = args.metric

    if args.psi:
        c.activate_psi_mode()

    com_file = None
    if config.EVAL:
        com_file = args.eval

    # Perform action
    try:
        if args.get_token:
            print(f"> Generated token at Key-Server:\n> {t}")
        elif args.hash_key:
            print(f"> Hash Key:\n> {c.get_hash_key().hex()}")
        elif args.hash is not None:
            h = args.hash
            r_list = c.get_record(h)
            print(f"> Retrieved: {[str(r) for r in r_list]}")
        elif args.similar is not None:
            target = parse_list(args.similar)
            logging.debug(f"Got: {str(target)}")
            print("> Number of Candidates: ",
                  len(list(c.compute_candidates(target, c.metric))))
        elif args.target is not None:
            target = parse_list(args.target)
            if config.EVAL:

                def execClient():
                    """Execute full retrieve and catch errors

                    :return: result, error
                    """
                    try:
                        return c.full_retrieve(target), None
                    except Exception as e:
                        error = str(e)
                        log.exception(error)
                        return None, error

                ram_usage, (result, error) = memory_usage(
                    (execClient,),
                    interval=config.RAM_INTERVAL,
                    include_children=True,
                    retval=True,
                )
                c.eval['result'] = result
                c.eval['ram_usage'] = ram_usage
                c.eval['error'] = error
                with open(com_file, "wb") as fd:
                    pickle.dump(c.eval, fd)
            else:
                res = c.full_retrieve(target)
                print("> Result:\n> ", end='')
                pprint.pprint([str(r) for r in res])
    except Exception as e:
        log.error(str(e), exc_info=True)
        sys.exit()
