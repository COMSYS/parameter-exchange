#!/usr/bin/env python3
"""Bloom Size Plot."""
import os

# noinspection PyUnresolvedReferences
from plot.colors import blue, orange, green
from plot.plot import (read_data, INPUT_DIR, OUTPUT_DIR,
                       error_plot_mult, read_data_mult, convert_to_minutes,
                       EXTENSION, plot_settings, Legend, read_ram_max,
                       convert_mib_to_gb)
# noinspection PyUnresolvedReferences
from plot.tls import compute_tls_curve

PLOT_ALL = 0
output_dir = OUTPUT_DIR + 'ot/'
os.makedirs(output_dir, exist_ok=True)
input_dir = INPUT_DIR + 'ot/'

# # Setsize WITHOUT TLS ---------------------------------------------------------
# if False or PLOT_ALL:
#     with plot_settings(half_width=True):
#         name = "butthead_setsize"
#         d = read_data(input_dir + f"setsize/{name}.csv", 2, 12)
#         minor_xticks = list(range(10 ** 6, 10 ** 7 + 1, 10 ** 6))
#         xticks = [2 ** i for i in range(20, 24)]
#         xlabels = [fr"$2^{{{i}}}$" for i in range(20, 24)]
#         minor_xlabels = [f"" for i in minor_xticks]
#         # minor_xlabels[4] = "5 Mio"
#         # minor_xlabels[2] = "3 Mio"
#         minor_xlabels[6] = "7 Mio"
#         minor_xlabels[-1] = "10 Mio"
#         for x in list(d.keys())[:]:
#             if x > 10 ** 7:
#                 del d[x]
#         error_plot_mult(
#             [d],
#             output_dir + f'{name}{EXTENSION}',
#             1,
#             0,
#             60,
#             10,
#             "Set Size [#]",
#             "Time [s]",
#             "OT Execution Time for 10 OTs (No TLS/MAL)",
#             adjust=(0.13, 0.93, 0.975, 0.215),
#             x_label_step=1,
#             xlabels=xlabels,
#             xticks=xticks,
#             minor_xticks=minor_xticks,
#             minor_xlabels=minor_xlabels
#         )
# # TotalOTs WITHOUT TLS --------------------------------------------------------
# if False or PLOT_ALL:
#     with plot_settings(half_width=True):
#         name = "butthead_numOTs"
#         d = read_data(input_dir + f"numOTs/{name}.csv", 3, 12)
#         xticks = list(range(0, 200, 30)) + [200]
#         minor_xticks = [i for i in range(0, 200, 10) if i not in xticks]
#         error_plot_mult(
#             [d],
#             output_dir + f'{name}{EXTENSION}',
#             10,
#             0,
#             80,
#             20,
#             "Number of OT Extensions [#]",
#             "Time [s]",
#             r"OT Execution Time for Setsize $2^20$ (No TLS/MAL)",
#             adjust=(0.13, 0.93, 0.975, 0.215),
#             xticks=xticks,
#             minor_xticks=minor_xticks,
#             minor_xlabels=['' for _ in minor_xticks]
#         )
# Latency WITHOUT TLS ---------------------------------------------------------
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        name = "butthead_latency"
        data_list = read_data_mult(input_dir + f"latency/{name}.csv", 3, 12, 6)
        for i in data_list.keys():
            data_list[i] = convert_to_minutes(data_list[i])
        latencies = sorted(data_list.keys(), reverse=True)
        legend_labels = [f"{i}ms" for i in latencies]
        legend_labels[-2] = "  50ms"
        legend_labels[-1] = "    0ms"
        print("Runtime at 300ms: ",
              sum(data_list[300][100]) / len(data_list[300][100]),
              "min")
        error_plot_mult(
            [data_list[i] for i in latencies],
            output_dir + f'{name}{EXTENSION}',
            20,
            0,
            8,
            2,
            "Number of OT Extensions [#]",
            "Time [min]",
            r"OT Execution Time with Latency (SS $2^{20}$, No TLS/MAL)",
            adjust=(0.11, 0.96, 0.76, 0.21),
            # for 2/3 height (0.19, 0.95, 0.98, 0.16)
            legend=Legend(legend_labels, location='above'),
            x_label_step=1,
        )

# Bandwidth WITHOUT TLS -------------------------------------------------------
# if False:
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
#         output_dir + f'{name}_sync{EXTENSION}',
#         20,
#         0,
#         40,
#         5,
#         "Number of OT Extensions [#]",
#         "Time [min]",
#         r"OT Execution Time with limited BW (SS $2^{20}$, No TLS/MAL)",
#         adjust=None,  # (0.17, 0.93, 0.98, 0.14),
#         legend_labels=legend_labels,
#         x_label_step=1,
#         legend_pos=None
#     )

# Async Bandwidth WITHOUT TLS -------------------------------------------------
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        name = "butthead_ot_bandwidth_async"
        data_list = read_data_mult(
            input_dir + f"bandwidth/{name}.csv", 3, 12, 7)
        for i in data_list.keys():
            data_list[i] = convert_to_minutes(data_list[i])
        latencies = [6000, 50000, 100000, 0]
        legend_labels = [
            r"    6Mbit/s",
            r"  50Mbit/s",
            r"100Mbit/s",
            "Unlimited"
        ]
        print("Runtime at 6Mibt/s: ",
              sum(data_list[6000][100]) / len(data_list[6000][100]),
              "min")
        error_plot_mult(
            [data_list[i] for i in latencies],
            output_dir + f'butthead_ot_bandwidth{EXTENSION}',
            20,
            0,
            20,
            5,
            "Number of OT Extensions [#]",
            "Time [min]",
            r"OT Execution Time with limited BW (1:10) (SS $2^{20}$, "
            r"No TLS/MAL)",
            adjust=(0.13, 0.96, 0.76, 0.21),
            # for 2/3 height(0.17, 0.95, 0.98, 0.16),
            legend=Legend(legend_labels, location='above', ncols=2),
            x_label_step=1,
            y_lim=20
        )

# Comprasion Plot--------------------------------------------------------------
if 0 or PLOT_ALL:
    MEASURED_TLS = True
    legend = []
    data_list = []

    if MEASURED_TLS:
        tls = read_data(input_dir + f"tls/butthead_ot_tls.csv", 3,
                        12)
        data_list.append(tls)
        legend.append("KKRT16 (128Bit) TLS (Meas.)")
        y_step = 10  # 30
        y_max = 40  # 280
    else:
        y_step = 10
        y_max = 40

    malicious = read_data(
        input_dir + f"malicious/butthead_ot_malicious.csv", 3, 12)
    data_list.append(malicious)
    legend.append("OOS16  (76Bit)")

    baseline128 = read_data(
        input_dir + f"baseline/butthead_ot_baseline128.csv", 3, 12)

    if True:
        # Theoretic TLS
        # Read sent Bytes
        sent = read_data(
            input_dir + f"baseline/butthead_ot_baseline128.csv", 3, 13)
        # Read received Bytes
        received = read_data(
            input_dir + f"baseline/butthead_ot_baseline128.csv", 3, 15)
        # Add overhead
        tls_theoretic = compute_tls_curve(baseline128, sent, received)
        data_list.append(tls_theoretic)
        legend.append("KKRT16 (128Bit) TLS (Theo.)")

    data_list.append(baseline128)
    legend.append("KKRT16 (128Bit)")

    baseline76 = read_data(input_dir + f"baseline/butthead_ot_baseline76.csv",
                           3,
                           12)
    data_list.append(baseline76)
    legend.append("KKRT16 (76Bit)")

    fmts = ['-' for _ in range(len(data_list))]
    # Dashed line for theoretic tls + RR 17
    fmts[2] = '--'

    error_plot_mult(
        data_list,
        output_dir + f'ot_comparison{EXTENSION}',
        20,
        0,
        y_max,
        y_step,
        "Number of OT Extensions [#]",
        "Time [s]",
        r"OT Execution Time for Set Size $2^{20}$ (10 Reps)",
        adjust=None,  # (0.09, 0.97, 0.98, 0.16),
        x_label_step=1,
        legend=Legend(legend),
        fmts=fmts,
        y_lim=40
    )

# Setsize RAM ---------------------------------------------------------
if 0 or PLOT_ALL:
    with plot_settings(half_width=True):
        name = "butthead_setsize"
        d = read_data(input_dir + f"setsize/butthead_setsize.csv", 2, 12)
        dc = read_ram_max(
            input_dir + f"setsize/butthead_setsize_clientram.csv", 2, 11)
        ds = read_ram_max(
            input_dir + f"setsize/butthead_setsize_serverram.csv", 2, 11)
        convert_mib_to_gb(dc)
        convert_mib_to_gb(ds)
        print("Runtime at 2^20: ",
              sum(d[2 ** 20]) / len(d[2 ** 20]), "s")
        print("Server RAM usage at 2^20: ",
              sum(ds[2 ** 20]) / len(ds[2 ** 20]), "GB")
        minor_xticks = list(range(10 ** 6, 10 ** 7 + 1, 10 ** 6))
        xticks = [2 ** i for i in range(20, 24)]
        xlabels = [fr"$2^{{{i}}}$" for i in range(20, 24)]
        minor_xlabels = [f"" for i in minor_xticks]
        # minor_xlabels[4] = "5 Mio"
        # minor_xlabels[2] = "3 Mio"
        minor_xlabels[6] = "7 Mio"
        minor_xlabels[-1] = "10 Mio"
        for x in list(ds.keys())[:]:
            if x > 10 ** 7:
                del d[x]
                del ds[x]
                del dc[x]
        error_plot_mult(
            [d, dc, ds],
            output_dir + f'{name}{EXTENSION}',
            1,
            0,
            60,
            10,
            "Set Size [#]",
            "Time [s]",
            "OT Execution Time for 10 OTs (No TLS/MAL)",
            adjust=(0.13, 0.88, 0.94, 0.215),
            x_label_step=1,
            xlabels=xlabels,
            xticks=xticks,
            minor_xticks=minor_xticks,
            minor_xlabels=minor_xlabels,
            legend=Legend(['Runtime', 'Client', 'Server'], 'top'),
            auto_ylabels=True,
            second_y_axis=[0, 1, 1],
            second_y_label="RAM Usage [GB]",
            second_ylim=6,
            second_y_lim_bottom=0,
            y_lim=75,
            colors=[blue, orange, green],
        )
# TotalOTs RAM --------------------------------------------------------
if 0 or PLOT_ALL:
    with plot_settings(half_width=True):
        name = "butthead_numOTs"
        d = read_data(input_dir + f"numOTs/butthead_numOTs.csv", 3, 12)
        dc = read_ram_max(input_dir + f"numOTs/butthead_numOTs_clientram.csv",
                          3, 11)
        ds = read_ram_max(input_dir + f"numOTs/butthead_numOTs_serverram.csv",
                          3, 11)
        convert_mib_to_gb(dc)
        convert_mib_to_gb(ds)
        print("Runtime for 200 OTes: ",
              sum(d[200]) / len(d[200]), "s")
        print("Server RAM usage for 200 OTes: ",
              sum(ds[200]) / len(ds[200]), "GB")
        xticks = list(range(0, 200, 30)) + [200]
        minor_xticks = [i for i in range(0, 200, 10) if i not in xticks]
        error_plot_mult(
            [d, dc, ds],
            output_dir + f'{name}{EXTENSION}',
            10,
            0,
            80,
            20,
            "Number of OT Extensions [#]",
            "Time [s]",
            r"OT Execution Time for Set Size $2^20$ (No TLS/MAL)",
            adjust=(0.13, 0.88, 0.94, 0.215),
            xticks=xticks,
            minor_xticks=minor_xticks,
            minor_xlabels=['' for _ in minor_xticks],
            legend=Legend(['Runtime', 'Client', 'Server'], 'top'),
            auto_ylabels=True,
            second_y_axis=[0, 1, 1],
            second_y_label="RAM Usage [GB]",
            second_ylim=6,
            colors=[blue, orange, green],
            second_y_lim_bottom=0,
            y_lim=75,
        )
