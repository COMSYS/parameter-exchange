#!/usr/bin/env python3
"""Ram Plot of Provider Eval."""
from plot.plot import (OUTPUT_DIR, INPUT_DIR,
                       read_y_only, read_ram,
                       mean_confidence_interval, error_plot_mult)


PLOT_ALL = True
output_dir = OUTPUT_DIR + "provider/"
input_dir = INPUT_DIR + "provider/"
# Offset 2---------------------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_provider_uploads"
    ram_file = input_dir + name + '_ram.csv'
    input_file = input_dir + name + '.csv'
    output_file = output_dir + 'provider_ram' + '.png'
    # Read Data
    # Only consider last line, because each ram measurement is different
    data, max_y = read_ram(ram_file, start_line=-1, y=4)

    times = []
    for i in range(4, 13):
        times.append(read_y_only(input_file, i, start_line=-6, end_line=-5))
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
    ylabel = "RAM Usage [MiB]"
    title = "RAM Provider App - 500 Uplodads"
    # x_labels = (
    #     'Parse Input', 'Hash Key Retr.', 'Hash Set', 'OT Index Comp.',
    #     'Key Retr. (OT)', 'Set Key', 'Encryption', 'Sending')
    x_labels = [
        '', 'Hash Key Retr.', '', '',
        'Key Retr. (OT)', '', ' ', 'Sending']

    print("Length of RAM measurement: ", max(data.keys()), 's')
    print("Length of Time measurement: ", xticks[-1], 's')

    xstep = 0.5
    min_y = 0
    max_y = 20000
    y_step = 5000
    for key, value in sorted(dict(zip(xticks, x_labels)).items(), key=lambda x: x[0]):
        print("{} : {}".format(key, value))
    error_plot_mult([data], output_file, xstep, min_y, max_y, y_step, xlabel, ylabel,
                    title, xticks=xticks, xlabels=x_labels,
                    ver_grid=True, x_rotation=90, auto_ylabels=True)
