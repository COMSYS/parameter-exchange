#!/usr/bin/env python3
"""Bloom dependence on Insert Size."""

# noinspection PyUnresolvedReferences
from typing import List

from plot.plot import (read_data, convert_to_gb, convert_to_minutes,
                       INPUT_DIR, OUTPUT_DIR, error_plot_mult,
                       EXTENSION, plot_settings, Legend)

PLOT_ALL = 1
output_dir = OUTPUT_DIR + 'bloom_insert_dep/'
input_dir = INPUT_DIR + 'bloom_full_insert/'
name = "butthead_bloom_insert"
xticks = [i for i in range(0, 10 ** 9 + 1, 10 ** 8)]
xlabels: List[str] = [0] + [
    f"{round(i / 10 ** 9, 1)} Bil" for i in
    xticks[1:]]
BOTTOM_ADJUST = 0.22
RIGHT_ADJUST = 0.935
TOP_ADJUST = 0.97
LEFT_ADJUST = 0.15

# Insert Time
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        d = read_data(input_dir + f"{name}.csv", 3, 6)
        d = convert_to_minutes(d)
        error_plot_mult(
            [d],
            output_dir + f'insert_time{EXTENSION}',
            100000000,
            0,
            350,
            50,
            "Inserted Elements [#]",
            "Insertion Time [min]",
            r"",
            x_label_step=2,
            auto_ylabels=True,
            adjust=(
                LEFT_ADJUST, RIGHT_ADJUST, TOP_ADJUST, BOTTOM_ADJUST),
            xticks=xticks,
            xlabels=xlabels
        )
