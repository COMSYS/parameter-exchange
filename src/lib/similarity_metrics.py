"""This module contains various similarity metrics.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import copy
import logging
import math
import re
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import List, Iterable, Sized

from lib import config as cnf
from lib.record import Record, round_s, get_power

log: logging.Logger = logging.getLogger(__name__)


class SimilarityMetricIterator(Iterator, ABC):  # pragma no cover
    """Base class for similarity metrics."""

    _rounding_vec: List[int] = None
    id_len: int = None

    def __iter__(self):
        return self

    def __init__(self, target: List[float],
                 *args,
                 rounding_vec: List[int] = None,
                 record_id_length: int = None):

        if rounding_vec is None:
            rounding_vec = cnf.ROUNDING_VEC
        if record_id_length is None:
            record_id_length = cnf.RECORD_ID_LENGTH
        if len(rounding_vec) != record_id_length:
            raise ValueError("Rounding Vector has to be as long as ID length:"
                             f"{len(rounding_vec)} vs {record_id_length}")
        self._rounding_vec = rounding_vec
        self.id_len = record_id_length

    @abstractmethod
    def split(self, n: int, j: int = 0) -> List[Iterator]:
        """
        Try to split iterator into at least (!) n smaller, as equal sized as
        possible, iterators if possible and into the maximal number otherwise.
        :param n: # Iterators to generate
        :param j: Index to split on
        :return: List of created Iterators
        """
        pass

    @abstractmethod
    def __len__(self):
        pass

    def __copy__(self):
        return copy.deepcopy(self)


class RecordIterator(Iterator):
    """
    Iterator encapsulating a similarity metric iterator but returning record
    objects.
    """

    def __init__(self, it: Iterable, hash_key: bytes):
        # noinspection PyTypeChecker
        self._iterator = iter(it)
        if isinstance(it, Sized):
            self._len = len(it)
        else:
            self._len = 0
        self._hash_key = hash_key

    def __iter__(self):
        return self

    def __next__(self) -> Record:
        vec = next(self._iterator)
        r = Record(vec, hash_key=self._hash_key)
        return r

    def __len__(self) -> int:
        if isinstance(self._iterator, Sized):
            return len(self._iterator)
        return self._len


class OffsetIterator(SimilarityMetricIterator, ABC):
    """Common base clase for offset metrics."""

    def __repr__(self) -> str:
        return f"<OffsetIterator from {self.min} to {self.max}>"

    end = False

    def split(self, n: int, j: int = 0) -> List[Iterator]:
        """
        Try to split iterator into at least n smaller, as equal sized as
        possible, iterators if possible and into the maximal number otherwise.
        :param n: # Iterators to generate
        :param j: Index to split on
        :return: List of created Iterators
        """
        if self.cur_vec != self.min or self.end:
            raise RuntimeError("Cannot call split on used iterator!")
        iterators = []
        inc = self.increments[j]
        diff = (self.max[j] - self.min[j]) / n
        diff = max(diff / inc, 1)
        for i in range(n):
            if i == 0:
                it = copy.deepcopy(self)
                it.min[j] = round_s(it.min[j], self._rounding_vec[j])
                it.max[j] = round_s(it.min[j] + int(diff) * inc,
                                    self._rounding_vec[j])
                iterators.append(it)
            elif round_s(iterators[-1].max[j] + inc,
                         self._rounding_vec[j]) <= self.max[
                    j]:
                it = copy.deepcopy(self)
                it.min[j] = round_s(iterators[-1].max[j] + inc,
                                    self._rounding_vec[j])
                it.max[j] = round_s(
                    self.min[j] + int((i + 1) * diff) * inc,
                    self._rounding_vec[j])
                iterators.append(it)
            else:  # pragma no cover
                break
        # Last iterator has to go till end
        iterators[-1].max[j] = self.max[j]
        for it in iterators:
            it.cur_vec = it.min[:]
        final_iterators = []
        if len(iterators) < n and j < self.id_len - 1:
            # Try to split on next index
            sub_num = int(math.ceil((n - len(iterators)) / len(iterators)))
            for it in iterators:
                final_iterators.extend(it.split(sub_num, j + 1))
        else:
            final_iterators = iterators
        if j == 0:
            log.debug(f"Final split into {len(final_iterators)} iterators.")
        # Debug
        # for it in final_iterators:
        #     print(it.min, it.max)
        return final_iterators

    @abstractmethod  # min and max are dependent on concrete implementation
    def __init__(self, target: List[float], offsets: List[float],
                 rounding_vec: List[int] = None,
                 record_id_length: int = None):
        super().__init__(target, rounding_vec=rounding_vec,
                         record_id_length=record_id_length)
        self.offsets = offsets
        self.start_pos = 0
        self.pos = self.id_len - 1
        self.end = False
        self.increments = []
        self.min = []
        self.max = []
        self.cur_vec = []

    def __next__(self) -> tuple:
        if self.end:
            raise StopIteration
        state = self.cur_vec[:]
        # Increment state
        while self.pos >= 0 and (
                self.increments[self.pos] == 0 or (
                round_s(self.cur_vec[self.pos] + self.increments[self.pos],
                        self._rounding_vec[self.pos]) > self.max[self.pos]
                )
        ):
            # We are at the maximum for this position, so we move one position
            # to the left.
            # 1. Reset current pos. to minimum
            self.cur_vec[self.pos] = self.min[self.pos]
            # 2. The increment may decrease the value over potency such that the
            # increment itself changes
            self.increments[self.pos] = compute_increment(
                self.cur_vec[self.pos], self._rounding_vec[self.pos])
            # 3. Move cursor left
            self.pos -= 1
        if self.pos >= 0 and \
                self.increments[self.pos] > 0 and \
                round_s(self.cur_vec[self.pos] + self.increments[self.pos],
                        self._rounding_vec[self.pos]) <= self.max[self.pos]:
            # We can increment the value at the current position
            self.cur_vec[self.pos] = round_s(
                self.cur_vec[self.pos] + self.increments[self.pos],
                self._rounding_vec[self.pos])
            # The increment may increase the value over potency such that the
            # increment itself changes
            self.increments[self.pos] = compute_increment(
                self.cur_vec[self.pos], self._rounding_vec[self.pos])
            # Go back to last value
            self.pos = self.id_len - 1
        else:
            # No increment possible
            self.end = True
        return tuple(state)

    def __len__(self) -> int:
        return comp_offset_num(self)


class AbsoluteOffsetIterator(OffsetIterator):
    """
    Offset Metric that uses an absolute distance for each item in list.
    """

    def __init__(self, target: List[float], offset: float,
                 rounding_vec: List[int] = None,
                 record_id_length: int = None):
        offsets = [offset for _ in range(len(target))]
        super().__init__(target, offsets, rounding_vec, record_id_length)
        self.min = []  # most negative value
        self.max = []  # most positive value
        for i, e in enumerate(target):
            if i < self.id_len:
                self.min.append(round_s(e - offset, self._rounding_vec[i]))
                self.max.append(round_s(e + offset, self._rounding_vec[i]))
                self.increments.append(
                        compute_increment(self.min[i], self._rounding_vec[i])
                )
                if self.min[-1] + self.increments[i] > self.max[-1]:
                    # Otherwise we might get conflicts for 100 and 99
                    self.min[-1] = e
            else:
                self.min.append(e)
        self.cur_vec = self.min[:]


class RelativeOffsetIterator(OffsetIterator):
    """
    Offset Metric that uses a relative distance for each item in list.
    """

    def __init__(self, target: List[float], offset: float,
                 rounding_vec: List[int] = None,
                 record_id_length: int = None):
        """

        :param target:
        :param offset: Offset in Percent < 100
        :param rounding_vec: Vector with rounding values
        :param record_id_length:
        """
        offsets = [offset for _ in range(len(target))]
        super().__init__(target, offsets, rounding_vec=rounding_vec,
                         record_id_length=record_id_length)
        offset = offset / 100
        self.min = []  # most negative value
        self.max = []  # most positive value
        for i, e in enumerate(target):
            if i < self.id_len:
                self.min.append(round_s(e * (1 - offset),
                                        self._rounding_vec[i]))
                self.max.append(round_s(e * (1 + offset),
                                        self._rounding_vec[i]))
                self.increments.append(
                    compute_increment(self.min[i], self._rounding_vec[i])
                )
                if self.min[-1] + self.increments[i] > self.max[-1]:
                    # Otherwise we might get conflicts for 100 and 99
                    self.min[-1] = e
            else:
                self.min.append(e)
        self.cur_vec = self.min[:]
        # print(self.min, self.max, self.increments)


class VariableOffsetIterator(OffsetIterator):
    """
    Offset Metric that uses a different relative distance for each item in
    list.
    """

    def __init__(self, target: List[float],
                 offsets: List[float],
                 positive_only: bool = False,
                 rounding_vec: List[int] = None,
                 record_id_length: int = None):
        """

        :param target:
        :param offsets: List of offsets for each entry of the target vector.
        len(offset) == len(target) !
        Special values:
            0: No variation
        :param rounding_vec: Vector with rounding values
        :param record_id_length:
        """
        super().__init__(target, offsets, rounding_vec=rounding_vec,
                         record_id_length=record_id_length)
        if self.id_len != len(offsets):
            raise ValueError(
                f"Offset List {len(offsets)} has to have ID length "
                f"({self.id_len}).")
        offsets = [i / 100 for i in offsets]
        self.min = []  # most negative value
        self.max = []  # most positive value
        for i, e in enumerate(target):
            if i < self.id_len:
                if positive_only:
                    self.min.append(
                        round_s(e, self._rounding_vec[i]))
                else:
                    self.min.append(
                        round_s(e * (1 - offsets[i]), self._rounding_vec[i]))
                self.max.append(
                    round_s(e * (1 + offsets[i]), self._rounding_vec[i]))
                self.increments.append(
                    compute_increment(self.min[i], self._rounding_vec[i])
                )
                if self.min[-1] + self.increments[i] > self.max[-1]:
                    # Otherwise we might get conflicts for 100 and 99
                    self.min[-1] = e
            else:
                self.min.append(e)
        self.cur_vec = self.min[:]


def compute_increment(n: float, rnd: int) -> float:
    """
    Compute the smallest increment for n.
    Special case rnd==0: increment is 1, n is exact int
    :param n: Value to increment
    :param rnd: Rounding value
    :return: Increment
    """
    if rnd == 0:
        # Special case
        return 1
    if n == 0:
        # Special case
        return 10 ** (1 - rnd)
    power = get_power(n)
    inc_power = power + 1 - rnd
    increment = 10 ** inc_power
    return increment


def comp_offset_num(o: OffsetIterator) -> int:
    """Compute the number of elements produces by an offest iterator"""
    total = 1
    var_per_pos = []
    for i in range(o.id_len):
        possibilities = 0
        # increment might change
        cur_min = o.min[i]
        inc = compute_increment(o.min[i], o._rounding_vec[i])
        if cur_min == 0:
            power = 0
        else:
            power = get_power(cur_min) + 1
        if 10 ** power < o.max[i]:
            cur_max = 10 ** power
            # +0.5inc b/c of float imprecision
            possibilities += int((cur_max - cur_min + 0.5 * inc) / inc)
            # Update increment
            inc = compute_increment(cur_max, o._rounding_vec[i])
            cur_min = cur_max
            power = get_power(cur_min) + 1
        # Now, we can cound till end
        # +0.5inc b/c of float imprecision
        possibilities += int((o.max[i] - cur_min + 0.5 * inc) / inc)
        possibilities += 1
        # +1 because min and max are always contained
        var_per_pos.append(possibilities)
    for n in var_per_pos:
        total *= n
    return round(total)


def map_metric(name: str) -> (SimilarityMetricIterator, list):
    """
    Map the given string name to a similarity metric.
    :param name: The name of the similarity metric.
    :return: The similarity metric class and Arguments
    """
    if (re.match(r'absOffset-\d+', name) is not None
            or re.match(r'offset-\d+', name) is not None):
        found = re.findall(r'\d+', name)
        if len(found) == 1:
            # int
            args = (int(found[0]),)
        else:
            # float
            args = (float(f"{found[0]}.{found[1]}"),)
        return AbsoluteOffsetIterator, args
    elif re.match(r'relOffset-\d+', name) is not None:
        found = re.findall(r'\d+', name)
        if len(found) == 1:
            # int
            args = (int(found[0]),)
        else:
            # float
            args = (float(f"{found[0]}.{found[1]}"),)
        return RelativeOffsetIterator, args
    elif name == "wzl1":
        # Any werkstueck, rest exact
        offsets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1000, 0, 0]
        return VariableOffsetIterator, (offsets, True)
    elif name == "wzl2":
        # Any werkstueck, rest exact
        offsets = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 400]
        return VariableOffsetIterator, (offsets, True)
    else:
        raise ValueError(f"No similarity metric with name {name} exists.")
