#!/usr/bin/env python3
"""This file contains the implementation of the platform's key server
component

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import pickle
import secrets
import sys
from os import path
from typing import List

from lib import config
from lib.helpers import create_data_dir, keys_to_int

sys.path.append(config.WORKING_DIR + 'cython/ot')
# Python Version of libOTe
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTSender  # noqa


log: logging.Logger = logging.getLogger(__name__)


class KeyServer:
    """Implements backend key server functionality."""

    _hash_key: bytes = None
    _enc_keys: List[bytes] = []

    def __init__(self, data_dir=config.DATA_DIR) -> None:
        """
        Initialize key server.
        Either load keys from file or generate keys for all possible indices.
        :param data_dir: The directory containing the key files.
        """
        self.data_dir = data_dir
        create_data_dir(data_dir)
        if path.exists(self.data_dir + config.KEY_HASHKEY_PATH):
            log.info(
                "Loading hash key from file: " + self.data_dir +
                config.KEY_HASHKEY_PATH)
            with open(self.data_dir + config.KEY_HASHKEY_PATH, "rb") as fd:
                self._hash_key = pickle.load(fd)
        else:
            log.info("No key-file found. Generating hash key...")
            self._generate_hash_key()
        if path.exists(self.data_dir + config.KEY_ENCKEY_PATH):
            log.info(
                "Loading encryption keys from file: " + self.data_dir +
                config.KEY_ENCKEY_PATH)
            with open(self.data_dir + config.KEY_ENCKEY_PATH, "rb") as fd:
                self._enc_keys = pickle.load(fd)
        else:
            log.info(
                f"No key-file found. Generating {config.OT_SETSIZE} "
                f"encryption keys into {self.data_dir + config.KEY_ENCKEY_PATH}.")
            self._generate_enc_keys()
        super().__init__()
        log.info("Key Server initialization completed.")

    def get_hash_key(self) -> bytes:
        """
        Return hash key.
        :return: Hash Key
        """
        if self._hash_key is None:
            raise RuntimeError("No hash key has been generated yet!")
        return self._hash_key

    @staticmethod
    def _gen_key(bit_length: int) -> bytes:
        """
        Return a cryptographically random key with given length.
        :param bit_length: Length of key [Multiple of 8]
        :return: A key with given bit length
        """
        if bit_length % 8 != 0:
            raise ValueError("Bit length of keys to generate should be "
                             "multiple of 8/ 1 Byte.")
        return secrets.token_bytes(bit_length // 8)

    def _generate_hash_key(self) -> None:
        """Generate a hash key and store to file."""
        self._hash_key = self._gen_key(config.HASHKEY_LEN)
        # Store to file
        with open(self.data_dir + config.KEY_HASHKEY_PATH, "wb") as fd:
            pickle.dump(self._hash_key, fd)

    def _generate_enc_keys(self) -> None:
        """Generate one encryption key for each possible OT
        index and store to file."""
        self._enc_keys = []
        for _ in range(config.OT_SETSIZE):
            self._enc_keys.append(self._gen_key(config.ENCKEY_LEN))
        # Store to file
        with open(self.data_dir + config.KEY_ENCKEY_PATH, "wb") as fd:
            pickle.dump(self._enc_keys, fd)

    def offer_ot(self, total_ots: int, port: int = config.OT_PORT) -> None:
        """
        Initialize an OT to transit the keys.
        :param total_ots: Number of OTs to perform
        :param port: Port to use for OT Server
        :return: None
        """
        sender = PyOTSender()
        sender.totalOTs = total_ots
        if len(self._enc_keys) != config.OT_SETSIZE:
            raise RuntimeError(
                f"Key Server has {len(self._enc_keys)} keys but OT setsize is "
                f"{config.OT_SETSIZE}.")
        sender.numChosenMsgs = len(self._enc_keys)
        sender.numThreads = config.OT_THREADS
        sender.statSecParam = config.OT_STATSECPARAM
        sender.inputBitCount = config.OT_INPUT_BIT_COUNT
        sender.maliciousSecure = config.OT_MAL_SECURE
        sender.hostName = config.OT_HOST
        sender.port = port
        sender.serverCert = config.KEY_TLS_CERT
        sender.serverKey = config.KEY_TLS_KEY
        # keys to bytes
        keys = keys_to_int(self._enc_keys)
        log.info(
            f"Listening for OT connection on {sender.hostName}:{port}. TLS: "
            f"{config.OT_TLS}")
        sender.executeSame(keys, config.OT_TLS)
        log.debug(f"OTs done. Thread for port {port} terminating.")
