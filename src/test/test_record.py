#!/usr/bin/env python3
"""Test for record class.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
from unittest import TestCase
from unittest.mock import patch

from lib.helpers import from_base64
from lib.record import Record, hash_to_index, round_s, get_power

rounding = 3
id_len = 3


@patch("lib.config.RECORD_ID_LENGTH", id_len)
@patch("lib.config.RECORD_LENGTH", 5)
class TestRecord(TestCase):
    record = [1.1, 22.22, 333.333, 4444.4444, 55555.55555]
    owner = "Testowner"
    hash_key = b"abcde"
    encryption_key = b"stEinAESPasswort"
    longhash_hex = (
        "0c449889397b9499e55f53911b21772e119a8c9128c47329f64888b0e42be"
        "3acaa82747aa5c328efbce2255b39057bd090d37e500a3e2af19009f983e9dbf293"
    )
    longhash = bytes.fromhex(longhash_hex)
    ciphertext = {
        'ciphertext': '/eHeyXRfvvtRrm2kQs+i6+g/x6OuChngHdoPb1ZSv29jHn+GbwR'
                      '+EQ==',
        'hash':
            'DESYiTl7lJnlX1ORGyF3LhGajJEoxHMp9kiIsOQr46yqgnR6pcMo77ziJVs5B'
            'XvQkNN+UAo+KvGQCfmD6dvykw==',
        'length': 'BQ==',
        'mac': 'r07173RxSg4fX0b3v4sb6A==',
        'nonce': 'g2xlxbCW2c77STMpf5wNpQ=='}

    @patch("lib.config.RECORD_LENGTH", 5)
    @patch("lib.config.RECORD_ID_LENGTH", id_len)
    @patch("lib.config.ROUNDING_VEC", [rounding for _ in range(id_len)])
    def setUp(self) -> None:
        """Create dummy record."""
        self.r = Record(self.record)

    def test_hash_to_index(self):
        h1 = bytes.fromhex("ffffffffffffffff")
        h2 = bytes.fromhex("c4dff7abcdef")
        self.assertEqual(
            hash_to_index(h1, 32),
            2 ** 32 - 1
        )
        self.assertEqual(
            hash_to_index(h1, 11),
            2 ** 11 - 1
        )
        self.assertEqual(
            hash_to_index(h2, 21),
            1564612
        )

    def test_init(self):
        r = Record(self.record, self.owner)
        self.assertEqual(r.record, self.record)
        self.assertEqual(r.owner, self.owner)
        self.assertIsNone(r._long_hash)
        with self.assertRaises(TypeError):
            Record(["test"])
        with self.assertRaises(ValueError):
            # Bad record length
            Record([1, 2, 3])

    def test_get_long_hash(self):
        with self.assertRaises(ValueError):
            self.r.get_long_hash()
        self.r._hash_key = self.hash_key
        h = self.r.get_long_hash()
        self.assertEqual(len(h), 64)
        self.assertEqual(self.longhash_hex, h.hex())

    @patch("lib.config.PSI_INDEX_LEN", 128)
    def test_get_psi_index(self):
        with self.assertRaises(ValueError):
            self.r.get_psi_index()
        self.r._hash_key = self.hash_key
        h = self.r.get_psi_index()
        self.assertEqual(61763042635925203158941279474836587532, h)

    def test_get_owner(self):
        with self.assertRaises(RuntimeError):
            self.r.get_owner()
        self.r.owner = "erik"
        self.assertEqual("erik", self.r.get_owner())

    def test_get_ot_index(self):
        with self.assertRaises(ValueError):
            self.r.get_ot_index()
        self.r._hash_key = self.hash_key
        h = self.r.get_ot_index()
        self.assertEqual(541708, h)

    def test__get_rounded_record(self):
        res = self.r._get_rounded_record()
        rounded = [1.1, 22.2, 333.0]
        self.assertEqual(rounded, res)
        self.r._rounding_vector = [0, 0, 0]
        self.assertEqual(self.record[:3],
                         self.r._get_rounded_record())

    def test_set_hash_key(self):
        self.r.set_hash_key(self.hash_key)
        self.assertEqual(self.hash_key, self.r._hash_key)

    def test_set_encryption_key(self):
        self.r.set_encryption_key(self.encryption_key)
        self.assertEqual(self.encryption_key, self.r._encryption_key)

    def test__get_identifier(self):
        self.assertEqual(self.r._get_identifier(),
                         str([1.1, 22.2, 333.0]).encode('utf-8'))

    def test_get_encrypted_record(self):
        self.r._hash_key = self.hash_key
        with self.assertRaises(ValueError):
            self.r.get_encrypted_record()
        res = self.r.get_encrypted_record(
            self.encryption_key,
            nonce=from_base64(self.ciphertext['nonce']))
        self.assertEqual(self.ciphertext, res)

    def test_from_ciphertext(self):
        r = Record.from_ciphertext(self.ciphertext, self.encryption_key)
        self.assertEqual(r.record, self.record)

    def test_str(self):
        self.assertEqual(
            str(self.r),
            f"({str(self.record)},)"
        )
        self.r.owner = self.owner
        self.assertEqual(
            str(self.r),
            f"({str(self.record)}, '{self.owner}')"
        )
        self.r.owner = None
        self.r._hash_key = self.hash_key
        self.assertEqual(
            str(self.r),
            f"('0x{self.longhash_hex}', {str(self.record)})"
        )
        self.r.owner = self.owner
        self.assertEqual(
            str(self.r),
            f"('0x{self.longhash_hex}', {str(self.record)}, '{self.owner}')"
        )

    def test_to_hash_rec_tuple(self):
        self.r._hash_key = self.hash_key
        self.assertEqual(self.r.to_hash_rec_tuple(),
                         ("0x" + self.longhash_hex, self.record))

    def test_to_full_tuple(self):
        self.r._hash_key = self.hash_key
        with self.assertRaises(ValueError):
            self.r.to_full_tuple()
        self.r.owner = self.owner
        self.assertEqual(self.r.to_full_tuple(),
                         ("0x" + self.longhash_hex, self.record, self.owner))

    def test_equality(self):
        r2 = Record(self.record, "Has-Owner")
        r3 = Record([1, 2, 3, 4, 5], "Has-Owner")
        self.assertTrue(self.r == self.r)
        # different type
        self.assertTrue(self.r != "Record")
        # no owner on one side
        self.assertTrue(self.r == r2)
        self.assertTrue(r2 == self.r)
        # both have owner
        self.assertTrue(r2 == r2)
        self.assertTrue(r2 != r3)

    def test_round_s(self):
        with self.assertRaises(ValueError):
            round_s(1, -1)
        for sign in [-1, 1]:
            self.assertEqual(
                sign * 0.00112,
                round_s(sign * 0.00111999, 3)
            )
            self.assertEqual(
                sign * 0.0111,
                round_s(sign * 0.01111111, 3)
            )
            self.assertEqual(
                sign * 0.111,
                round_s(sign * 0.11111, 3)
            )
            self.assertEqual(
                sign * 1.11,
                round_s(sign * 1.11, 3)
            )
            self.assertEqual(
                sign * 11.1,
                round_s(sign * 11.11, 3)
            )
            self.assertEqual(
                sign * 111,
                round_s(sign * 111.11, 3)
            )
            self.assertEqual(
                sign * 1110,
                round_s(sign * 1111.11, 3)
            )
            self.assertEqual(
                sign * 11100,
                round_s(sign * 11111.11, 3)
            )
            self.assertEqual(
                sign * 1.11,
                round_s(sign * 1.11, 0)
            )
            self.assertEqual(
                sign * 11.111111111,
                round_s(sign * 11.111111111, 0)
            )

    def test_get_power(self):
        with self.assertRaises(ValueError):
            get_power(0)
