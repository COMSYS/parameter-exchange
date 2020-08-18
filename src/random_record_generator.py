#!/usr/bin/env python3
"""Generate random records.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import sys
from typing import List

from lib import config
import random


def main(args=List[str]):
    """
    Generate random records according to the given CL arguments.
    :param args: Command line arguments
    """
    parser = argparse.ArgumentParser("Record  Generator")
    parser.add_argument('num', type=int, help="Number of records to generate.",
                        metavar="NUM")
    parser.add_argument('-o', '--output', type=str, default="records.tmp",
                        help="Output file.")
    parser.add_argument('-l', '--length', type=int, default=config.RECORD_LENGTH,
                        help="Length of records")
    parser.add_argument('--max', type=float, default=100,
                        help="Maximal value for items.")
    parser.add_argument('--min', type=float, default=0,
                        help="Minimal value for items.")

    args = parser.parse_args(args)

    records = []
    random.seed()
    for _ in range(args.num):
        records.append(
            [
                random.uniform(args.min, args.max)
                for _ in range(args.length)
            ]
        )
    with open(args.output, "w") as fd:
        fd.writelines([f"{str(r)}\n" for r in records])


if __name__ == '__main__':  # pragma no cover
    main(sys.argv[1:])
