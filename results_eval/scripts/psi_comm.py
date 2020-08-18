#!/usr/bin/env python3
"""Bloom Size Plot."""
import math
import os

from plot.plot import (read_data, INPUT_DIR, OUTPUT_DIR,
                       read_data_mult, convert_to_gb, stacked_bar_plot,
                       stacked_bar_plot_mult)

PLOT_ALL = True
output_dir = OUTPUT_DIR + 'psi_comm/'
os.makedirs(output_dir, exist_ok=True)
input_dir = INPUT_DIR + 'psi/'
to_server = 11
from_server = 13

# Setsize ---------------------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_psi_setsize"
    input_file = input_dir + f"setsize/{name}2.csv"
    d_to = read_data(input_file, 2, to_server)
    d_from = read_data(input_file, 2, from_server)
    convert_to_gb(d_to)
    convert_to_gb(d_from)
    minor_xlabels = [f"{int(i / 10 ** 6)} Mio" for i in sorted(d_to.keys()) if
                     i % 10 ** 6 == 0]
    for i in [3, 5, 7, 9, 11, 13, 15, 17, 19]:
        minor_xlabels[i] = ''
    xticks = [i for i, x in enumerate(sorted((d_to.keys()))) if
              x != 0 and x % 10 ** 6 != 0]
    minor_xticks = [i for i, _ in enumerate(sorted((d_to.keys()))) if
                    i not in xticks]
    xlabels = [fr"$2^{{ {i} }}$" for i in range(20, 26, 1)]
    stacked_bar_plot(
        output_dir + f'{name}.png',
        [d_to, d_from],
        ["Receiver -> Sender", "Sender -> Receiver"],
        "Set Size [#]",
        "Size [GB]",
        "PSI Communication Overhead (No TLS/MAL)",
        xlabels=xlabels,
        xticks=xticks,
        minor_xticks=minor_xticks,
        minor_xlabels=minor_xlabels,
        label_step=1
    )
# Latency WITHOUT TLS ---------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_psi_latency"
    input_file = input_dir + f"latency/{name}.csv"
    data_list_to = read_data_mult(input_file, 2, to_server, 7)
    data_list_from = read_data_mult(input_file, 2, from_server, 7)
    for d in data_list_to.values():
        convert_to_gb(d)
    for d in data_list_from.values():
        convert_to_gb(d)
    latencies = sorted(data_list_to.keys(), reverse=True)
    legend_labels = [f"{i}ms" for i in latencies]
    data = []
    for lat in list(data_list_to.keys()):
        data.append([data_list_to[lat], data_list_from[lat]])
    xlabels = [f"{i // 1000000}M" if not math.log2(
        i).is_integer() else fr"$2^{{{int(math.log2(i))}}}$" for i in
               sorted(list(data_list_to.values())[0])]
    stacked_bar_plot_mult(
        output_dir + f'{name}.png',
        data,
        ["Receiver -> Sender", "Sender -> Receiver"],
        "Set Size [#]",
        "Size [GB]",
        r"PSI Communication Overhead (No TLS/MAL)",
        xticks=xlabels,
        label_step=1,
        # legend_pos=None

    )
# # Bandwidth WITHOUT TLS
# -------------------------------------------------------
# if False or PLOT_ALL:
#     name = "butthead_psi_bandwidth"
#     data_list = read_data_mult(input_dir + f"bandwidth/{name}.csv", 2, 10, 8)
#     bws = sorted(data_list.keys())[1:]
#     legend_labels = [f"{round(i / 1000)} Mbit/s" for i in bws]
#     bws.append(0)
#     legend_labels.append('Unlimited')
#     for data in data_list.values():
#         convert_to_minutes(data)
#     xticks = list(range(0, 10 ** 6 + 1, 10 ** 5))
#     error_plot_mult(
#         [data_list[i] for i in bws],
#         output_dir + f'{name}.png',
#         100000,
#         0,
#         20,
#         5,
#         "PSI Setsize  [#]",
#         "Time [min]",
#         "PSI Execution Time w/ restricted Bandwidth [1:10] (No TLS/MAL)",
#         legend_labels=legend_labels,
#         x_label_step=2,
#         legend_pos=None,
#         xticks=xticks,
#         x_labels=[0] + [f"{i / 10 ** 6:1} Mio" for i in xticks[1:]]
#     )
# # Comparison Plot
# -------------------------------------------------------------
# if True or PLOT_ALL:
#     MEASURED_TLS = True
#     legend = []
#     data_list = []
#     fmts = ['-' for _ in range(4)]
#     # Dashed line for theoretic tls + RR 17
#     fmts[1], fmts[2] = '--', '--'
#
#     baseline = read_data(input_dir +
#     f"baseline/butthead_psi_baseline.csv", 2,
#                          10)
#
#     malicious = read_data(input_dir + f"malicious/butthead_psi_rr16.csv",
#                           2,
#                           10)
#     data_list.append(malicious)
#     legend.append("RR16")
#
#     if MEASURED_TLS:
#         tls = read_data(input_dir + f"tls/butthead_psi_tls.csv", 2,
#                         10)
#         data_list.append(tls)
#         legend.append("KKRT16 TLS (Meas./Broken)")
#         y_step = 10
#         y_max = 60
#         fmts.insert(1, ':')
#     else:
#         y_step = 10
#         y_max = 60
#
#     malicious = read_data(input_dir + f"malicious/butthead_psi_rr17.csv",
#                           2,
#                           10)
#     data_list.append(malicious)
#     legend.append("RR17 (Broken)")
#
#     THEO_TLS = True
#     if THEO_TLS:
#         # Read sent Bytes
#         sent = read_data(
#             input_dir + f"baseline/butthead_psi_baseline.csv", 2, 11)
#         # Read received Bytes
#         received = read_data(
#             input_dir + f"baseline/butthead_psi_baseline.csv", 2, 13)
#         # Add overhead
#         tls_theoretic = compute_tls_curve(baseline, sent, received)
#         data_list.append(tls_theoretic)
#         legend.append("KKRT16 TLS (Theo.)")
#
#     data_list.append(baseline)
#     legend.append("KKRT16")
#
#     error_plot_mult(
#         data_list,
#         output_dir + f'psi_compare.png',
#         100000,
#         0,
#         y_max,
#         y_step,
#         "PSI Set Size [#]",
#         "Time [s]",
#         "PSI Execution Time (10 Reps)",
#         legend_labels=legend,
#         x_label_step=2,
#         legend_pos=None,
#         x_labels=[f"{round(i):,}" for i in range(100000, 1000001, 100000)],
#         xticks=range(100000, 1000001, 100000),
#         fmts=fmts
#     )
