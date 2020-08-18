#!/usr/bin/env python3
"""Bloom Size Plot."""
import os

from plot.colors import bar_colors

from plot.plot import (bar_plot, OUTPUT_DIR, INPUT_DIR, stacked_bar_plot,
                       read_data, stacked_bar_plot_mult, convert_to_gb)

PLOT_ALL = 1
EXTENSION = '.png'
output_dir_provider = OUTPUT_DIR + "provider_comm/"
os.makedirs(output_dir_provider, exist_ok=True)
input_dir = INPUT_DIR + "provider/"
colors = bar_colors
values = {
    13: "From KS",
    15: "ToKS",
    17: "FromSS",
    19: "ToSS",
    21: "To OT",
    23: "From OT",
}
indizes = sorted(values.keys())
labels = [values[i] for i in indizes]
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
x_ind = 2
# Read Data
read_stacks = []
for i in indizes:
    d = read_data(input_file, x_ind, i)
    d = convert_to_gb(d)
    read_stacks.append(d)
# -----------------------------------------------------------------------------
# Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Provider App - 500 Uploads - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks):
        data[i] = s[500]  # Only consider 500 matches
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels[:],
             small_xticks=True)

# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploads [#]"
    ylabel = "Size [GB]"
    title = "Provider App - 1-1000 Uploads - 10 Reps"
    stacks = read_stacks
    stacked_bar_plot(output_file, stacks, labels[:], xlabel, ylabel, title,
                     label_step=1, colors=colors)
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
x_ind = 3
# Read Data
read_stacks = []
for i in indizes:
    d = read_data(input_file, x_ind, i)
    d = convert_to_gb(d)
    read_stacks.append(d)
# -----------------------------------------------------------------------------
# Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Provider App - 500 Record Len - 100 Uploads - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks):
        data[i] = s[500]  # Only consider 500 matches
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels[:],
             small_xticks=True)
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploads [#]"
    ylabel = "Size [GB]"
    title = "Provider App - 100 Uploads - Length 1-1000 - 10 Reps"

    stacks = read_stacks
    xticks = list(range(100, 1000, 100)) + [1000]
    xticks = [i if i in xticks else '' for i in range(100, 1001, 100)]
    stacked_bar_plot(output_file, stacks, labels[:], xlabel, ylabel, title,
                     label_step=1, colors=colors,
                     xticks=xticks)
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
x_ind = 2
# Read Data
read_stacks_ikv1 = []
for i in indizes:
    old_d = read_data(input_file, x_ind, i)
    d = {}
    for m in old_d:
        d[m * 100 // 4620] = old_d[m]
    d = convert_to_gb(d)
    read_stacks_ikv1.append(d)
# -----------------------------------------------------------------------------
# Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Provider App - IKV Data - Upload (Ran. Choice from 4620 " \
            "Records) - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks_ikv1):
        data[i] = s[100]  # Only consider 500 matches
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels[:],
             small_xticks=True)

# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    ylabel = "Size [GB]"
    title = "Provider App - IKV Data (4620 Records) - 10 Reps"
    stacks = read_stacks_ikv1  # Don't plot start time
    stacked_bar_plot(output_file, stacks, labels[:], xlabel, ylabel, title,
                     label_step=1, colors=colors)
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
x_ind = 2
# Read Data
read_stacks_ikv2 = []
for i in indizes:
    old_d = read_data(input_file, x_ind, i)
    d = {}
    for m in old_d:
        d[m * 100 // 4620] = old_d[m]
    d = convert_to_gb(d)
    read_stacks_ikv2.append(d)
# -----------------------------------------------------------------------------
# Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Provider App - IKV Data - Upload (Seq. Choice from 4620 " \
            "Records) - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks_ikv2):
        data[i] = s[100]  # Only consider 500 matches
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels[:],
             small_xticks=True)
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    ylabel = "Size [GB]"
    title = "Provider App - IKV Data (4620 Records) - 10 Reps"
    stacks = read_stacks_ikv2  # Don't plot start time
    stacked_bar_plot(output_file, stacks, labels[:], xlabel, ylabel, title,
                     label_step=1, colors=colors)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Both IKV
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
if 1 or PLOT_ALL:
    output_file = output_dir + f'../' + f'ikv_stacked{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    ylabel = "Size [GB]"
    title = "Provider App - IKV Data (4620 Records) - Seq. vs Ran. - 10 Reps"
    stacks = read_stacks_ikv2
    stacked_bar_plot_mult(output_file,
                          [read_stacks_ikv2, read_stacks_ikv1], labels[:],
                          xlabel, ylabel, title,
                          label_step=1, colors=colors)
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
x_ind = 2
# Read Data
read_stacks = []
for i in indizes:
    old_d = read_data(input_file, x_ind, i)
    d = {}
    for m in old_d:
        d[m * 100 // 600] = old_d[m]
    d = convert_to_gb(d)
    read_stacks.append(d)
# -----------------------------------------------------------------------------
# Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_bar{EXTENSION}'
    xlabel = "Phase"
    ylabel = "Size [GB]"
    title = "Provider App - WZL Data - Full Upload (600 Records) - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks):
        data[i] = s[100]
    bar_plot(output_file, data, xlabel, ylabel, title, xticks=labels[:],
             small_xticks=True)
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'provider_stacked_bar{EXTENSION}'
    xlabel = "Uploaded Records [%]"
    ylabel = "Size [GB]"
    title = "Provider App - WZL Data (600 Records) - 10 Reps"
    stacks = read_stacks[:]
    stacked_bar_plot(output_file, stacks, labels[:], xlabel, ylabel, title,
                     label_step=1, colors=colors)
