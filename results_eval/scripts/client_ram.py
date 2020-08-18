#!/usr/bin/env python3
"""Bloom Size Plot."""
import os

from plot.plot import (OUTPUT_DIR, INPUT_DIR,
                       read_y_only, read_data, read_ram,
                       mean_confidence_interval, error_plot_mult, )


PLOT_ALL = 1
output_dir = OUTPUT_DIR + "client/"
os.makedirs(output_dir, exist_ok=True)
input_dir = INPUT_DIR + "client/"
# Preserver--------------------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_bloom"
    ram_file = input_dir + name + '_ram.csv'
    input_file = input_dir + name + '.csv'
    output_file = output_dir + 'client_ram' + '.png'
    # Read Data
    # Only consider last line, because each ram measurement is different
    data, max_y = read_ram(ram_file, start_line=5, end_line=6)
    # convert to GiB
    for key in data:
        data[key] = [i / (2 ** 10) for i in data[key]]

    times = []
    for i in range(6, 17):
        times.append(read_y_only(input_file, i, start_line=5, end_line=6))
    means = []
    for t in times:
        m, h = mean_confidence_interval(t)
        means.append(m)
    start_time = means[0]
    xticks = []
    for m in means[1:]:
        xticks.append(m - start_time)

    # Configuration
    xlabel = "Phase"
    ylabel = "RAM Usage [GiB]"
    title = "RAM Client App - 1000 Matches - Rel. Offset 0.3%"
    x_labels = [
        'Candidates', 'Hash Key', 'PSI Prep.', 'PSI Exec.', 'PSI Final',
        'Bloom Retr.', 'Matching', 'Key Retr. (OT)', 'Record Retr.', 'Decryption']
    # x_labels = [
    # 'Hash Key R.', 'PSI Prep.', 'PSI Exec.',
    # 'Key R. (OT)', 'Record R.', 'Decryption']

    print("Length of RAM measurement: ", max(data.keys()), 's')
    print("Length of Time measurement: ", xticks[-1], 's')

    # Fit lengths
    # new_data = {}
    # step = xticks[-1] / len(data.keys())
    # for i, key in enumerate(sorted(data.keys())):
    #     new_data[(i + 1) * step] = data[key]
    # data = new_data
    for i in range(len(xticks[:]) - 1, -1, -1):
        if xticks[i] < 0:
            del xticks[i]
            del x_labels[i]
    xstep = 0.5
    min_y = 0
    max_y = 20
    y_step = 5
    print(xticks, x_labels)
    error_plot_mult([data], output_file, xstep, min_y, max_y, y_step, xlabel, ylabel,
                    title, xticks=xticks, xlabels=x_labels,
                    ver_grid=True, x_rotation=90, auto_ylabels=True)
