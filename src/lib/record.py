#!/usr/bin/env python3
"""
Class representing one record.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import hashlib
import json
import logging
import struct
from typing import List, Tuple, Any

from Crypto.Cipher import AES

from lib import config
from lib.helpers import to_base64, from_base64

log: logging.Logger = logging.getLogger(__name__)


def get_power(n: float) -> int:
    """Get power of number in scientific representation."""
    if n == 0:
        raise ValueError("log10(0) undefined!")
    power = 0
    abs_n = abs(n)
    if abs_n >= 1:
        while 10 ** (power + 1) <= abs_n:
            power += 1
    else:
        while 10 ** power > abs_n:
            power -= 1
    return power


def round_s(n: float, rnd: int) -> float:
    """Round to rnd digits, including those before point.
    rnd = 0 means exact value (no rounding).
    Examples for rnd = 3:
        1.1111 = 1.11
        22.2222 = 22.2
        222.2222 = 222
        2222.2222 = 2220
        66666.66666 = 66700
    """
    if rnd < 0:
        raise ValueError(
            f"Rounding values has to be 0 or larger, but is: {rnd}")
    if rnd == 0 or n == 0:
        # Exact
        return n
    power = get_power(n)
    n = n * 10 ** (-power)
    n = round(n, rnd - 1)  # One number before point
    n = n * 10 ** power
    fac = max(0, rnd - 1 - power)
    n = round(n, fac)  # Round because of imprecision
    return n


def hash_to_index(hash_v: bytes, bit_len: int) -> int:
    """Return a index of given bit length derived from the hash value."""

    byte_len = bit_len // 8
    overhang = bit_len % 8
    in_bytes = hash_v[:byte_len]
    num = int.from_bytes(in_bytes, byteorder='little')
    if overhang != 0:
        num += (hash_v[byte_len] % (2 ** overhang)) * (2 ** (byte_len * 8))
    return num


def round_record(record: List[float],
                 rnd_vec: List[int] = config.ROUNDING_VEC,
                 id_len: int = config.RECORD_ID_LENGTH) -> List[float]:
    """
    Transfer record to rounded representation:
    (11.1, 222.2, 3333.33) _ (1.11, 222, 3330)
    :param rnd_vec: Record Rounding Parameters
    :param id_len: ID length of record (X Part)
    :param record: Vector to transform
    :return: Transformed result vector
    """
    res = []
    for i, e in enumerate(record[:id_len]):
        res.append(round_s(e, rnd_vec[i]))
    return res


class Record:
    """Class representing one data record."""

    _long_hash: bytes = None
    _hash_key: bytes = None
    _encryption_key: bytes = None
    _rounding_vector: List[int] = None

    def __ne__(self, o: object) -> bool:
        return not self.__eq__(o)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Record):
            return False
        if self.owner is None or o.owner is None:
            return self.record == o.record
        else:
            return self.record == o.record and self.owner == o.owner

    def __init__(self, record: List[float] or Tuple[float], owner: str = None,
                 hash_key: bytes = None
                 ) -> None:
        """Store record and owner. Hashes are only generated on-demand."""
        for i in record:
            if not isinstance(i, int) and not isinstance(i, float):
                raise TypeError("Records must only contain numbers!")
        if len(record) != config.RECORD_LENGTH:
            raise ValueError(
                f"Record has not a length of {config.RECORD_LENGTH},"
                f"But: {len(record)}!")
        self.record = [float(i) for i in record]
        self.owner = owner
        self._identfier_length = config.RECORD_ID_LENGTH
        self._rounding_vector = config.ROUNDING_VEC
        if hash_key is not None:
            self.set_hash_key(hash_key)

    def get_long_hash(self) -> bytes:
        """Return the long hash used in the bloom filter and for record
        retrieval. It is a 512 bit SHA-3. Hashes are only generated on-demand.
        """
        if self._hash_key is None:
            raise ValueError("The hash key has to be set before hashes can "
                             "be computed!")
        if self._long_hash is None:
            m = hashlib.sha3_512(self._hash_key)
            m.update(self._get_identifier())
            self._long_hash = m.digest()
        return self._long_hash

    def get_psi_index(self) -> int:
        """Return the shorter hash used for PSI converted to an int.
        Hashes are only generated on-demand.

        :return: PSI Index as Integer
        """
        return hash_to_index(self.get_long_hash(), config.PSI_INDEX_LEN)

    def get_ot_index(self) -> int:
        """Return the shorter hash used for OT converted to an int.
        Hashes are only generated on-demand.

        :return: OT Value as Integer
        """
        return hash_to_index(self.get_long_hash(), config.OT_INDEX_LEN)

    def _get_rounded_record(self) -> List[float]:
        """Return the record with each entry rounded according to the"""
        return round_record(self.record, self._rounding_vector,
                            config.RECORD_ID_LENGTH)

    def set_hash_key(self, key: bytes) -> None:
        """Set the key ussed in hashing."""
        self._hash_key = key

    def set_encryption_key(self, key: bytes) -> None:
        """Define the key used for encryption."""
        self._encryption_key = key

    def _get_identifier(self) -> bytes:
        """Return portion of record that is used for hashing as byte
        string."""
        # The * 2 is caused by the usage of a scientific representation with
        # two entries per position.
        return str(self._get_rounded_record()).encode('utf-8')

    def get_encrypted_record(self, enc_key: bytes = None, nonce: bytes =
                             None) -> dict:
        """
        Return the encrypted form of the record.
        :param enc_key: Key used for encryption.
        :param nonce: DEBUG ONLY!
        :return: Encrypted record as dict
        """
        if enc_key is None and self._encryption_key is None:
            raise ValueError("No encryption key defined.")
        if enc_key is not None:
            self._encryption_key = enc_key
        length = len(self.record).to_bytes((len(self.record).bit_length() + 7)
                                           // 8,
                                           byteorder='big')
        buf = struct.pack('%sd' % len(self.record), *self.record)
        data = buf
        longhash = self.get_long_hash()
        key = self._encryption_key
        # log.debug(f"Encryption - Using key: {self._encryption_key}")
        if nonce is not None:
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        else:
            cipher = AES.new(key, AES.MODE_GCM)
        cipher.update(length)
        cipher.update(longhash)
        ciphertext, mac = cipher.encrypt_and_digest(data)
        json_k = ['nonce', 'length', 'hash', 'ciphertext', 'mac']
        json_v = [to_base64(x) for x in
                  (cipher.nonce, length, longhash, ciphertext, mac)]
        result = dict(zip(json_k, json_v))
        return result

    @classmethod
    def from_ciphertext(cls, ciphertext: dict, key: bytes) -> Any:
        """Create a record by decrypting a ciphertext"""
        log.debug(f"Decryption - Using key: {key}")
        b64 = ciphertext
        json_k = ['nonce', 'length', 'hash', 'ciphertext', 'mac']
        jv = {k: from_base64(b64[k]) for k in json_k}
        cipher = AES.new(key, AES.MODE_GCM, nonce=jv['nonce'])
        cipher.update(jv['length'])
        cipher.update(jv['hash'])
        length = int.from_bytes(jv['length'], byteorder='big')
        plaintext = cipher.decrypt_and_verify(jv['ciphertext'], jv['mac'])
        record_list = struct.unpack('%sd' % length, plaintext)
        record = Record(record_list)
        return record

    def to_hash_rec_tuple(self) -> Tuple[str, List[float]]:
        """Return record as a tuple (long-hash HEX, record)"""
        return "0x" + self.get_long_hash().hex(), self.record

    def to_full_tuple(self) -> Tuple[str, List[float], str]:
        """Return record as a tuple (long-hash. Hex, reocrd, owner)"""
        if self.owner is None:
            raise ValueError(
                "Full tuple can only be provided if an owner is defined.")
        return "0x" + self.get_long_hash().hex(), self.record, self.owner

    def get_owner(self):
        """Return owner."""
        if self.owner is None:
            raise RuntimeError("No owner set.")
        return self.owner

    def get_upload_format(self) -> Tuple[str, str, str]:
        """
        Return format required for upload to storage server
        :return: [Base64(long_hash), json.dumps(ciphertext), owner]
        """
        return (
            to_base64(self.get_long_hash()),
            json.dumps(self.get_encrypted_record()),
            self.get_owner()
        )

    def __str__(self) -> str:
        if self._hash_key is None and self.owner is None:
            return str((self.record,))
        elif self._hash_key is None:
            return str((self.record, self.owner))
        if self.owner is None:
            return str(self.to_hash_rec_tuple())
        else:
            return str(self.to_full_tuple())
