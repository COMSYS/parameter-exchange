#!/usr/bin/env python3
"""Bloom dependence on Query Size."""

# noinspection PyUnresolvedReferences
from typing import List

from plot.plot import (read_data, convert_to_gb, convert_to_minutes,
                       INPUT_DIR, OUTPUT_DIR, error_plot_mult,
                       EXTENSION, plot_settings, Legend)

PLOT_ALL = 1
output_dir = OUTPUT_DIR + 'bloom_query_dep/'
input_dir = INPUT_DIR + 'bloom_full_query/'
name = "butthead_bloom_query"
xticks = [i for i in range(0, 10 ** 9 + 1, 10 ** 8)]
xlabels: List[str] = [0] + [
    f"{round(i / 10 ** 9, 1)} Bil" for i in
    xticks[1:]]
BOTTOM_ADJUST = 0.22
RIGHT_ADJUST = 0.935
TOP_ADJUST = 0.97
LEFT_ADJUST = 0.11

# Query Time
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 4, 7)
        d = convert_to_minutes(d)
        error_plot_mult(
            [d],
            output_dir + f'query_time{EXTENSION}',
            100000000,
            0,
            350,
            50,
            "Queries [#]",
            "Query Time [min]",
            r"Time for Query (FP Rate: $1^{{-20}}$, Stored: To Cap., "
            r"1Bil Queries, "
            "10 Reps)",
            x_label_step=2,
            auto_ylabels=True,
            adjust=(LEFT_ADJUST, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks,
            xlabels=xlabels
        )
