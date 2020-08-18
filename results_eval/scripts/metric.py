#!/usr/bin/env python3
"""Bloom Size Plot."""
import os
# noinspection PyUnresolvedReferences
import pickle

from plot.plot import (error_plot_mult, read_data,
                       INPUT_DIR, OUTPUT_DIR, EXTENSION, plot_settings)

PLOT_ALL = True
output_dir = OUTPUT_DIR + 'metric/'
os.makedirs(output_dir, exist_ok=True)
input_dir = INPUT_DIR + 'metric/'

# ROWS
METRIC = 1
OFFSET = 2
POSITIVE = 3
TOTAL_LEN = 4
ID_LEN = 5
ROUNDING = 6
CANDIDATES = 7

y_label = "Candidates [#]"
x_axis = {
    OFFSET: "Offset [%]",
    TOTAL_LEN: "Record Length [#]",
    ID_LEN: "ID Parameters [#]",
    ROUNDING: "Rounding Value"
}
# ADJUSTS
TOP = 0.985
BOTTOM = 0.22
LEFT = 0.16
RIGHT = 0.95

evals = [
    {
        'name': 'metric_id12',
        'x': ROUNDING,
        'x_step': 2,
        'x_float': False,
        'y': CANDIDATES,
        'title': 'Rel. Offset: ID Len. 10; 10% Offset',
        'y_log': True,
        'auto_y': True,
        'y_step': 1 * 10 ** 20,
        'y_max': 5 * 10 ** 20,
        'adjust': (LEFT + 0.005, RIGHT + 0.03, TOP, BOTTOM),
        'half_width': True,
        'out': 'rounding_single',
        'xticks': [i for i in range(0, 10, 2)],
        'xlabels': [i for i in range(0, 10, 2)],
        'minor_xticks': [i for i in range(1, 10, 2)],
        'minor_xlabels': ['' for i in range(1, 10, 2)],
    },
    {
        'name': 'metric_id1',
        'x': OFFSET,
        'x_step': 5,
        'x_float': True,
        'y': CANDIDATES,
        'title': 'Rel. Offset: ID Len. 10; Rounding: 3',
        'y_log': True,
        'adjust': (LEFT, RIGHT + 0.02, TOP, BOTTOM),
        'half_width': True,
        'out': 'offset',
        'xticks': [i for i in range(0, 51, 10)],
        'xlabels': [i for i in range(0, 51, 10)],
    },
    # {
    #     'name': 'metric_id2',
    #     'x': OFFSET,
    #     'x_step': 5,
    #     'x_float': True,
    #     'y': CANDIDATES,
    #     'title': 'Rel. Offset: ID Len. 10; Rounding: 3; Positive Offset',
    #     'y_log': True,
    #     'adjust': (LEFT, RIGHT, TOP, BOTTOM),
    #     'half_width': True,
    #     'out': 'offset_positive'
    # },
    # {
    #     'name': 'metric_id3',
    #     'x': TOTAL_LEN,
    #     'x_step': 10,
    #     'x_float': False,
    #     'y': CANDIDATES,
    #     'title': 'Rel. Offset: ID Len. 10; Rounding: 3; 10% Offset',
    #     'y_log': False,
    #     'auto_y': False,
    #     'y_step': 1 * 10 ** 20,
    #     'y_max': 5 * 10 ** 20,
    #     'scientific_y': True,
    #     'adjust': (LEFT, RIGHT, TOP, BOTTOM),
    #     'half_width': True,
    #     'out': 'total_len'
    # },
    {
        'name': 'metric_id4',
        'x': ID_LEN,
        'x_step': 10,
        'x_float': False,
        'y': CANDIDATES,
        'title': 'Rel. Offset: Rounding: 3; 10% Offset',
        'y_log': True,
        'adjust': (LEFT + 0.015, RIGHT + 0.01, TOP, BOTTOM),
        'half_width': True,
        'out': 'id_len',
        'y_lim_bottom': 1,
        'xticks': [i for i in range(0, 101, 20)],
        'xlabels': [i for i in range(0, 101, 20)],
        'minor_xticks': [i for i in range(10, 101, 20)],
        'minor_xlabels': ['' for i in range(10, 101, 20)],
    },
    {
        'name': 'metric_id5',
        'x': ROUNDING,
        'x_step': 2,
        'x_float': False,
        'y': CANDIDATES,
        'title': 'Rel. Offset: ID Len. 10; 10% Offset',
        'y_log': True,
        'adjust': (LEFT + 0.005, RIGHT + 0.03, TOP, BOTTOM),
        'half_width': True,
        'out': 'rounding_all',
        'y_lim_bottom': 1,
        'xticks': [i for i in range(0, 10, 2)],
        'xlabels': [i for i in range(0, 10, 2)],
        'minor_xticks': [i for i in range(1, 10, 2)],
        'minor_xlabels': ['' for i in range(1, 10, 2)],
    },
    # {
    #     'name': 'metric_id6',
    #     'x': OFFSET,
    #     'x_step': 5,
    #     'x_float': True,
    #     'y': CANDIDATES,
    #     'title': 'IKV - Relative Offset',
    #     'y_log': True,
    #     'adjust': (LEFT, RIGHT, TOP, BOTTOM),
    #     'half_width': True,
    #     'out': 'offset_ikv'
    # },
    # {
    #     'name': 'metric_id7',
    #     'x': ROUNDING,
    #     'x_step': 2,
    #     'x_float': False,
    #     'y': CANDIDATES,
    #     'title': 'IKV - Relative Offset',
    #     'y_log': True,
    #     'adjust': (LEFT + 0.015, RIGHT + 0.03, TOP - 0.03, BOTTOM),
    #     'half_width': True,
    #     'out': 'rounding_ikv'
    # },
    # {
    #     'name': 'metric_id8',
    #     'x': ID_LEN,
    #     'x_step': 2,
    #     'x_float': False,
    #     'y': CANDIDATES,
    #     'title': 'IKV - Relative Offset',
    #     'y_log': True,
    #     'adjust': (LEFT, RIGHT + 0.02, TOP, BOTTOM),
    #     'half_width': True,
    #     'out': 'id_len_ikv'
    # },
    # {
    #     'name': 'metric_id9',
    #     'x': OFFSET,
    #     'x_step': 5,
    #     'x_float': True,
    #     'y': CANDIDATES,
    #     'title': 'WZL - Relative Offset',
    #     'y_log': True,
    #     # 'y_lim': 10 ** 39,
    #     'adjust': (LEFT, RIGHT, TOP - 0.025, BOTTOM),
    #     'half_width': True,
    #     'out': 'offset_wzl'
    # },
    # {
    #     'name': 'metric_id10',
    #     'x': ROUNDING,
    #     'x_step': 2,
    #     'x_float': False,
    #     'y': CANDIDATES,
    #     'title': 'WZL - Relative Offset',
    #     'y_log': True,
    #     'adjust': (LEFT + 0.015, RIGHT + 0.03, TOP, BOTTOM),
    #     'half_width': True,
    #     'out': 'rounding_wzl'
    # },
    # {
    #     'name': 'metric_id11',
    #     'x': ID_LEN,
    #     'x_step': 2,
    #     'x_float': False,
    #     'y': CANDIDATES,
    #     'title': 'WZL - Relative Offset',
    #     'y_log': True,
    #     'adjust': (LEFT, RIGHT + 0.02, TOP, BOTTOM),
    #     'half_width': True,
    #     'out': 'id_len_wzl'
    # },
]

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Metric
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
for eval in evals:
    d = read_data(input_dir + f"{eval['name']}.csv", eval['x'], eval['y'],
                  x_is_float=eval['x_float'])
    with open(input_dir + f"{eval['name']}.pyc", 'wb') as f:
        pickle.dump(d, f)
for eval in evals:
    with plot_settings(half_width=eval['half_width']):
        with open(input_dir + f"{eval['name']}.pyc", 'rb') as f:
            d = pickle.load(f)
        error_plot_mult(
            [d],
            output_dir + f"{eval['out']}{EXTENSION}",
            eval['x_step'],
            0,
            eval['y_max'] if 'y_max' in eval else 0,
            eval['y_step'] if 'y_step' in eval else 0,
            x_axis[eval['x']],
            y_label,
            eval['title'],
            adjust=eval['adjust'] if 'adjust' in eval else None,
            y_log=eval['y_log'],
            auto_ylabels=True if 'auto_y' not in eval else eval['auto_y'],
            y_lim=eval['y_lim'] if 'y_lim' in eval else None,
            y_lim_bottom=eval[
                'y_lim_bottom'] if 'y_lim_bottom' in eval else None,
            xticks=eval[
                'xticks'] if 'xticks' in eval else None,
            xlabels=eval[
                'xlabels'] if 'xlabels' in eval else None,
            minor_xticks=eval[
                'minor_xticks'] if 'minor_xticks' in eval else None,
            minor_xlabels=eval[
                'minor_xlabels'] if 'minor_xlabels' in eval else None,
        )
