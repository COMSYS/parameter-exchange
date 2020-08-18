#!/usr/bin/env python3
"""Bloom dependence on Error Rate."""

import numpy as np
from numpy import log as ln

# noinspection PyUnresolvedReferences
from plot.plot import (read_data, convert_to_gb, convert_to_minutes,
                       INPUT_DIR, OUTPUT_DIR, read_fp,
                       error_plot_mult, EXTENSION, plot_settings, Legend, )

PLOT_ALL = 1
output_dir = OUTPUT_DIR + 'bloom_error_dep/'
input_dir = INPUT_DIR + 'bloom_full_err/'
name = "butthead_bloom_fp"
xticks = [10 ** (-1)] + [10 ** (-i) for i in range(2, 21, 1) if i % 3 == 0]
xlabels = [fr"$10^{{-1}}$"] + [fr"$10^{{-{i}}}$" for i in range(2, 21, 1) if
                               i % 3 == 0] + [fr"$10^{{-20}}$"]
minor_xticks = [10 ** (-i) for i in range(2, 21, 1) if i % 3 != 0]
minor_xlabels = ["" for _ in minor_xticks]
# Adjusts
BOTTOM_ADJUST = 0.22
RIGHT_ADJUST = 0.985
TOP_ADJUST = 0.97
LEFT_ADJUST = 0.14


def comp_bloom_bits(n, p):
    m = np.ceil(-n * ln(p) / (ln(2) ** 2))
    return m


def bit_to_gb(b):
    return b / 8 / 1000 / 1000 / 1000


# Size
if 0 or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 2, 5, x_is_float=True)
        d = convert_to_gb(d)
        theo = {}
        for x in d:
            theo[x] = [bit_to_gb(comp_bloom_bits(100000000, x))] * 2
        error_plot_mult(
            [d, theo],
            output_dir + f'size{EXTENSION}',
            100000000,
            0,
            1.5,
            0.5,
            "FP Rate",
            "Size [GB]",
            "Bloom Filter Size (Capacity: 100Mio, Stored: To Cap., 10 Reps)",
            legend=Legend(['Measured', 'Theoretic'], location='upper left'),
            adjust=(LEFT_ADJUST, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks,
            xlabels=xlabels,
            minor_xticks=minor_xticks,
            minor_xlabels=minor_xlabels,
            log_base=10,
            x_log=True,
            x_sync=True,
            reverseX=True,
        )

# Query Time
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 2, 7, x_is_float=True)
        error_plot_mult(
            [d],
            output_dir + f'query_time{EXTENSION}',
            100000000,
            0,
            40,
            10,
            "FP Rate",
            "Query Time [s]",
            "Time for Query (Capacity: 100Mio, Stored: To Cap., 100Mio "
            "Queries, "
            "10 Reps)",
            adjust=(LEFT_ADJUST - 0.01, RIGHT_ADJUST, TOP_ADJUST,
                    BOTTOM_ADJUST),
            # 2/3 H adjust=(0.17, 0.98, 0.98, 0.16),
            xticks=xticks,
            xlabels=xlabels,
            minor_xticks=minor_xticks,
            minor_xlabels=minor_xlabels,
            log_base=10,
            x_log=True,
            x_sync=True
        )

# Insertion Time
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 2, 6, x_is_float=True)
        d = convert_to_minutes(d)
        error_plot_mult(
            [d],
            output_dir + f'insert_time{EXTENSION}',
            100000000,
            0,
            20,
            5,
            "FP Rate",
            "Insertion Time [min]",
            "Time for Insertion (Capacity: 100Mio, Stored: To Cap., 10 Reps)",
            adjust=(LEFT_ADJUST - 0.01, RIGHT_ADJUST, TOP_ADJUST,
                    BOTTOM_ADJUST),
            # 2/3 Height adjust=(0.17, 0.98, 0.98, 0.16),
            xticks=xticks,
            xlabels=xlabels,
            minor_xticks=minor_xticks,
            minor_xlabels=minor_xlabels,
            log_base=10,
            x_log=True,
            x_sync=True
        )

# FP Rate
if 0 or PLOT_ALL:
    d = read_fp(input_dir + f"{name}.csv", 2, 4, 8, x_is_float=True)
    xticks = [10 ** (-i) for i in range(1, 10, 1)]
    xlabels = [fr"$10^{{-{i}}}$" for i in range(1, 10, 1)]
    for k in list(d.keys())[:]:
        if k < 10 ** -9:
            del d[k]
    error_plot_mult(
        [d],
        output_dir + f'fp_rate{EXTENSION}',
        100000000,
        0,
        0.1,
        0.02,
        "FP Rate (Configured)",
        "FP Rate (Measured)",
        "False Positives (Capacity: 100Mio, Stored: To Cap., 100Mio Queries, "
        "10 Reps)",
        adjust=None,  # (0.06, 0.978, 0.979, 0.165),
        xticks=xticks,
        xlabels=xlabels,
        log_base=10,
        x_log=True,
        x_sync=True,
        reverseX=False,
        y_log=True,
        ylabels=[
            rf"$10^{{{i}}}$"
            for i in range(-9, 0)
        ],
        yticks=[
            10 ** i
            for i in range(-9, 0)
        ],
        grid=True,
    )
