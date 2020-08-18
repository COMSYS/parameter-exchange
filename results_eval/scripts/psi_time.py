#!/usr/bin/env python3
"""Bloom Size Plot."""
import os

# noinspection PyUnresolvedReferences
from plot.colors import green, orange, blue
from plot.plot import (read_data, INPUT_DIR, OUTPUT_DIR,
                       read_data_mult, error_plot_mult, convert_to_minutes,
                       EXTENSION, plot_settings, Legend, read_ram_max,
                       convert_to_gb, convert_mib_to_gb)
# noinspection PyUnresolvedReferences
from plot.tls import compute_tls_curve

PLOT_ALL = 0
output_dir = OUTPUT_DIR + 'psi/'
os.makedirs(output_dir, exist_ok=True)
input_dir = INPUT_DIR + 'psi/'

# Setsize ---------------------------------------------------------------------
# if False or PLOT_ALL:
#     name = "butthead_psi_setsize"
#     d = read_data(input_dir + f"setsize/{name}2.csv", 2, 10)
#     minor_xticks = list(range(10 ** 6, 2 * 10 ** 7 + 1, 10 ** 6))
#     xticks = [2 ** i for i in range(20, 25)]
#     minor_xlabels = [f"" for i in minor_xticks]
#     minor_xlabels[5] = "6 Mio"
#     minor_xlabels[9] = "10 Mio"
#     minor_xlabels[14] = "15 Mio"
#     minor_xlabels[-1] = "20 Mio"
#     xlabels = [rf"$2^{{{i}}}$" for i in range(20, 25)]
#     error_plot_mult(
#         [d],
#         output_dir + f'{name}{EXTENSION}',
#         1,
#         0,
#         80,
#         10,
#         "PSI Set Size [#]",
#         "Time [s]",
#         "PSI Execution Time (No TLS/MAL)",
#         adjust=None,  # (0.09, 0.96, 0.98, 0.18),
#         xlabels=xlabels,
#         xticks=xticks,
#         minor_xticks=minor_xticks,
#         minor_xlabels=minor_xlabels,
#         # x_rotation=30
#     )
# Latency WITHOUT TLS ---------------------------------------------------------
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        name = "butthead_psi_latency"
        data_list = read_data_mult(input_dir + f"latency/{name}.csv", 2, 10, 7)
        for d in data_list.values():
            # Remove 2er potencies
            del d[2 ** 20]
            del d[2 ** 21]
            del d[2 ** 22]
            del d[2 ** 23]
            del d[2 ** 24]
            convert_to_minutes(d)
        print("Runtime at 300ms: ",
              sum(data_list[300][10 ** 7]) / len(data_list[300][10 ** 7]),
              "min")
        latencies = sorted(data_list.keys(), reverse=True)
        legend_labels = [f"{i}ms" for i in latencies]
        legend_labels[-2] = "  50ms"
        legend_labels[-1] = "    0ms"
        xticks = list(range(0, 10 ** 7 + 1, 2 * 10 ** 6))
        error_plot_mult(
            [data_list[i] for i in latencies],
            output_dir + f'{name}{EXTENSION}',
            2 * 10 ** 6,
            0,
            5,
            1,
            "PSI Set Size [#]",
            "Time [min]",
            "PSI Execution Time w/ Latency(No TLS/MAL)",
            adjust=(0.11, 0.935, 0.76, 0.21),
            # for 2/3  Height (0.19, 0.93, 0.98, 0.16),
            legend=Legend(legend_labels, location='above'),
            x_label_step=1,
            y_lim=5,
            xticks=xticks,
            xlabels=[0] + [f"{i // 10 ** 6} Mio" for i in xticks[1:]]
        )
# Bandwidth WITHOUT TLS -------------------------------------------------------
if False or PLOT_ALL:
    with plot_settings(half_width=True):
        name = "butthead_psi_bandwidth"
        data_list = read_data_mult(
            input_dir + f"bandwidth/{name}.csv", 2, 10, 8)
        bws = sorted(data_list.keys())[1:]
        bws.append(0)
        legend_labels = [
            r"    6Mbit/s",
            r"  50Mbit/s",
            r"100Mbit/s",
            "Unlimited"
        ]
        for data in data_list.values():
            convert_to_minutes(data)
        print("Runtime at 6Mibt/s: ",
              sum(data_list[6000][10**6]) / len(data_list[6000][10**6]), "min")
        xticks = list(range(0, 10 ** 6 + 1, 10 ** 5))
        error_plot_mult(
            [data_list[i] for i in bws],
            output_dir + f'{name}{EXTENSION}',
            100000,
            0,
            5,
            1,
            "PSI Set Size [#]",
            "Time [min]",
            "PSI Execution Time w/ restricted Bandwidth [1:10] (No TLS/MAL)",
            adjust=(0.11, 0.93, 0.76, 0.21),
            # for 2/3 height (0.15, 0.93, 0.98, 0.16),
            legend=Legend(legend_labels, location='above', ncols=2),
            x_label_step=2,
            xticks=xticks,
            xlabels=[0] + [f"{i / 10 ** 6:1} Mio" for i in xticks[1:]],
            y_lim=5
        )
# Comparison Plot -------------------------------------------------------------
if 0 or PLOT_ALL:
    MEASURED_TLS = True
    legend = []
    data_list = []
    fmts = ['-' for _ in range(4)]
    # Dotted line for RR 17
    fmts[1] = ':'
    # Dashed for TLS theo
    fmts[2] = '--'

    baseline = read_data(input_dir + f"baseline/butthead_psi_baseline.csv", 2,
                         10)

    malicious = read_data(input_dir + f"malicious/butthead_psi_rr16.csv",
                          2,
                          10)
    data_list.append(malicious)
    legend.append("RR16")

    if MEASURED_TLS:
        tls = read_data(input_dir + f"tls/butthead_psi_tls.csv", 2,
                        10)
        data_list.append(tls)
        legend.append("KKRT16 TLS (Meas.)")
        y_step = 10
        y_max = 60
        fmts.insert(1, '-')
    else:
        y_step = 10
        y_max = 60

    malicious = read_data(input_dir + f"malicious/butthead_psi_rr17.csv",
                          2,
                          10)
    data_list.append(malicious)
    legend.append("RR17 (Broken)")

    THEO_TLS = True
    if THEO_TLS:
        # Read sent Bytes
        sent = read_data(
            input_dir + f"baseline/butthead_psi_baseline.csv", 2, 11)
        # Read received Bytes
        received = read_data(
            input_dir + f"baseline/butthead_psi_baseline.csv", 2, 13)
        # Add overhead
        tls_theoretic = compute_tls_curve(baseline, sent, received)
        data_list.append(tls_theoretic)
        legend.append("KKRT16 TLS (Theo.)")

    data_list.append(baseline)
    legend.append("KKRT16")

    error_plot_mult(
        data_list,
        output_dir + f'psi_compare{EXTENSION}',
        100000,
        0,
        y_max,
        y_step,
        "PSI Set Size [#]",
        "Time [s]",
        "PSI Execution Time (10 Reps)",
        adjust=None,  # (0.09, 0.97, 0.98, 0.16),
        legend=Legend(legend),
        x_label_step=2,
        xlabels=[f"{round(i):,}" for i in range(100000, 1000001, 100000)],
        xticks=list(range(100000, 1000001, 100000)),
        fmts=fmts,
        auto_ylabels=True,
    )
# # Set Size ---------------------------------------------------------------------
# if False or PLOT_ALL:
#     name = "butthead_psi_setsize_ram"
#     dc = read_ram_max(
#         input_dir + f"setsize/butthead_psi_setsize2_clientram.csv", 2, 9)
#     ds = read_ram_max(
#         input_dir + f"setsize/butthead_psi_setsize2_serverram.csv", 2, 9)
#     convert_mib_to_gb(dc)
#     convert_mib_to_gb(ds)
#     minor_xticks = list(range(10 ** 6, 2 * 10 ** 7 + 1, 10 ** 6))
#     xticks = [2 ** i for i in range(20, 25)]
#     minor_xlabels = [f"" for i in minor_xticks]
#     minor_xlabels[5] = "6 Mio"
#     minor_xlabels[9] = "10 Mio"
#     minor_xlabels[14] = "15 Mio"
#     minor_xlabels[-1] = "20 Mio"
#     xlabels = [rf"$2^{{{i}}}$" for i in range(20, 25)]
#     error_plot_mult(
#         [dc, ds],
#         output_dir + f'{name}{EXTENSION}',
#         1,
#         0,
#         80,
#         10,
#         "PSI Set Size [#]",
#         "RAM Usage [GB]",
#         "PSI Execution Time (No TLS/MAL)",
#         adjust=None,  # (0.09, 0.96, 0.98, 0.18),
#         xlabels=xlabels,
#         xticks=xticks,
#         minor_xticks=minor_xticks,
#         minor_xlabels=minor_xlabels,
#         legend=Legend(['Client', 'Server'], 'top'),
#         auto_ylabels=True
#         # x_rotation=30
#     )

# Setsize RAM + Normal---------------------------------------------------------
if 0 or PLOT_ALL:
    name = "butthead_psi_setsize"
    d = read_data(input_dir + f"setsize/{name}2.csv", 2, 10)
    dc = read_ram_max(
        input_dir + f"setsize/butthead_psi_setsize2_clientram.csv", 2, 9)
    ds = read_ram_max(
        input_dir + f"setsize/butthead_psi_setsize2_serverram.csv", 2, 9)
    convert_mib_to_gb(dc)
    convert_mib_to_gb(ds)
    print("Runtime at 2^20: ",
          sum(d[2 ** 20]) / len(d[2 ** 20]), "s")
    print("Server RAM usage at 2^20: ",
          sum(ds[2 ** 20]) / len(ds[2 ** 20]), "GB")
    print("Runtime at 20Mio: ",
          sum(d[2 * 10 ** 7]) / len(d[2 * 10 ** 7]), "s")
    print("Server RAM usage at 20Mio: ",
          sum(ds[2 * 10 ** 7]) / len(ds[2 * 10 ** 7]), "GB")
    minor_xticks = list(range(10 ** 6, 2 * 10 ** 7 + 1, 10 ** 6))
    xticks = [2 ** i for i in range(20, 25)]
    minor_xlabels = [f"" for i in minor_xticks]
    minor_xlabels[5] = "6 Mio"
    minor_xlabels[9] = "10 Mio"
    minor_xlabels[14] = "15 Mio"
    minor_xlabels[-1] = "20 Mio"
    xlabels = [rf"$2^{{{i}}}$" for i in range(20, 25)]
    error_plot_mult(
        [d, dc, ds],
        output_dir + f'psi_setsize{EXTENSION}',
        1,
        0,
        80,
        10,
        "PSI Set Size [#]",
        "Time [s]",
        "PSI Execution Time (No TLS/MAL)",
        adjust=None,  # (0.09, 0.96, 0.98, 0.18),
        xlabels=xlabels,
        xticks=xticks,
        minor_xticks=minor_xticks,
        minor_xlabels=minor_xlabels,
        legend=Legend(['Runtime', 'Client', 'Server'], 'top'),
        auto_ylabels=True,
        second_y_axis=[0, 1, 1],
        second_y_label="RAM Usage [GB]",
        second_ylim=15,
        y_lim=80,
        colors=[blue, orange, green],
        second_y_lim_bottom=0
        # x_rotation=30
    )
