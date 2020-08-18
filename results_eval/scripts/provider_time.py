#!/usr/bin/env python3
"""Bloom Size Plot."""
import os
from typing import List, Union

# noinspection PyUnresolvedReferences
from plot.colors import bar_colors, maroon
# noinspection PyUnresolvedReferences
from plot.plot import (OUTPUT_DIR, INPUT_DIR,
                       read_data, stacked_bar_plot_mult, EXTENSION, Legend,
                       read_ram_max, convert_mib_to_gb, error_plot_mult)
# noinspection PyUnresolvedReferences
from plot.tls import compute_tls_curve

PLOT_ALL = 1
TLS = 1
output_dir_provider = OUTPUT_DIR + "provider/"
os.makedirs(output_dir_provider, exist_ok=True)
input_dir = INPUT_DIR + "provider/"
colors = bar_colors
del colors[1]  # Remove blue
colors[0] = maroon
hatches: List[Union[None, str]] = [None for _ in range(len(colors))]
TLS_INDEX = 2
if TLS:
    ot_tls_color = 'forestgreen'
    colors.insert(TLS_INDEX - 1, ot_tls_color)
    hatches[TLS_INDEX] = '////////'

# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Leave out invisible xticks
#
# phases = (
#     'Parse Input', 'Hash Key R.', 'Hash Set', 'OT Index Comp.',
#     'Key R. (OT)', 'Set Key', 'Encryption', 'Sending')
phases = [
    'Hash Key R.', 'Key R. (OT)', 'Encryption', 'Sending']
if TLS:
    phases.insert(TLS_INDEX, 'OT TLS')
indizes = [4, 6, 9, 11, 12]
x_ind = 2
adjust_bar = None  # (0.1, 0.99, 0.99, 0.15)
adjust_bar2 = None  # (0.075, 0.99, 0.99, 0.15)
adjust_stacked_bar = (0.07, 0.98, 0.94, 0.20)
adjust_stacked_bar2 = (0.09, 0.98, 0.94, 0.20)
ylabel = "Time [s]"
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Random Upload Dependence
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_provider_uploads"
output_dir = output_dir_provider + "rand_uploads/"
os.makedirs(output_dir, exist_ok=True)

# Read Data
input_file = input_dir + name + '.csv'
# Read Data
read_stacks = []
for i in indizes:
    d = read_data(input_file, x_ind, i)
    read_stacks.append(d)
for i in range(len(read_stacks) - 1, 0, -1):
    data = read_stacks[i]
    for matches in data.keys():
        for j, v in enumerate(data[matches]):
            # Subtract prev. time
            data[matches][j] = v - read_stacks[i - 1][matches][j]
if TLS:
    # OT
    sent = read_data(input_file, x_ind, 21)
    recv = read_data(input_file, x_ind, 23)
    base = {}
    for x in read_stacks[TLS_INDEX]:
        base[x] = [0 for _ in range(len(read_stacks[3][x]))]
    tls = compute_tls_curve(base, sent, recv)
    read_stacks.insert(TLS_INDEX + 1, tls)
# -----------------------------------------------------------------------------
# Bar Plot
# if False or PLOT_ALL:
#     output_file = output_dir + f'provider_bar{EXTENSION}'
#     xlabel = "Phase"
#     title = "Provider App - 500 Uploads - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks):
#         if i not in [0]:
#             # Ignore start and non significant stacks
#             data[i] = s[500]  # Only consider 500 matches
#     stacked_bar_plot_mult(output_file, [[data]], xlabel, ylabel, title,
#                           adjust=adjust_bar,
#                           xlabels=phases[:])
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if 0 or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploads [#]"
    title = "Provider App - 1-1000 Uploads - 10 Reps"
    stacks = read_stacks[1:]  # Don't plot start time
    legend_texts = phases[:]
    legend_texts[0] = 'Hash Key Retrieval (R.)'
    stacked_bar_plot_mult(output_file, [stacks], xlabel, ylabel, title,
                          stack_legend=Legend(legend_texts),
                          adjust=adjust_stacked_bar, label_step=1,
                          colors=colors,
                          hatches=hatches,
                          y_lim=62)
# RAM Plot
if 0 or PLOT_ALL:
    output_file = output_dir + f'provider_ram{EXTENSION}'
    xlabel = "Uploads [#]"
    title = "Title"
    d = read_ram_max(
        input_dir + 'butthead_provider_uploads_ram' + '.csv', 2, 4)
    convert_mib_to_gb(d)
    error_plot_mult(
        [d],
        output_file,
        100,
        0,
        35,
        5,
        xlabel,
        "RAM Usage [GB]",
        r"Title",
        auto_ylabels=True,
    )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Random Length Dependence
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_provider_record_length"
output_dir = output_dir_provider + "rand_length/"
os.makedirs(output_dir, exist_ok=True)

# Read Data
input_file = input_dir + name + '.csv'
# Read Data
read_stacks = []
for i in indizes:
    d = read_data(input_file, 3, i)
    read_stacks.append(d)
for i in range(len(read_stacks) - 1, 0, -1):
    data = read_stacks[i]
    for matches in data.keys():
        for j, v in enumerate(data[matches]):
            # Subtract prev. time
            data[matches][j] = v - read_stacks[i - 1][matches][j]
if TLS:
    # OT
    sent = read_data(input_file, 3, 21)
    recv = read_data(input_file, 3, 23)
    base = {}
    for x in read_stacks[TLS_INDEX]:
        base[x] = [0 for _ in range(len(read_stacks[3][x]))]
    tls = compute_tls_curve(base, sent, recv)
    read_stacks.insert(TLS_INDEX + 1, tls)
# -----------------------------------------------------------------------------
# Bar Plot
# if False or PLOT_ALL:
#     output_file = output_dir + f'provider_bar{EXTENSION}'
#     xlabel = "Phase"
#     title = "Provider App - 500 Record Len - 100 Uploads - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks):
#         if i not in [0]:
#             # Ignore start and non significant stacks
#             data[i] = s[500]  # Only consider 500 matches
#     stacked_bar_plot_mult(output_file, [[data]], xlabel, ylabel, title,
#                           adjust=adjust_bar2, xlabels=phases[:])
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Record Length [#]"
    title = "Provider App - 100 Uploads - Length 1-1000 - 10 Reps"
    stacks = read_stacks[1:]  # Don't plot start time
    xticks = list(range(100, 1000, 100)) + [1000]
    xticks = [i if i in xticks else '' for i in range(100, 1001, 100)]
    stacked_bar_plot_mult(output_file, [stacks], xlabel, ylabel, title,
                          stack_legend=Legend(phases[:]),
                          label_step=1, colors=colors, hatches=hatches,
                          adjust=adjust_stacked_bar2, xlabels=xticks,
                          y_lim=15)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Data
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_provider_ikv"
output_dir = output_dir_provider + "ikv/"
os.makedirs(output_dir, exist_ok=True)

# Read Data
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_ikv1 = []
for i in indizes:
    old_d = read_data(input_file, x_ind, i)
    d = {}
    for m in old_d:
        d[m * 100 // 4620] = old_d[m]
    read_stacks_ikv1.append(d)
for i in range(len(read_stacks_ikv1) - 1, 0, -1):
    data = read_stacks_ikv1[i]
    for matches in data.keys():
        for j, v in enumerate(data[matches]):
            # Subtract prev. time
            data[matches][j] = v - read_stacks_ikv1[i - 1][matches][j]
if TLS:
    # OT
    sent = read_data(input_file, x_ind, 21)
    recv = read_data(input_file, x_ind, 23)
    base = {}
    for x in sent:
        base[x] = [0 for _ in range(len(sent[x]))]
    tls = compute_tls_curve(base, sent, recv)
    d = {}
    for m in tls:
        d[m * 100 // 4620] = tls[m]
    read_stacks_ikv1.insert(TLS_INDEX + 1, d)
# -----------------------------------------------------------------------------
# Bar Plot
# if False or PLOT_ALL:
#     output_file = output_dir + f'provider_bar{EXTENSION}'
#     xlabel = "Phase"
#     title = "Provider App - IKV Data - Upload (Ran. Choice from 4620 " \
#             "Records) - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks_ikv1):
#         if i not in [0]:
#             # Ignore start and non significant stacks
#             data[i] = s[100]  # Only consider 500 matches
#     stacked_bar_plot_mult(output_file, [[data]], xlabel, ylabel, title,
#                           adjust=adjust_bar2, xlabels=phases[:])
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if 1 or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    title = "Provider App - IKV Data (4620 Records) - 10 Reps"
    stacks = read_stacks_ikv1[1:]  # Don't plot start time
    stacked_bar_plot_mult(output_file, [stacks], xlabel, ylabel, title,
                          stack_legend=Legend(phases[:]),
                          adjust=None, label_step=1,
                          colors=colors,
                          hatches=hatches, y_lim=15)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Data 2 - Non Random
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_provider_ikv2"
output_dir = output_dir_provider + "ikv2/"
os.makedirs(output_dir, exist_ok=True)

# Read Data
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_ikv2 = []
for i in indizes:
    old_d = read_data(input_file, x_ind, i)
    d = {}
    for m in old_d:
        d[m * 100 // 4620] = old_d[m]
    read_stacks_ikv2.append(d)
for i in range(len(read_stacks_ikv2) - 1, 0, -1):
    data = read_stacks_ikv2[i]
    for matches in data.keys():
        for j, v in enumerate(data[matches]):
            # Subtract prev. time
            data[matches][j] = v - read_stacks_ikv2[i - 1][matches][j]
if TLS:
    # OT
    sent = read_data(input_file, x_ind, 21)
    recv = read_data(input_file, x_ind, 23)
    base = {}
    for x in sent:
        base[x] = [0 for _ in range(len(sent[x]))]
    tls = compute_tls_curve(base, sent, recv)
    d = {}
    for m in tls:
        d[m * 100 // 4620] = tls[m]
    read_stacks_ikv2.insert(TLS_INDEX + 1, d)
# -----------------------------------------------------------------------------
# Bar Plot
# if False or PLOT_ALL:
#     output_file = output_dir + f'provider_bar{EXTENSION}'
#     xlabel = "Phase"
#     title = "Provider App - IKV Data - Upload (Seq. Choice from 4620 " \
#             "Records) - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks_ikv2):
#         if i not in [0]:
#             # Ignore start and non significant stacks
#             data[i] = s[100]  # Only consider 500 matches
#     stacked_bar_plot_mult(output_file, [[data]], xlabel, ylabel, title,
#                           xlabels=phases[:],
#                           adjust=adjust_bar2)
# -----------------------------------------------------------------------------
# Stacked Bar Plot
# if False or PLOT_ALL:
#     output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
#     xlabel = "Uploaded Records [%]"
#     title = "Provider App - IKV Data (4620 Records) - 10 Reps"
#
#     stacks = read_stacks_ikv2[1:]  # Don't plot start time
#     stacked_bar_plot_mult(output_file, [stacks], xlabel, ylabel, title,
#                           stack_legend=Legend(phases[:]),
#                           adjust=adjust_stacked_bar,
#                           label_step=1, colors=colors, hatches=hatches)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Both IKV
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if 0 or PLOT_ALL:
    output_file = output_dir + '../' + f'ikv_stacked{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    title = "Provider App - IKV Data (4620 Records) - Seq. vs Ran. - " \
            "" \
            "10 Reps"

    stacks = read_stacks_ikv2[1:]  # Don't plot start time
    stacked_bar_plot_mult(output_file,
                          [read_stacks_ikv2[1:], read_stacks_ikv1[1:]],
                          xlabel, ylabel, title,
                          stack_legend=Legend(phases[:]),
                          adjust=adjust_stacked_bar2,
                          label_step=1, colors=colors, hatches=hatches,
                          y_lim=14.5)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                WZL Data
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_provider_wzl"
output_dir = output_dir_provider + "wzl/"
os.makedirs(output_dir, exist_ok=True)

# Read Data
input_file = input_dir + name + '.csv'
# Read Data
read_stacks = []
for i in indizes:
    old_d = read_data(input_file, x_ind, i)
    d = {}
    for m in old_d:
        d[m * 100 // 600] = old_d[m]
    read_stacks.append(d)
for i in range(len(read_stacks) - 1, 0, -1):
    data = read_stacks[i]
    for matches in data.keys():
        for j, v in enumerate(data[matches]):
            # Subtract prev. time
            data[matches][j] = v - read_stacks[i - 1][matches][j]
if TLS:
    # OT
    sent = read_data(input_file, x_ind, 21)
    recv = read_data(input_file, x_ind, 23)
    base = {}
    for x in sent:
        base[x] = [0 for _ in range(len(sent[x]))]
    tls = compute_tls_curve(base, sent, recv)
    d = {}
    for m in tls:
        d[m * 100 // 600] = tls[m]
    read_stacks.insert(TLS_INDEX + 1, d)
# -----------------------------------------------------------------------------
# Bar Plot
# if False or PLOT_ALL:
#     output_file = output_dir + f'provider_bar{EXTENSION}'
#     xlabel = "Phase"
#     title = "Provider App - WZL Data - Full Upload (600 Records) - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks):
#         if i not in [0]:
#             # Ignore start and non significant stacks
#             data[i] = s[100]  # Only consider 500 matches
#     # adjust = list(adjust_bar[:])
#     # adjust[0] = 0.085
#     stacked_bar_plot_mult(output_file, [[data]], xlabel, ylabel, title,
#                           adjust=None, xlabels=phases[:])
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    title = "Provider App - WZL Data (600 Records) - 10 Reps"
    stacks = read_stacks[1:]  # Don't plot start time
    stacked_bar_plot_mult(output_file, [stacks], xlabel, ylabel,
                          title,
                          stack_legend=Legend(phases[:]),
                          adjust=adjust_stacked_bar,
                          label_step=1, colors=colors, hatches=hatches,
                          y_lim=30)
