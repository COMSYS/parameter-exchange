#!/usr/bin/env python3
"""Bloom dependence on Capacity."""
from typing import List

import numpy as np
from numpy import log as ln

# noinspection PyUnresolvedReferences
from plot.plot import (read_data, convert_to_gb, convert_to_minutes,
                       INPUT_DIR, OUTPUT_DIR, error_plot_mult,
                       EXTENSION, plot_settings, Legend)

PLOT_ALL = 0
output_dir = OUTPUT_DIR + 'bloom_capacity_dep/'
input_dir = INPUT_DIR + 'bloom_full_cap/'
name = "butthead_bloom_cap"
xticks = [i for i in range(0, 10 ** 9 + 1, 10 ** 8)]
xlabels: List[str] = [0] + [
    f"{round(i / 10 ** 9, 1)} Bil" for i in
    xticks[1:]]
# Adjusts
BOTTOM_ADJUST = 0.22
RIGHT_ADJUST = 0.935
TOP_ADJUST = 0.97
LEFT_ADJUST = 0.13


def comp_bloom_bits(n, p):
    m = np.ceil(-n * ln(p) / (ln(2) ** 2))
    return m


def bit_to_gb(b):
    return b / 8 / 1000 / 1000 / 1000


# Size
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 1, 5)
        d = convert_to_gb(d)
        theo = {}
        for x in d:
            theo[x] = [bit_to_gb(comp_bloom_bits(x, 10 ** -20))] * 2
        error_plot_mult(
            [d, theo],
            output_dir + f'size{EXTENSION}',
            100000000,
            0,
            20,
            4,
            "Capacity [#]",
            "Size [GB]",
            r"Bloom Filter Size (FP Rate: $1^{{-20}}$, Stored: To Cap., "
            r"10 Reps)",
            legend=Legend(['Measured', 'Theoretic'], location="upper left"),
            adjust=(LEFT_ADJUST, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks[:],
            xlabels=xlabels[:],
            x_label_step=2
        )

# Query Time
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 1, 7)
        # d = convert_to_minutes(d)
        error_plot_mult(
            [d],
            output_dir + f'query_time{EXTENSION}',
            100000000,
            0,
            80,
            20,
            "Capacity [#]",
            "Query Time [s]",
            r"Time for Query (FP Rate: $1^{{-20}}$, Stored: To Cap., "
            r"1Bil Queries, "
            "10 Reps)",
            adjust=(LEFT_ADJUST, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks[:],
            xlabels=xlabels[:],
            x_label_step=2
        )

# Insertion Time
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 1, 6)
        d = convert_to_minutes(d)
        error_plot_mult(
            [d],
            output_dir + f'insert_time{EXTENSION}',
            100000000,
            0,
            400,
            100,
            "Capacity [#]",
            "Insertion Time [min]",
            r"Time for Insertion (FP Rate: $1^{{-20}}$, Stored: To Cap., "
            r"10 Reps)",
            adjust=(
                LEFT_ADJUST + 0.02, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks[:],
            xlabels=xlabels[:],
            x_label_step=2
        )

# Insertion Time alone
if 1 or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"butthead_bloom_cap_fixed_insert.csv", 1, 6)
        d = convert_to_minutes(d)
        error_plot_mult(
            [d],
            output_dir + f'solo_insert_time{EXTENSION}',
            100000000,
            0,
            100,
            20,
            "Capacity [#]",
            "Insertion Time [min]",
            r"Time for Insertion (FP Rate: $1^{{-20}}$, Stored: 100 Mio., "
            r"10 Reps)",
            adjust=(
                LEFT_ADJUST + 0.02, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks[:],
            xlabels=xlabels[:],
            x_label_step=2
        )
