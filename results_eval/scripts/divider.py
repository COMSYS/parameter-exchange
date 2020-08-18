#!/usr/bin/env python3
"""Test module to develop divider scripts"""

import os
from typing import List, Union

# noinspection PyUnresolvedReferences
from plot.colors import (maroon, orange, yellow, green, purple, pink, blue,
                         lightblue, bar_colors)
# noinspection PyUnresolvedReferences
from plot.tls import compute_tls_curve

# noinspection PyUnresolvedReferences
from client_time import get_stacks, replace_psi_stacks, replace_bloom_stacks
# noinspection PyUnresolvedReferences
from plot.plot import (bar_plot, OUTPUT_DIR, INPUT_DIR, stacked_bar_plot,
                       read_data, error_plot_mult, stacked_bar_plot_mult,
                       join_stack_data, bar_plot_mult, stacked_bar_plot_two_y,
                       EXTENSION, mean_confidence_interval, Y_LIM, TITLE,
                       make_legend, output, PRINT)

PLOT_ALL = 0
TLS = 1
output_dir_client = OUTPUT_DIR + "client/"
os.makedirs(output_dir_client, exist_ok=True)
input_dir = INPUT_DIR + "client/"
psi_colors = [maroon, orange, yellow, green,
              purple, pink]
bloom_colors = [maroon, blue, lightblue, green, purple, pink]
both_colors = [maroon, orange, yellow, blue, lightblue,
               green, purple, pink]
hatches: List[Union[str, None]] = [None for _ in range(len(both_colors) + 2)]
psi_hatches = hatches[:]
bloom_hatches = hatches[:]
x_index = 5  # Results
indices = [6, 8, 9, 11, 12, 13, 14, 15, 16]
PSI_TLS_IND = 3
OT_TLS_BOTH = 7
OT_TLS_PSI = 5
OT_TLS_BLOOM = 4
if TLS:
    ot_tls_color = 'forestgreen'
    psi_tls_color = 'lightyellow'
    psi_colors.insert(PSI_TLS_IND, psi_tls_color)
    both_colors.insert(PSI_TLS_IND, psi_tls_color)
    psi_colors.insert(OT_TLS_PSI - 1, ot_tls_color)
    bloom_colors.insert(OT_TLS_BLOOM - 1, ot_tls_color)
    both_colors.insert(OT_TLS_BOTH - 1, ot_tls_color)
    psi_hatches[PSI_TLS_IND] = '////////'
    psi_hatches[OT_TLS_PSI] = '////////'
    bloom_hatches[OT_TLS_BLOOM] = '////////'
    hatches[PSI_TLS_IND] = '////////'
    hatches[OT_TLS_BOTH] = '////////'
# -----------------------------------------------------------------------------
bloom_phases = [
    'Hashkey Retr.', 'Bloom Retr.', 'Matching',
    'Key Retr. (OT)', 'Record Retr.', 'Decryption']
psi_phases = [
    'Hashkey Retr.', 'PSI Prep.', 'PSI Exec.',
    'Key Retr. (OT)', 'Record Retr.', 'Decryption']
both_phases = [
    'Hashkey Retr.', 'PSI Prep.', 'PSI Exec.',
    'Bloom Retr.', 'Matching', 'Key Retr. (OT)',
    'Record Retr.', 'Decryption'
]
if TLS:
    bloom_phases.insert(OT_TLS_BLOOM, 'OT TLS')
    psi_phases.insert(PSI_TLS_IND, 'PSI TLS')
    psi_phases.insert(OT_TLS_PSI, 'OT TLS')
    both_phases.insert(PSI_TLS_IND, 'PSI TLS')
    both_phases.insert(OT_TLS_BOTH, 'OT TLS')
ylabel = "Time [s]"

name = "butthead_client_ikv2"
input_file = input_dir + name + '.csv'
read_stacks_ikv2 = get_stacks(input_file)
name = "butthead_client_ikv1"
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_ikv1 = get_stacks(input_file)
output_dir = output_dir_client + 'divided/'
os.makedirs(output_dir, exist_ok=True)
output_file = output_dir + f'ikv_joined_bar{EXTENSION}'
xlabel = "Phase"
title = "Client App - IKV Data - 10 Reps"
data1 = {}
for i, s in enumerate(read_stacks_ikv1):
    if i not in [0, 2, 3, 4]:
        # Ignore start and PSI Stack
        data1[i] = s[77]
data2 = {}
for i, s in enumerate(read_stacks_ikv2):
    if i not in [0, 2, 3, 4]:
        # Ignore start and PSI Stack
        data2[i] = s[77]
