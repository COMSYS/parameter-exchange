#!/usr/bin/env python3
"""Base Client for both client applications.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import atexit
import logging
import math
import multiprocessing as mp
import sys
import time
from abc import ABC, abstractmethod
from typing import List, Tuple, Iterable

import requests
import urllib3
# noinspection PyUnresolvedReferences
from memory_profiler import profile

from lib import config, helpers
from lib.helpers import from_base64, encryption_keys_from_int

sys.path.append(config.WORKING_DIR + 'cython/ot/')
sys.path.append(config.WORKING_DIR + 'cython/psi/')
# Python Version of libOTe
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTReceiver  # noqa
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSIReceiver  # noqa

log: logging.Logger = logging.getLogger(__name__)

KEYSERVER = f"https://{config.KEYSERVER_HOSTNAME}:{config.KEY_API_PORT}"
STORAGESERVER = f"https://{config.STORAGESERVER_HOSTNAME}:" \
                f"{config.STORAGE_API_PORT}"


class UserType:
    """Allowed user types in this system."""
    CLIENT = "client"
    OWNER = "provider"


class ServerType:
    """Type of servers used by the system."""
    KeyServer = "key_server"
    StorageServer = "storage_server"


class BaseClient(ABC):
    """Abstract base class for the end-user clients of client and data
    providers. """

    user: str = None
    password: str = None
    KEYSERVER: str = None
    STORAGESERVER: str = None
    _hash_key: bytes = None
    eval = {
        'ot_tcpdump_sent': [],
        'ot_tcpdump_recv': [],
        'psi_tcpdump_sent': [],
        'psi_tcpdump_recv': []
    }

    @property
    @abstractmethod
    def type(self) -> str:
        """It has to be defined whether this is a client or owner client
        app, see UserType above."""
        pass  # pragma no cover

    def __init__(self, username: str) -> None:
        """Create object."""
        # Disable warnings for self-signed cert.
        urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)
        self.user = username
        self.KEYSERVER = KEYSERVER + "/" + self.type
        self.STORAGESERVER = STORAGESERVER + "/" + self.type

    def get_auth_data(self, url: str) -> Tuple[str, str]:
        """Return authentication information for authentication towards
        key or storage server.

        :type url: URL to determine server from
        :return (Username, Token
        """
        if KEYSERVER in url:
            server_type = ServerType.KeyServer
        elif STORAGESERVER in url:
            server_type = ServerType.StorageServer
        else:
            raise ValueError(f"Unknown server type for url: {url}")
        return self.user, self.get_token(server_type)

    def get(self, url: str,
            auth: Tuple[str, str] or None = None) -> requests.Response:
        """
        Perform a get request and check result.
        :param url: URL to request
        :param auth: Only if no Token Authentication used.
        :return: Response object.
        """
        if auth is None:
            auth = self.get_auth_data(url)
        r = requests.get(url, verify=config.TLS_ROOT_CA, auth=auth)
        if r.status_code == 401:
            raise RuntimeError(
                f"Authentication failed at: {url}.")
        elif r.status_code != 200 and r.status_code != 202:
            r.raise_for_status()
        else:
            return r

    def post(self, url: str, json: dict or Iterable,
             auth: Tuple[str, str] or None = None) -> requests.Response:
        """
        Perform a POST request and check result.
        :param url: URL to request
        :param json: JSON to transmit with request
        :param auth: Only if no Token Authentication used.
        :return: Response object.
        """
        if auth is None:
            auth = self.get_auth_data(url)
        r = requests.post(url, verify=config.TLS_ROOT_CA, auth=auth, json=json)
        if r.status_code == 401:
            raise RuntimeError(
                f"Authentication failed at: {url}.")
        elif r.status_code != 200 and r.status_code != 202:
            r.raise_for_status()
        else:
            return r

    def get_hash_key(self) -> bytes:
        """Return hash key retrieved from key server

        :return Hash Key as Bytes object
        """
        if self._hash_key is None:
            r = self.get(f"{self.KEYSERVER}/hash_key")
            # Revert encoding -> sent as Base64
            self._hash_key = from_base64(r.json()['hash_key'])
            log.debug("Retrieved Hash Key: " + str(self._hash_key))
        return self._hash_key

    # noinspection PyUnboundLocalVariable
    def _retrieve_keys(self, inidices: list, q=None) -> List[int]:
        """Return the encryption keys for the given indizes after retrieval
        from the key server.

        :indices: List of Indices to retrieve
        :return: List of retrieved keys (as ints) in same order
        """
        num_ots = len(inidices)
        r = self.get(
            f"{self.KEYSERVER}/key_retrieval?totalOTs={num_ots}")
        d = r.json()
        if not d['success']:
            raise RuntimeError(f"Key retrieval failed: {d['msg']}")
        if d['tls'] != config.OT_TLS:
            raise RuntimeError(
                f"Mismatch of server and client TLS settings. Client: "
                f"{config.OT_TLS} Server: {d['tls']}.")
        host = d['host']
        port = d['port']
        if d['tls']:
            tls = "with"
        else:
            tls = "without"
        log.info(f"Connecting for OT to host {host} on port {port} {tls} "
                 f"TLS. Will perform {num_ots} OTs.")

        if config.EVAL:  # pragma no cover
            to_svr, f1 = helpers.start_trans_measurement(
                port, direction="dst", sleep=False)
            from_svr, f2 = helpers.start_trans_measurement(
                port, direction="src", sleep=False)
            if q is not None:
                q.put(f1)  # Sent first
                q.put(f2)  # Recv second
            time.sleep(1)  # Wait for startup

        keys = self._receive_ots(inidices,
                                 host, port, d['tls'])

        log.debug(f"Completed OT.")
        return keys

    def _get_enc_keys(self, all_indices: List[int]) -> List[bytes]:
        """Return the encryption keys for the given indizes after retrieval
        from the key server.

        :param all_indices: List of Indices to retrieve
        :return: List of retrieved keys (as bytes) in same order
        """
        if len(all_indices) == 0:
            return []
        # The index list may stil contain duplicates.
        indices = []
        mapping = {}  # Map for 'index: entry_in_indices_list'
        for index in all_indices:
            if index not in indices:
                mapping[index] = len(indices)
                indices.append(index)
        keys = []
        step = config.OT_MAX_NUM
        if config.PARALLEL and len(indices) > step:
            if len(indices) / step > config.MAX_PROCS:
                # Would spawn too many processes
                step = int(math.ceil(len(indices) / config.MAX_PROCS))
            m = mp.Manager()
            results = m.dict()  # Order needs to hold
            errors = m.list()
            processes = []
            queues = []
            j = 0

            def parallel_func(
                    indices: List[int],
                    proc_num: int,
                    q: mp.Queue):  # pragma no cover
                """Process function."""
                try:
                    res = self._retrieve_keys(indices, q=q)
                    results[proc_num] = res
                except Exception as e:
                    errors.append(e)

            for i in range(0, len(indices), step):
                queue = mp.Queue()
                queues.append(queue)
                p = mp.Process(target=parallel_func,
                               args=(indices[i:i + step], j,
                                     queue))
                processes.append(p)
                p.start()
                atexit.register(p.terminate)
                j += 1
            log.info("All OT processes started.")
            # Wait for termination
            for i, p in enumerate(processes):
                p.join()
                atexit.unregister(p.terminate)
                if config.EVAL:  # pragma no cover
                    q = queues[i]
                    self.eval['ot_tcpdump_sent'].append(q.get())  # First sent
                    self.eval['ot_tcpdump_recv'].append(q.get())  # Send recv
            # Check result
            for e in errors:  # pragma no cover
                log.error(str(e))
                raise e
            # Reassemble
            for key in sorted(results.keys()):
                keys.extend(results[key])
        else:
            q = None
            if config.EVAL:  # pragma no cover
                q = mp.Queue()
            for i in range(0, len(indices), step):
                keys.extend(self._retrieve_keys(indices[i:(i + step)], q=q))
            if config.EVAL:  # pragma no cover
                self.eval['ot_tcpdump_sent'].append(q.get())  # First sent
                self.eval['ot_tcpdump_recv'].append(q.get())  # Send recv
        # Convert keys appropriately
        converted_keys = encryption_keys_from_int(keys)
        # Map back to original indices with duplicates
        result = []
        for index in all_indices:
            # get index in converted_keys:
            ind = mapping[index]
            result.append(converted_keys[ind])
        return result

    def set_password(self, pwd: str) -> None:
        """
        Set password for this user
        :param pwd: Password of this used
        :return: None
        """
        self.password = pwd

    def get_token(self, server_type: str) -> str:
        """Retrieve a token from the given server.

        :param server_type: The type of server to get the token from
        :return Token as string, can be used for authentication as is.
        """
        log.debug("Get token from key server.")
        if self.password is None:
            raise ValueError("To retrieve a token, the user has to be "
                             "authenticated.")
        if server_type == ServerType.StorageServer:
            server = self.STORAGESERVER
        elif server_type == ServerType.KeyServer:
            server = self.KEYSERVER
        else:
            raise ValueError(f"No Server '{server_type}' exists.")
        r = self.get(
            f"{server}/gen_token",
            auth=(self.user, self.password))
        r = r.json()
        if not r['success']:
            msg = f"Token generation failed: {r['msg']}"
            raise RuntimeError(msg)
        else:
            return r['token']

    @staticmethod
    def _receive_ots(
            choices, host, port, tls, threads: int =
            config.OT_THREADS, root_ca: str = config.TLS_ROOT_CA,
            mal_sec: bool = config.OT_MAL_SECURE,
            stat_sec: int = config.OT_STATSECPARAM, input_bit_count:
            int = config.OT_INPUT_BIT_COUNT,
            num_chosen_msgs: int = config.OT_SETSIZE) -> List[int]:
        """
        Execute an OT with the given choices
        :return: List of received INTEGERS
        """
        log.debug("Starting OT.")
        recv = PyOTReceiver()
        recv.totalOTs = len(choices)
        recv.numThreads = threads
        recv.hostName = host
        recv.port = port
        recv.rootCA = root_ca
        recv.maliciousSecure = mal_sec
        recv.statSecParam = stat_sec
        recv.inputBitCount = input_bit_count
        recv.numChosenMsgs = num_chosen_msgs
        result = recv.execute(choices, tls)
        log.debug("OTs complete.")
        return result

    @staticmethod
    def _receive_psi(
            client_set, host, port, tls, threads: int =
            config.OT_THREADS, root_ca: str = config.TLS_ROOT_CA,
            stat_sec: int = config.OT_STATSECPARAM,
            scheme: str = config.PSI_SCHEME) -> List[int]:
        """
        Perform a PSI with the given client_set
        :return: All items that matches the server_set
        """
        log.debug("Starting PSI.")
        recv = PyPSIReceiver()

        recv.statSecParam = stat_sec
        recv.setSize = len(client_set)

        recv.hostName = host
        recv.port = port
        recv.numThreads = threads
        recv.tls = tls
        recv.rootCA = root_ca
        # We use a new process to make killing possible
        q = mp.Queue()

        def exec():  # pragma no cover
            result = recv.execute(scheme, client_set)
            q.put(result)

        p = mp.Process(target=exec)
        p.start()
        atexit.register(p.terminate)
        p.join()
        atexit.unregister(p.terminate())
        result = q.get()
        # result = recv.execute(scheme, client_set)
        # The PSI only returns the indices of the matching client_set
        log.debug("PSI complete.")
        return [client_set[r] for r in result]
