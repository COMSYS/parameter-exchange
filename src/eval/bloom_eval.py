#!/usr/bin/env python3
"""Evaluate bloom filter properties.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import logging
import math
import os
import random
import time
from tempfile import NamedTemporaryFile

import numpy
from pybloomfilter import BloomFilter

from eval.shared import get_last_line
from lib import config
from lib.logging import configure_root_loger
from .shared import lb

# Constants -------------------------------------------------------------------
CAPACITY = range(0, 1000000001, 100000000)  # 10 ** 8
# ERROR_RATE = 10 ** -20
ERROR_RATE = [10 ** (-i) for i in range(1, 21)]
INSERT = 10 ** 8  # range(0, 1000000001, 100000000)  # CAPACITY  # FULL
INSERT_STEP = 10 ** 7
ROUNDS_START = 0
ROUNDS_END = 10
QUERY = 0  # range(10 ** 8, 10 ** 9 + 1, 10 ** 8)  # 10 ** 8  # 100.000.000
QUERY_ALL = False
RESUME = False
FILL = False
# -----------------------------------------------------------------------------
log = configure_root_loger(logging.INFO, None)


def get_file_path(base_name: str, file_name: str) -> str:
    """Return path to file."""
    directory = config.EVAL_DIR + base_name + "/"
    os.makedirs(directory, exist_ok=True)
    return directory + file_name


def get_file_name(base_name: str, query=True) -> str:
    """
    Compute file path to eval path.
    """
    file_name = f"{base_name}_{random.randint(1, 1000)}.csv"
    while os.path.exists(file_name):
        file_name = f"{base_name}_{random.randint(1, 1000)}.csv"
    return file_name


def write_header(base_name: str, file_path: str, row_format: str) -> None:
    """Write eval header to file."""
    with open(file_path, 'w') as fd:
        fd.write("------------------------HEADER------------------------\n")
        fd.write(f"EVAL: {base_name}\n")
        fd.write(f"Capacity: {CAPACITY}\n")
        fd.write(f"Error Rate: {ERROR_RATE}\n")
        if FILL:
            fd.write(f"Inserted Dummy values: Filled to capacity.\n")
        else:
            fd.write(f"Inserted Dummy values: {INSERT}\n")
        if "Partial" in base_name:
            fd.write(f"INSERT STEP: {INSERT_STEP}\n")
        if QUERY_ALL:
            fd.write(f"Perfomed queries: 100 / FP Rate\n")
        else:
            fd.write(f"Perfomed queries: {QUERY}\n")
        fd.write(f"Rounds: {ROUNDS_END}\n")
        fd.write(f"{row_format}\n")
        fd.write("----------------------END-HEADER----------------------\n")


def get_round(file_path: str) -> int:
    """Read round from given file."""
    with open(file_path, 'r') as fd:
        last = get_last_line(fd)
        state = last.split(';')
        rs = int(state[0])
        log.warning(f"Resuming at round {ROUNDS_START}")
    return rs


def bloom_full(basename: str):
    """Measure all values at once."""
    if basename is None:
        raise ValueError("No basename given.")
    file_path = get_file_path("bloom_full", basename)
    partial_insert_file = file_path.replace(".csv", "_partial_insert.csv")
    rs = ROUNDS_START
    if not RESUME or not os.path.exists(file_path):
        # Write header if new file only
        row_fmt = f"ROUND;CAPACITY;ERROR_RATE;INSERTED ELEMENTS;" \
                  f"QUERIED ELEMENTS;SIZE;INSERT TIME;QUERY TIME;" \
                  f"# False Positives"
        write_header("Bloom Full", file_path, row_fmt)
        # row_fmt = f"ROUND;CAPACITY;ERROR_RATE;INSERTED ELEMENTS;" \
        #           f"SIZE;INSERT_TIME[s](for elements added in step);"
        # write_header("Bloom Partial Insert", partial_insert_file, row_fmt)
    else:
        # Read values to resume
        rs = get_round(file_path)
    for r in lb(range(rs, ROUNDS_END), "Rounds"):
        for capacity in lb(CAPACITY, "Capacities", leave=False):
            for error_rate in lb(ERROR_RATE, "Error Rates", leave=False):
                if FILL:
                    i = [capacity]
                else:
                    i = lb(INSERT, "Inserts", leave=False)
                for insert in i:
                    with NamedTemporaryFile() as tmp:
                        b = BloomFilter(capacity, error_rate, tmp.name)
                        real_set = [random.random() for _ in range(insert)]
                        start = time.monotonic()
                        for s in real_set:
                            # Add random value
                            b.add(s)
                        insert_time = time.monotonic() - start
                        size = len(b.to_base64())
                        if QUERY_ALL:
                            query_range = int(math.ceil(100 / error_rate))
                        else:
                            query_range = QUERY
                        for query in lb(query_range, "Queries", leave=False):
                            # +1 because only values <1 stored
                            query_set = [
                                random.random() + 1 for _ in range(query)]
                            start = time.monotonic()
                            false_positives = 0
                            for q in query_set:
                                if q in b:
                                    false_positives += 1
                            query_time = time.monotonic() - start
                            with open(file_path, "a") as fd:
                                fd.write(
                                    f"{r};{capacity};{error_rate};"
                                    f"{insert};{query};{size};{insert_time};"
                                    f"{query_time};{false_positives}\n")


if __name__ == '__main__':
    p = argparse.ArgumentParser("Bloom Eval")
    p.add_argument('--resume', help="Resume Eval", action="store_true")
    p.add_argument('--fill', help="Fill up to capacity", action="store_true")
    p.add_argument('-r', '--reps', help="Rounds", action='store', default=0,
                   type=int)
    p.add_argument('-c', '--capacity',
                   help="Capacity: Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('-e', '--error',
                   help="Error Rate: Either constant or 3 values.",
                   action='store', type=float,
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+')
    p.add_argument('-i', '--insert',
                   help="Inserted Values: Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('-q', '--query',
                   help="Number of random element queries:"
                        "Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('-o', '--out', type=str, action='store',
                   help="Filename", required=True)
    args = p.parse_args()
    if args.resume:
        RESUME = True
    if args.fill:
        log.warning("Using Fill Mode!")
        FILL = True
    else:
        log.warning("Not using Fill Mode!")
        FILL = False
    if args.reps > 0:
        ROUNDS_END = args.reps
    if args.capacity is not None:
        if len(args.capacity) == 1:
            CAPACITY = args.capacity[0]
        elif len(args.capacity) == 3:
            CAPACITY = range(args.capacity[0],
                             args.capacity[1] + args.capacity[2],
                             args.capacity[2])
        else:
            raise ValueError("Either 1 or 3 capacity parameters!")
    if args.error is not None:
        if len(args.error) == 1:
            ERROR_RATE = args.error[0]
        elif len(args.error) == 3:
            ERROR_RATE = numpy.arange(args.error[0],
                                      args.error[1] + args.error[2],
                                      args.error[2])
        else:
            raise ValueError("Either 1 or 3 error parameters!")
    if args.insert is not None:
        if len(args.insert) == 1:
            INSERT = args.insert[0]
        elif len(args.insert) == 3:
            INSERT = range(args.insert[0],
                           args.insert[1] + args.insert[2],
                           args.insert[2])
        else:
            raise ValueError("Either 1 or 3 insert parameters!")
    if args.query is not None:
        if len(args.query) == 1:
            QUERY = args.query[0]
        elif len(args.query) == 3:
            QUERY = range(args.query[0],
                          args.query[1] + args.query[2],
                          args.query[2])
        else:
            raise ValueError("Either 1 or 3 query parameters!")
    filename = args.out + ".csv"
    bloom_full(filename)
