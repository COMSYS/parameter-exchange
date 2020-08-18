#!/usr/bin/env python3
"""Bloom Size Plot."""
import math
import os

from plot.plot import (read_data, INPUT_DIR, OUTPUT_DIR,
                       read_data_mult, stacked_bar_plot, convert_to_gb,
                       stacked_bar_plot_mult)

PLOT_ALL = True
output_dir = OUTPUT_DIR + 'ot_comm/'
os.makedirs(output_dir, exist_ok=True)
input_dir = INPUT_DIR + 'ot/'
to_server = 13
from_server = 15

# Setsize WITHOUT TLS ---------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_setsize"
    d_to = read_data(input_dir + f"setsize/{name}.csv", 2, to_server)
    d_from = read_data(input_dir + f"setsize/{name}.csv", 2, from_server)
    convert_to_gb(d_to)
    convert_to_gb(d_from)
    for x in list(d_to.keys())[:]:
        if x > 10 ** 7:
            del d_to[x]
            del d_from[x]
    xlabels = [
        f"{int(i / 10 ** 6)}M" if i % 10 ** 6 == 0 else fr"$2^{{"
                                                        fr"{int(math.log2(i))}}}$"
        for i in sorted(d_to.keys())]
    xlabels[0] = int(min(sorted(d_to.keys())))
    stacked_bar_plot(
        output_dir + f'{name}.png',
        [d_to, d_from],
        ["Receiver -> Sender", "Sender -> Receiver"],
        "Set Size [#]",
        "Size [GB]",
        "OT Communication Overhead - 10 OT Extensions",
        xlabels=xlabels,
        label_step=1
    )
# TotalOTs WITHOUT TLS --------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_numOTs"
    input_file = input_dir + f"numOTs/{name}.csv"
    d_to = read_data(input_file, 3, to_server)
    d_from = read_data(input_file, 3, from_server)
    convert_to_gb(d_to)
    convert_to_gb(d_from)
    stacked_bar_plot(
        output_dir + f'{name}.png',
        [d_to, d_from],
        ["Receiver -> Sender", "Sender -> Receiver"],
        "Set Size [#]",
        "Size [GB]",
        r"OT Communication Overhead - Set Size $2^{20}$",
        # xticks=xlabels,
        label_step=2

    )
# Latency WITHOUT TLS ---------------------------------------------------------
if False or PLOT_ALL:
    name = "butthead_latency"
    input_file = input_dir + f"latency/{name}.csv"
    data_list_to = read_data_mult(input_file, 3, to_server, 6)
    data_list_from = read_data_mult(input_file, 3, from_server, 6)
    for d in data_list_to.values():
        convert_to_gb(d)
    for d in data_list_from.values():
        convert_to_gb(d)
    latencies = sorted(data_list_to.keys(), reverse=True)
    legend_labels = [f"{i}ms" for i in latencies]
    data = []
    for lat in list(data_list_to.keys()):
        data.append([data_list_to[lat], data_list_from[lat]])
    stacked_bar_plot_mult(
        output_dir + f'{name}.png',
        data,
        ["Receiver -> Sender", "Sender -> Receiver"],
        "Number of OT Extensions [#]",
        "Size [GB]",
        r"OT Communication Overhead - Set Size $2^{20}$",
        # xticks=xlabels,
        label_step=1,
        # legend_pos=None

    )
#
# # Bandwidth WITHOUT TLS
# -------------------------------------------------------
# if False or PLOT_ALL:
#     name = "butthead_bandwidth"
#     data_list = read_data_mult(input_dir + f"bandwidth/{name}.csv", 3, 12, 7)
#     for i in data_list.keys():
#         data_list[i] = convert_to_minutes(data_list[i])
#     latencies = [6000, 50000, 100000, 0]
#     legend_labels = [f"{round(i / 1000)}Mbit/s" for i in latencies if
#                      i is not 0]
#     legend_labels.append("Unlimited")  # 0 has special meaning
#     error_plot_mult(
#         [data_list[i] for i in latencies],
#         output_dir + f'{name}.png',
#         20,
#         0,
#         40,
#         5,
#         "Number of OT Extensions [#]",
#         "Time [min]",
#         r"OT Execution Time with limited BW (SS $2^{20}$, No TLS/MAL)",
#         legend_labels=legend_labels,
#         x_label_step=1,
#         legend_pos=None
#     )
#
# # Async Bandwidth WITHOUT TLS
# -------------------------------------------------
# if False or PLOT_ALL:
#     name = "butthead_ot_bandwidth_async"
#     data_list = read_data_mult(input_dir + f"bandwidth/{name}.csv", 3, 12, 7)
#     for i in data_list.keys():
#         data_list[i] = convert_to_minutes(data_list[i])
#     latencies = [6000, 50000, 100000, 0]
#     legend_labels = [f"{round(i / 1000)}Mbit/s" for i in latencies if
#                      i is not 0]
#     legend_labels.append("Unlimited")  # 0 has special meaning
#     error_plot_mult(
#         [data_list[i] for i in latencies],
#         output_dir + f'{name}.png',
#         20,
#         0,
#         40,
#         5,
#         "Number of OT Extensions [#]",
#         "Time [min]",
#         r"OT Execution Time with limited BW (1:10) (SS $2^{20}$,
#         No TLS/MAL)",
#         legend_labels=legend_labels,
#         x_label_step=1,
#         legend_pos=None
#     )
#
# # Comprasion
# Plot--------------------------------------------------------------
# if True or PLOT_ALL:
#     MEASURED_TLS = False
#     legend = []
#     data_list = []
#
#     if MEASURED_TLS:
#         tls = read_data(input_dir + f"tls/butthead_ot_tls.csv", 3,
#                         12)
#         data_list.append(tls)
#         legend.append("KKRT16 (128Bit) TLS (Meas.)")
#         y_step = 30
#         y_max = 280
#     else:
#         y_step = 10
#         y_max = 40
#
#     malicious = read_data(
#         input_dir + f"malicious/butthead_ot_malicious.csv", 3, 12)
#     data_list.append(malicious)
#     legend.append("OOS16 (76Bit)")
#
#     baseline128 = read_data(
#         input_dir + f"baseline/butthead_ot_baseline128.csv", 3, 12)
#
#     if True:
#         # Theoretic TLS
#         # Read sent Bytes
#         sent = read_data(
#             input_dir + f"baseline/butthead_ot_baseline128.csv", 3, 13)
#         # Read received Bytes
#         received = read_data(
#             input_dir + f"baseline/butthead_ot_baseline128.csv", 3, 15)
#         # Add overhead
#         tls_theoretic = compute_tls_curve(baseline128, sent, received)
#         data_list.append(tls_theoretic)
#         legend.append("KKRT16 (128Bit) TLS (Theo.)")
#
#     data_list.append(baseline128)
#     legend.append("KKRT16 (128Bit)")
#
#     baseline76 = read_data(input_dir +
#     f"baseline/butthead_ot_baseline76.csv",
#                            3,
#                            12)
#     data_list.append(baseline76)
#     legend.append("KKRT16 (76Bit)")
#
#     fmts = ['-' for _ in range(len(data_list))]
#     # Dashed line for theoretic tls + RR 17
#     fmts[1] = '--'
#
#     error_plot_mult(
#         data_list,
#         output_dir + f'ot_comparison.png',
#         20,
#         0,
#         y_max,
#         y_step,
#         "Number of OT Extensions [#]",
#         "Time [s]",
#         r"OT Execution Time for Setsize $2^{20}$ (10 Reps)",
#         x_label_step=1,
#         legend_labels=legend,
#         fmts=fmts
#     )
