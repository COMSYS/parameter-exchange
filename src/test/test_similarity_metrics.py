#!/usr/bin/env python3
"""Test the similarity metrics.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import copy
import unittest
from unittest import TestCase
from unittest.mock import patch

import lib.similarity_metrics as sm
from lib.record import Record


class SimilarityMetricsTest(unittest.TestCase):

    def test_map_metric(self):
        with self.assertRaises(ValueError):
            sm.map_metric("UNKNOWN")
        func, args = sm.map_metric("absOffset-1")
        self.assertEqual(sm.AbsoluteOffsetIterator, func)
        self.assertEqual(
            (1,), args)
        func, args = sm.map_metric("absOffset-0.5")
        self.assertEqual(sm.AbsoluteOffsetIterator, func)
        self.assertEqual(
            (0.5,), args)
        func, args = sm.map_metric("relOffset-1")
        self.assertEqual(sm.RelativeOffsetIterator, func)
        self.assertEqual(
            (1,), args)
        func, args = sm.map_metric("relOffset-0.5")
        self.assertEqual(sm.RelativeOffsetIterator, func)
        self.assertEqual(
            (0.5,), args)
        func, args = sm.map_metric("wzl1")
        self.assertEqual(sm.VariableOffsetIterator, func)
        offsets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1000, 0, 0]
        self.assertEqual(
            (offsets, True), args)
        func, args = sm.map_metric("wzl2")
        self.assertEqual(sm.VariableOffsetIterator, func)
        offsets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 400]
        self.assertEqual(
            (offsets, True), args)

    def test_offset(self):
        r = [2.0, 2.0, 3.0, 4.0]
        self.assertEqual(1,
                         len(list(sm.AbsoluteOffsetIterator(r, 0, [3, 3], 2))))
        self.assertEqual(441,
                         len(list(
                             sm.AbsoluteOffsetIterator(r, 0.1, [3, 3], 2))))
        r2 = [2000.0, 20000.0, 3.0, 4.0]
        self.assertEqual(3,
                         len(list(
                             sm.AbsoluteOffsetIterator(r2, 10, [3, 3], 2))))
        r = [200.0, 200.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 0.1, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual([(200.0, 200.0, 3.0, 4.0)], [i for i in it])

    def test_abs_offset_iterator(self):
        r = [1.0, 2.0, 3.0, 4.0]
        it = sm.AbsoluteOffsetIterator(r, 0.1, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(len(it), len([i for i in it]))

    def test_rel_offset_iterator(self):
        r = [2.0, 2.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 5, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(441, len([i for i in it]))
        r = [20.0, 20.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 0.5, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(9, len([i for i in it]))
        r = [200.0, 2.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 0.05, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual([(200.0, 2.0, 3.0, 4.0)], [i for i in it])

    def test_split(self):
        r = [200.0, 2.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 2, rounding_vec=[3, 3],
                                       record_id_length=2)
        l1 = [str(i) for i in it]
        l = [str(i) for i in it]
        with self.assertRaises(RuntimeError):
            it.split(5)
        it = sm.RelativeOffsetIterator(r, 2, rounding_vec=[3, 3],
                                       record_id_length=2)
        its = it.split(5)
        self.assertGreaterEqual(len(its), 5)
        l2 = []
        for it in its:
            l2.extend([str(i) for i in it])
        self.assertEqual(sorted(l1), sorted(l2))
        it = sm.RelativeOffsetIterator(r, 2, rounding_vec=[3, 3],
                                       record_id_length=2)
        its = it.split(5)
        for i in its:
            length = len(list(i))
            self.assertIn(length, [9, 18])
        # split on second
        it = sm.AbsoluteOffsetIterator(r, 0.5, rounding_vec=[2, 2],
                                       record_id_length=2)
        it2 = copy.deepcopy(it)
        l1 = [i for i in it2]
        its = it.split(5)
        self.assertEqual(4,
                         len(its))
        l2 = []
        for it in its:
            l2.extend([i for i in it])
        self.assertEqual(l1,
                         l2)

    def test_repr(self):
        r = [100.0, 1.0, 3.0, 4.0]
        t = sm.AbsoluteOffsetIterator(r, 1)
        self.assertEqual(
            "<OffsetIterator from [99.0, 0.0, 2.0, 3.0] to [101.0, 2.0, 4.0, "
            "5.0]>",
            str(t)
        )

    @patch("lib.config.RECORD_LENGTH", 4)
    def test_record_iterator(self):
        r = [100.0, 1.0, 3.0, 4.0]
        it = sm.RecordIterator([r], b"key")
        res = [i for i in it]
        self.assertEqual(
            [Record(r, hash_key=b"key")],
            res
        )

    @patch("lib.config.RECORD_LENGTH", 4)
    def test_record_iterator_len(self):
        r = [100.0, 1.0, 3.0, 4.0]
        it = sm.RecordIterator([r], b"key")
        self.assertEqual(1, len(it))
        m = sm.RelativeOffsetIterator(r, 5, rounding_vec=[3, 3],
                                      record_id_length=2)
        it = sm.RecordIterator(m, b"key")
        self.assertEqual(3136, len(it))
        it = sm.RecordIterator(iter([1]), b"key")
        self.assertEqual(0, len(it))

    def test_comp_offset_num(self):
        # Relative
        r = [2.0, 2.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 5, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(441, sm.comp_offset_num(it))
        r = [20.0, 20.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 0.5, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(9, sm.comp_offset_num(it))
        # Absolute
        r = [2.0, 2.0, 3.0, 4.0]
        it = sm.AbsoluteOffsetIterator(r, 0.1, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(441, sm.comp_offset_num(it))

    def test_len(self):
        r = [2.0, 2.0, 3.0, 4.0]
        offset = 0.5
        it = sm.RelativeOffsetIterator(r, offset, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(
            len([i for i in copy.deepcopy(it)]),
            len(it)
        )
        self.assertEqual(
            9,  # 3 * 3
            len(it)
        )
        offset = 5
        it = sm.RelativeOffsetIterator(r, offset, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(
            len([i for i in copy.deepcopy(it)]),
            len(it)
        )
        offset = 7
        it = sm.RelativeOffsetIterator(r, offset, rounding_vec=[3, 3],
                                       record_id_length=2)
        self.assertEqual(
            len([i for i in copy.deepcopy(it)]),
            len(it)
        )
        # Test len with power hop
        # Example of WZL data
        r = [1, 2.2, 60.0, 20.0, 60.0, 20.0, 60.0, 20.0,
             1, 1, 2, 22.5, 23.6, 30.2, 1, 1, 40.0, 165.0, 0.08]
        rounding = [0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 3, 0, 0, 3]
        id_len = 17
        offset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 400]
        it = sm.VariableOffsetIterator(r, offset, True, rounding, id_len)
        self.assertEqual(
            701,
            len(it)
        )

    def test_compute_increment(self):
        self.assertEqual(
            0.1,
            sm.compute_increment(44, 3)
        )
        self.assertEqual(
            0.01,
            sm.compute_increment(1, 3)
        )
        self.assertEqual(
            10,
            sm.compute_increment(1111, 3)
        )
        self.assertEqual(
            0.1,
            sm.compute_increment(-99, 3)
        )
        self.assertEqual(
            1,
            sm.compute_increment(-100, 3)
        )
        self.assertEqual(
            0.0001,
            sm.compute_increment(-0.03, 3)
        )
        self.assertEqual(
            1,
            sm.compute_increment(7, 0)
        )
        self.assertEqual(
            1,
            sm.compute_increment(10, 0)
        )
        self.assertEqual(
            1,
            sm.compute_increment(0.1, 0)
        )

    def test_copy(self):
        r = [1.0, 1.0, 3.0, 4.0]
        it = sm.RelativeOffsetIterator(r, 1, [2, 2], 2)
        it2 = copy.copy(it)
        self.assertEqual(len(it), len(it2))
        self.assertEqual(list(it), list(it2))

    def test_eval_offsets(self):
        r = [float(i) for i in range(1, 101)]
        rounding = [3 for _ in range(10)]
        for offset in range(1, 6):
            it = sm. RelativeOffsetIterator(r, offset, rounding, 10)
            # self.assertGreaterEqual(10**9, len(it), f"Offset: {offset}")


@patch("lib.config.RECORD_ID_LENGTH", 5)
@patch("lib.config.ROUNDING_VEC", [2 for _ in range(5)])
class TestVariableOffsetIterator(TestCase):
    target = [i for i in range(6)]

    def test_error(self):
        with self.assertRaises(ValueError) as e:
            sm.VariableOffsetIterator(self.target, [1, 2])

    def test_special_value_0(self):
        it = sm.VariableOffsetIterator(self.target, [0 for _ in range(5)])
        self.assertEqual(
            1,
            len(it)
        )
        self.assertEqual(
            [tuple(self.target)],
            [i for i in it]
        )

    def test_normal_case(self):
        # Basically 2 identical Iterators
        it = sm.VariableOffsetIterator(self.target, [10 for _ in range(5)])
        it2 = sm.RelativeOffsetIterator(self.target, 10)
        self.assertEqual(
            len(it),
            len(it2)
        )
        self.assertEqual(
            list(it),
            list(it2)
        )

    def test_manual_case(self):
        with patch("lib.config.ROUNDING_VEC", [2 for _ in range(3)]),\
              patch("lib.config.RECORD_ID_LENGTH", 3):
            target = [2.0, 2.0, 4.0]
            it = sm.VariableOffsetIterator(target, [5, 5, 2.5])
            self.assertEqual(
                {
                    (1.9, 2.0, 4.0),
                    (2.0, 2.0, 4.0),
                    (2.1, 2.0, 4.0),
                    (1.9, 1.9, 4.0),
                    (2.0, 1.9, 4.0),
                    (2.1, 1.9, 4.0),
                    (1.9, 2.1, 4.0),
                    (2.0, 2.1, 4.0),
                    (2.1, 2.1, 4.0),
                    (1.9, 2.0, 3.9),
                    (2.0, 2.0, 3.9),
                    (2.1, 2.0, 3.9),
                    (1.9, 1.9, 3.9),
                    (2.0, 1.9, 3.9),
                    (2.1, 1.9, 3.9),
                    (1.9, 2.1, 3.9),
                    (2.0, 2.1, 3.9),
                    (2.1, 2.1, 3.9),
                    (1.9, 2.0, 4.1),
                    (2.0, 2.0, 4.1),
                    (2.1, 2.0, 4.1),
                    (1.9, 1.9, 4.1),
                    (2.0, 1.9, 4.1),
                    (2.1, 1.9, 4.1),
                    (1.9, 2.1, 4.1),
                    (2.0, 2.1, 4.1),
                    (2.1, 2.1, 4.1),
                },
                set(it)
            )
            it = sm.VariableOffsetIterator(target, [5, 5, 2.5],
                                           positive_only=True)
            self.assertEqual(
                {
                    (2.0, 2.0, 4.0),
                    (2.1, 2.0, 4.0),
                    (2.0, 2.1, 4.0),
                    (2.1, 2.1, 4.0),
                    (2.0, 2.0, 4.1),
                    (2.1, 2.0, 4.1),
                    (2.0, 2.1, 4.1),
                    (2.1, 2.1, 4.1),
                },
                set(it)
            )
