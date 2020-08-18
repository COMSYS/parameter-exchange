#!/usr/bin/env python3
"""Evaluate the number of candidated produced by the offset metric.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import logging
import os

import numpy as np

from lib import config
from lib.logging import configure_root_loger
# Constants -------------------------------------------------------------------
from lib.similarity_metrics import comp_offset_num, RelativeOffsetIterator
from .shared import lb

METRIC = RelativeOffsetIterator
ARGS = [(10,)]  # [(i,) for i in range(1, 1001, 1)]
ROUNDS = 10
RECORD_ID_LENGTH = range(1, 100, 1)  # Value of Lego data.
RECORD_ROUNDING = [[3 for i in range(100)]]
RECORD_TOTAL_LENGTH = 100
POSITIVE_ONLY = False
RESUME = False
DIRECTORY = config.EVAL_DIR + "metric" + "/"
os.makedirs(DIRECTORY, exist_ok=True)
# -----------------------------------------------------------------------------
log = configure_root_loger(logging.INFO, None)


def write_header(file_path: str, row_format: str) -> None:
    """Write eval header to file"""
    with open(file_path, 'w') as fd:
        fd.write("------------------------HEADER------------------------\n")
        fd.write(f"EVAL: Metric Eval\n")
        fd.write(f"Metric: {get_metric_name()}\n")
        fd.write(f"Metric Args: {str(ARGS)}\n")
        fd.write(f"Positive Only: {str(POSITIVE_ONLY)}\n")
        fd.write(f"Data source: Random Data\n")
        fd.write(f"Record Rounding: {RECORD_ROUNDING}\n")
        fd.write(f"Record ID Length: {RECORD_ID_LENGTH}\n")
        fd.write(f"Record Total Length: {RECORD_TOTAL_LENGTH}\n")
        fd.write(f"Rounds: {ROUNDS}\n")
        fd.write(f"{row_format}\n")
        fd.write("----------------------END-HEADER----------------------\n")


def get_metric_name() -> str:
    return getattr(METRIC, '__name__', 'Unknown')


def fake_data_eval(base_name: str):
    """Evaluate the metric with fake data."""
    # Read Lego data
    file_path = DIRECTORY + base_name + '.csv'
    row_fmt = ("ROUND;"
               "METRIC;"
               "OFFSET;"
               "POS_ONLY;"
               "REC_LEN;"
               "REC_ID_LEN;"
               "REC_ROUNDING"
               ";#CANDIDATES")
    if not RESUME or not os.path.exists(file_path):
        write_header(file_path, row_fmt)
    # Start loop
    for round in lb(range(0, ROUNDS), "Rounds", position=0):
        for rounding in lb(RECORD_ROUNDING, "Rounding", leave=False):
            for id_len in lb(RECORD_ID_LENGTH, "ID Length", leave=False):
                for total_len in lb(RECORD_TOTAL_LENGTH, "Total Length",
                                    leave=False):
                    for offset in lb(ARGS, "Arguments", leave=False):
                        # target = [random.random() for _ in range(total_len)]
                        rounding_vec = [rounding[i] for i in range(id_len)]
                        target = [float(100) for i in range(total_len)]
                        it = METRIC(target,
                                    *offset,
                                    rounding_vec=rounding_vec,
                                    record_id_length=id_len)
                        total = comp_offset_num(it)
                        if len(offset) == 1:
                            offset = offset[0]
                        with open(file_path, 'a') as f:
                            f.write(';'.join((
                                str(round),
                                str(get_metric_name()),
                                str(offset),
                                str(POSITIVE_ONLY),
                                str(total_len),
                                str(id_len),
                                str(rounding_vec[0]),
                                str(total),
                                '\n'
                            )))


if __name__ == '__main__':
    p = argparse.ArgumentParser("Metric Eval")
    p.add_argument('--resume', help="Resume Eval", action="store_true")
    p.add_argument('-o', '--out', type=str, action='store',
                   help="Filename", required=True)
    p.add_argument('-r', '--rounds', help="How many rounds to perform?",
                   default=ROUNDS, type=int)
    cases = p.add_mutually_exclusive_group(required=False)
    cases.add_argument('--id1', action='store_true')
    cases.add_argument('--id2', action='store_true')
    cases.add_argument('--id3', action='store_true')
    cases.add_argument('--id4', action='store_true')
    cases.add_argument('--id5', action='store_true')
    cases.add_argument('--id6', action='store_true')
    cases.add_argument('--id7', action='store_true')
    cases.add_argument('--id8', action='store_true')
    cases.add_argument('--id9', action='store_true')
    cases.add_argument('--id10', action='store_true')
    cases.add_argument('--id11', action='store_true')
    cases.add_argument('--id12', action='store_true')
    args = p.parse_args()
    filename = args.out
    ROUNDS = args.rounds
    if args.id1:
        METRIC = RelativeOffsetIterator
        ARGS = [(i,) for i in np.arange(1, 50, 0.01)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 100
        RECORD_ID_LENGTH = 10
        RECORD_ROUNDING = [[3 for _ in range(RECORD_ID_LENGTH)]]
    elif args.id2:
        METRIC = RelativeOffsetIterator
        ARGS = [(i,) for i in np.arange(1, 50, 0.01)]
        POSITIVE_ONLY = True
        RECORD_TOTAL_LENGTH = 100
        RECORD_ID_LENGTH = 10
        RECORD_ROUNDING = [[3 for _ in range(RECORD_ID_LENGTH)]]
    elif args.id3:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = range(10, 100)
        RECORD_ID_LENGTH = 10
        RECORD_ROUNDING = [[3 for _ in range(RECORD_ID_LENGTH)]]
    elif args.id4:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 100
        RECORD_ID_LENGTH = range(1, 100)
        RECORD_ROUNDING = [[3 for _ in range(100)]]
    elif args.id5:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 100
        RECORD_ID_LENGTH = 10
        RECORD_ROUNDING = [[i for _ in range(RECORD_ID_LENGTH)] for i in
                           range(1, 10)]
    elif args.id6:
        METRIC = RelativeOffsetIterator
        ARGS = [(i,) for i in np.arange(1, 20, 0.01)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 28
        RECORD_ID_LENGTH = 21
        RECORD_ROUNDING = [[2 for _ in range(RECORD_ID_LENGTH)]]
    elif args.id7:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 28
        RECORD_ID_LENGTH = 21
        RECORD_ROUNDING = [[i for _ in range(RECORD_ID_LENGTH)] for i in
                           range(1, 10)]
    elif args.id8:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 28
        RECORD_ID_LENGTH = range(1, 21)
        RECORD_ROUNDING = [[2 for _ in range(21)]]
    elif args.id9:
        METRIC = RelativeOffsetIterator
        ARGS = [(i,) for i in np.arange(1, 20, 0.01)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 19
        RECORD_ID_LENGTH = 17
        RECORD_ROUNDING = [[3 for _ in range(RECORD_ID_LENGTH)]]
    elif args.id10:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 19
        RECORD_ID_LENGTH = 17
        RECORD_ROUNDING = [[i for _ in range(RECORD_ID_LENGTH)] for i in
                           range(1, 10)]
    elif args.id11:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 19
        RECORD_ID_LENGTH = range(1, 17)
        RECORD_ROUNDING = [[3 for _ in range(17)]]
    elif args.id12:
        METRIC = RelativeOffsetIterator
        ARGS = [(10,)]
        POSITIVE_ONLY = False
        RECORD_TOTAL_LENGTH = 100
        RECORD_ID_LENGTH = 10
        RECORD_ROUNDING = [[j] + [3 for i in range(9)] for j in range(1, 10)]

    fake_data_eval(filename)
