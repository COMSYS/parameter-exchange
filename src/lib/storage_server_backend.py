#!/usr/bin/env python3
"""This file contains the implementation of the platform's storage server
component

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
import sys
from typing import List, Iterable, Tuple

from pybloomfilter import BloomFilter

import lib.config as config
from lib.base_client import UserType
from lib.helpers import from_base64
from lib.record import hash_to_index
from lib.user_database import Owner, Client, get_user
from storage_server.storage_database import StoredRecord, db, \
    BillingInfo, RecordRetrieval

sys.path.append(config.WORKING_DIR + 'cython/psi')
# Python Version of libPSIe
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSISender  # noqa

# Log configuration
log: logging.Logger = logging.getLogger(__name__)


class StorageServer:
    """Implements the storage server of the platform."""

    _bloom: BloomFilter = None
    _data_dir: str = config.DATA_DIR

    @property
    def bloom(self):
        """
        Return bloom filter containing the record hashes (as base64 encoding).
        Needs to be a property to avoid concurrency problems with mutltiple
        threads. Initialize with database contents it no bloom filter exists.

        :return: Bloom Filter
        """
        if self._bloom is None:
            # Initialize
            bloom_file = self.data_dir + config.BLOOM_FILE
            if os.path.isfile(bloom_file):
                self._bloom = BloomFilter.open(
                    filename=bloom_file)
                log.info(f"Bloom Filter loaded from file {bloom_file}!")
            else:
                # new Bloom filter
                self._initialize_bloom_filter()
        return self._bloom

    def __init__(self, data_dir=config.DATA_DIR) -> None:
        """Set data directory and create it, if it does not exist."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _initialize_bloom_filter(self) -> None:
        """
        Create new bloom filter and add all values from storage DB.
        """
        bloom_file = self.data_dir + config.BLOOM_FILE
        self._bloom = BloomFilter(config.BLOOM_CAPACITY,
                                  config.BLOOM_ERROR_RATE,
                                  bloom_file)
        records = StoredRecord.query.all()
        for r in records:
            self._bloom.add(r.hash)
        log.info(f"Created new Bloom Filter @ {bloom_file}.")

    def store_record(self, hash_val: str, ciphertext: str, owner: str) -> None:
        """
        Store the record with the given attributes into the DB.
        :param hash_val: Base64 of record's long hash
        :param ciphertext: json.dumps(ciphertext-dict)
        :param owner: owner of record as string
        :return:
        """
        log.debug("Store record called.")
        records = [(hash_val, ciphertext, owner)]
        self.batch_store_records_db(records)
        self.batch_store_records_bloom(records)
        log.info(f"Stored record: {hash_val} - {ciphertext} of {owner}")

    @staticmethod
    def batch_store_records_db(records: List[Iterable[str]]) -> None:
        """Store all records in the list into the database.

        :param records: List of records, each represented as a tuple of the
            base64 encoded long hash, the ciphertext as json.dumps and the
            owner as string:
            [
                ('Base64(HASH-1)', 'json.dumps(CIPHERTEXT-1)', 'owner-1'),
                ('Base64(HASH-2)', 'json.dumps(CIPHERTEXT-2)', 'owner-2'),
                ...
            ]

        """
        log.debug("Batch store record DB called.")
        recs = [
            StoredRecord(hash=h, ciphertext=c, owner=o)
            for (h, c, o) in records
        ]
        for r in recs:
            db.session.add(r)
        db.session.commit()
        log.info("Successfully stored records into DB.")

    def batch_store_records_bloom(self, records: List[Iterable[str]]) -> None:
        """Store all records in the list into the bloom filter.

        :param records: List of records, each represented as a tuple of the
            base64 encoded long hash, the ciphertext as json.dumps and the
            owner as string:
            [
                ('Base64(HASH-1)', 'json.dumps(CIPHERTEXT-1)', 'owner-1'),
                ('Base64(HASH-2)', 'json.dumps(CIPHERTEXT-2)', 'owner-2'),
                ...
            ]

        """
        log.debug("Batch store record Bloom called.")
        for (hash_val, record, owner) in records:
            self.bloom.add(hash_val)

    @staticmethod
    def get_record(hash_base64: str,
                   client: str) -> List[Tuple[str, str]]:
        """Retrieve records with defined base64 encoded hash. There might be
        multiple ciphertexts with the same hash.

        :param hash_base64: Base64 encoded hash
        :param client: Username of client requesting the records
        :return: List of matching records, each represented as a tuple with
        two elements ['Base64(HASH)', 'json.dumps(CIPHERTEXT)'].
        I.e. an example returned value might be:
            [
                ['Base64(HASH)', 'json.dumps(CIPHERTEXT-1)'],
                ['Base64(HASH)', 'json.dumps(CIPHERTEXT-2)']
            ]
        """
        log.debug("Get record called.")
        res = StorageServer.batch_get_records([hash_base64], client)
        if not res:
            raise ValueError(f"No record for hash exists: '{hash_base64}'")
        else:
            return res

    @staticmethod
    def _add_to_billing_db(records: List[StoredRecord], client: Client,
                           transaction: RecordRetrieval):
        """
        Compute and store billing information.
        :param transaction: The corresponding transaction
        :param records: The records retrieved from the database
        :param client: The client performing the query
        :return: None
        """
        # Count per owner
        owners = {}
        for r in records:
            if r.owner in owners:
                owners[r.owner] += 1
            else:
                owners[r.owner] = 1
        # Add to billing db
        for owner in owners:
            o: Owner = Owner.query.filter_by(username=owner).first()
            if o is None:
                raise ValueError(f"Owner '{o}'does not exist!")
            s = BillingInfo(provider=o,
                            count=owners[o.username],
                            client=client,
                            transaction=transaction)
            db.session.add(s)
        db.session.commit()

    @staticmethod
    def _add_to_transaction_db(records: List[StoredRecord], client: Client,
                               hashes: List[str]) -> RecordRetrieval:
        """
        Create a transaction and store the number of encryption keys the
        client would have to retrieve from the key server.
        :param records: The records retrieved from the database
        :param client: The client performing the query
        :param hashes: The hashes send by the client
        :return: The created RecordRetrieval
        """
        bh = 0
        #  Number of encryption keys for all requested hashes
        br = 0
        #  Number of encryption keys fo all returned records
        ot_indices = []
        for r in records:
            ind = hash_to_index(from_base64(r.hash), config.OT_INDEX_LEN)
            if ind not in ot_indices:
                br += 1
                ot_indices.append(ind)
        ot_indices.clear()
        for h in hashes:
            ind = hash_to_index(from_base64(h), config.OT_INDEX_LEN)
            if ind not in ot_indices:
                bh += 1
                ot_indices.append(ind)

        t = RecordRetrieval(
            client=client,
            enc_keys_by_hash=bh,
            enc_keys_by_records=br
        )
        db.session.add(t)
        db.session.commit()
        return t

    @staticmethod
    def batch_get_records(hashes: List[str],
                          client: str) -> List[Tuple[str, str]]:
        """
        Return all records matching at least one hash in the list.
        Store access into billing database.

        :param hashes: List of base64 encoded hashes:
            ['Base64(HASH-1)', 'Base64(HASH-2)', 'Base64(HASH-3)']
        :param client: Username of client requesting the records
        :return: List of matching records, each represented as a tuple with
        two elements ['Base64(HASH)', 'json.dumps(CIPHERTEXT)'].
        I.e. an example returned value might be:
            [
                ('Base64(HASH-1)', 'json.dumps(CIPHERTEXT-1)'),
                ('Base64(HASH-1)', 'json.dumps(CIPHERTEXT-2)'),
                ('Base64(HASH-2)', 'json.dumps(CIPHERTEXT-3)')
            ]
        ( Multiple ciphertexts per hash possible)
        """
        res: List[StoredRecord] = StoredRecord.query.filter(
            StoredRecord.hash.in_(hashes)).all()
        c = get_user(UserType.CLIENT, client)
        t = StorageServer._add_to_transaction_db(res, c, hashes)
        StorageServer._add_to_billing_db(res, c, t)
        return [
            (r.hash, r.ciphertext)
            for r in res
        ]

    def get_bloom_filter(self) -> bytes:
        """
        Return a base64 encoding of the server's bloom filter.
        :return: bytes: base64 encoding of bloom filter
        """
        return self.bloom.to_base64()

    @staticmethod
    def get_all_record_psi_hashes() -> List[int]:
        """
        Return the PSI hashes for all stored records.
        :return: List of PSI Indices as Ints
        """
        records = StoredRecord.query.all()
        res = [get_psi_index(r.hash) for r in records]
        return res

    @staticmethod
    def offer_psi(setSize: int = config.PSI_SETSIZE,
                  port: int = config.PSI_PORT,
                  scheme: str = config.PSI_SCHEME) -> None:
        """
        Initialize an PSI to transit the Indices.
        :param setSize: Size of the sets compared with PSI
        :param port: For PSI server to listen on
        :param scheme: Which PSI to use
        :return: None
        """
        sender = PyPSISender()
        records = StorageServer.get_all_record_psi_hashes()
        log.debug(f"Server set without dummies: {str(records)}")
        if len(records) > setSize:
            raise RuntimeError("More records than PSI Setsize allows.")

        # Add unique dummies
        dummy = config.PSI_DUMMY_START_SERVER
        while len(records) < setSize:
            records.append(dummy)
            dummy += 1

        sender.statSecParam = config.PSI_STATSECPARAM
        sender.setSize = setSize

        sender.hostName = config.PSI_HOST
        sender.port = port
        sender.numThreads = config.PSI_THREADS
        sender.tls = config.PSI_TLS

        sender.serverCert = config.KEY_TLS_CERT
        sender.serverKey = config.KEY_TLS_KEY

        log.info(
            f"Listening for PSI connection on {sender.hostName}:{sender.port}."
            f"TLS: {sender.tls}")
        sender.execute(scheme, records)
        log.debug(f"PSI done. Thread for port {sender.port} terminating.")


def get_psi_index(long_hash_base64: str) -> int:
    """
    Convert the base64 encoded long hash into the corresponding
    PSI Index.
    :param long_hash_base64: Long hash in Base64 encoding
    :return: PSI Index as Integer
    """
    long_hash_bytes: bytes = from_base64(long_hash_base64)
    psi_index = hash_to_index(long_hash_bytes, config.PSI_INDEX_LEN)
    return psi_index
