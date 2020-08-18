#!/usr/bin/env python3
"""Bloom Size Plot."""
import copy
import os

from plot.colors import *

from plot.plot import (bar_plot, OUTPUT_DIR, INPUT_DIR, stacked_bar_plot,
                       read_data, join_stack_data, bar_plot_mult,
                       stacked_bar_plot_two_y,
                       convert_to_gb, convert_to_mb)

PLOT_ALL = 1
EXTENSION = '.png'
output_dir_client = OUTPUT_DIR + "client_comm/"
os.makedirs(output_dir_client, exist_ok=True)
input_dir = INPUT_DIR + "client/"
values = {
    17: "From KS",
    19: "ToKS",
    21: "FromSS",
    23: "ToSS",
    25: "To OT",
    27: "From OT",
    29: "To PSI",
    31: "From PSI"
}
indizes = sorted(values.keys())
labels = [values[i] for i in indizes]
indizes_wo_psi = [i for i in sorted(values.keys())[:-2]]
labels_wo_psi = [values[i] for i in indizes_wo_psi]

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Random PSI & Bloom
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_psi_vs_bloom"
output_dir = output_dir_client + 'psi_vs_bloom/'
os.makedirs(output_dir, exist_ok=True)
input_file = input_dir + name + '.csv'
# Read Data
read_stacks = []
for i in indizes:
    d = read_data(input_file, 4, i)
    d = convert_to_gb(d)
    read_stacks.append(d)
# -----------------------------------------------------------------------------
# Bar Plot
# --------------------------
# ---------------------------------------------------
# Bar Plot - Butthead Run - Joined
if 0 or PLOT_ALL:
    output_file = output_dir + f'joined_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Full Client App - 500 Matches - Rel. Offset 0.3% - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks):
        data[i] = s[500]  # Only consider 500 matches
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels[:],
             small_xticks=True)
# -----------------------------------------------------------------------------
# Stacked Bar Plot  - Relative Offset 2 - Butthead - Bloom
if 0 or PLOT_ALL:
    output_file = output_dir + f'client_stacked_bloom_butthead{EXTENSION}'
    xlabel = "Matches [#]"
    ylabel = "Size [GB]"
    title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
    stacks = read_stacks[:-2]
    stacked_bar_plot(output_file, stacks, labels_wo_psi[:], xlabel,
                     ylabel, title, label_step=1)
# -----------------------------------------------------------------------------
# Both
# -----------------------------------------------------------------------------
if 0 or PLOT_ALL:
    output_file = output_dir + f'client_stacked_butthead{EXTENSION}'
    xlabel = "Matches [#]"
    ylabel = "Size [GB]"
    title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
    stacks = read_stacks[:]
    stacked_bar_plot(output_file, stacks, labels[:], xlabel, ylabel,
                     title, label_step=1)

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                WZL Client 1
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_wzl1"
num_matches = 10
output_dir = output_dir_client + 'wzl/'
os.makedirs(output_dir, exist_ok=True)
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_wzl1 = []
for i in indizes:
    d = read_data(input_file, 5, i)
    d = convert_to_mb(d)
    read_stacks_wzl1.append(d)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                WZL Client 2
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_wzl2"
num_matches = 6
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_wzl2 = []
for i in indizes:
    d = read_data(input_file, 5, i)
    d = convert_to_mb(d)
    read_stacks_wzl2.append(d)
# -----------------------------------------------------------------------------
# Same for Joined
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Joined
if 0 or PLOT_ALL:
    output_file = output_dir + f'wzl_joined_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [MB]"
    title = "Client App - WZL Data - 10 Reps"
    data1 = {}
    for i, s in enumerate(read_stacks_wzl1):
        data1[i] = s[10]  # Only consider 500 matches
    data2 = {}
    for i, s in enumerate(read_stacks_wzl2):
        data2[i] = s[6]  # Only consider 500 matches
    bar_plot_mult(output_file, [data1, data2], xlabel, ylabel, title,
                  ['WZL1', 'WZL2'],
                  xticks=labels[:],
                  small_xticks=True,
                  )
# -----------------------------------------------------------------------------
# Both Both
# -----------------------------------------------------------------------------
if 0 or PLOT_ALL:
    output_file = output_dir + f'client_wzl{EXTENSION}'
    xlabel = "Metric"
    ylabel = "Size [MB]"
    title = "Full Client App - WZL Data - 10 Reps"
    stacks = join_stack_data([read_stacks_wzl1, read_stacks_wzl2],
                             [['WZL1'], ['WZL2']])
    stacked_bar_plot(output_file, stacks, labels[:],
                     xlabel, ylabel, title,
                     label_step=1)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Client 1 - Rounding: 2, rel. Offset 2%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_ikv1"
num_matches = 77
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_ikv1 = []
for i in indizes_wo_psi:
    d = read_data(input_file, 5, i)
    d = convert_to_mb(d)
    read_stacks_ikv1.append(d)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Client 2 - Rounding: 2, rel. Offset 2.5%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_ikv2"
num_matches = 77
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_ikv2 = []
for i in indizes_wo_psi:
    d = read_data(input_file, 5, i)
    d = convert_to_mb(d)
    read_stacks_ikv2.append(d)
# -----------------------------------------------------------------------------
# Both Both
# -----------------------------------------------------------------------------
if 1 or PLOT_ALL:
    output_dir = output_dir_client + 'ikv/'
    os.makedirs(output_dir, exist_ok=True)
    output_file = output_dir + f'client_ikv{EXTENSION}'
    xlabel = "Metric"
    ylabel = "Size [MB]"
    title = "Client App - IKV Data - rel. Offset - 10 Reps"
    stacks1 = copy.deepcopy(read_stacks_ikv1)
    stacks2 = copy.deepcopy(read_stacks_ikv2)
    stacked_bar_plot_two_y(output_file, [stacks1, stacks2], labels_wo_psi[:],
                           xlabel, ylabel, title,
                           label_step=1, )
# -----------------------------------------------------------------------------
# Same for Joined
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Joined
if 0 or PLOT_ALL:
    output_dir = output_dir_client + 'ikv/'
    os.makedirs(output_dir, exist_ok=True)
    output_file = output_dir + f'ikv_joined_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [MB]"
    title = "Client App - IKV Data - 10 Reps"
    data1 = {}
    for i, s in enumerate(read_stacks_ikv1):
        data1[i] = s[77]
    data2 = {}
    for i, s in enumerate(read_stacks_ikv2):
        data2[i] = s[77]
    bar_plot_mult(output_file, [data1, data2], xlabel, ylabel, title,
                  legend=['IKV1', 'IKV2'],
                  xticks=labels_wo_psi[:],
                  small_xticks=True,
                  second_y_axis=False)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Random Client 2 - Rounding: 3, ID Len 10, rel. Offset 0.5%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_bloom"
num_matches = 500
output_dir = output_dir_client + 'bloom/'
os.makedirs(output_dir, exist_ok=True)
input_file = input_dir + name + '.csv'
# Read Data
read_stacks = []
for i in indizes_wo_psi:
    d = read_data(input_file, 5, i)
    d = convert_to_gb(d)
    read_stacks.append(d)
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Bloom
if False or PLOT_ALL:
    output_file = output_dir + f'client_bar_bloom{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Full Client App - 500 Matches - Rel. Offset 0.5% - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks):
        data[i] = s[num_matches]  # Only consider one number of matches
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels_wo_psi[:],
             small_xticks=True)
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'client_stacked_bloom{EXTENSION}'
    xlabel = "Results [#]"
    ylabel = "Size [GB]"
    title = "Full Client App - ID Len. 10 - Rel. Offset 0.5% - 10 Reps"
    stacks = copy.deepcopy(read_stacks)
    stacked_bar_plot(output_file, stacks, labels_wo_psi[:], xlabel, ylabel,
                     title,
                     label_step=1)
