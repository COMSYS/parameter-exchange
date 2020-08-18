#!/usr/bin/env python3
"""Bloom Size Plot."""
import copy
import os
from typing import List, Union

from matplotlib import patches

# noinspection PyUnresolvedReferences
from plot.colors import (maroon, orange, yellow, green, purple, pink, blue,
                         lightblue)
# noinspection PyUnresolvedReferences
from plot.plot import (OUTPUT_DIR, INPUT_DIR,
                       read_data, error_plot_mult, stacked_bar_plot_mult,
                       join_stack_data,
                       EXTENSION,
                       Legend, BarText, font_size, plot_settings, figure_width,
                       cm, read_ram_max, convert_mib_to_gb)
# noinspection PyUnresolvedReferences
from plot.tls import compute_tls_curve

PLOT_ALL = 0
TLS = 1
IKV1 = "IM-2%"
IKV2 = "IM-2.5%"
IKV3 = "IM-3%"
WZL1 = "MT-Material"
WZL2 = "MT-Diameter"
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
TLS_HATCH = '////////'
hatch_rec = patches.Patch(facecolor="white", hatch=TLS_HATCH)
if TLS:
    ot_tls_color = 'forestgreen'
    psi_tls_color = 'lightyellow'
    psi_colors.insert(PSI_TLS_IND, psi_tls_color)
    both_colors.insert(PSI_TLS_IND, psi_tls_color)
    psi_colors.insert(OT_TLS_PSI - 1, ot_tls_color)
    bloom_colors.insert(OT_TLS_BLOOM - 1, ot_tls_color)
    both_colors.insert(OT_TLS_BOTH - 1, ot_tls_color)
    psi_hatches[PSI_TLS_IND] = TLS_HATCH
    psi_hatches[OT_TLS_PSI] = TLS_HATCH
    bloom_hatches[OT_TLS_BLOOM] = TLS_HATCH
    hatches[PSI_TLS_IND] = TLS_HATCH
    hatches[OT_TLS_BOTH] = TLS_HATCH
# -----------------------------------------------------------------------------
bloom_phases = [
    'Hash Key R.', 'Bloom R.', 'Matching',
    'Key R. (OT)', 'Record R.', 'Decryption']
psi_phases = [
    'Hash Key R.', 'PSI Prep.', 'PSI Exec.',
    'Key R. (OT)', 'Record R.', 'Decryption']
both_phases = [
    'Hash Key R.', 'PSI Prep.', 'PSI Exec.',
    'Bloom R.', 'Matching', 'Key R. (OT)',
    'Record R.', 'Decryption'
]
both_phases_no_tls = [
    'Hash Key R.', 'PSI Prep.', 'PSI Exec.',
    'Bloom R.', 'Matching', 'Key R. (OT)',
    'Record R.', 'Decryption'
]
bloom_phases_no_tls = [
    'Hash Key R.', 'Bloom R.', 'Matching',
    'Key R. (OT)', 'Record R.', 'Decryption']
if TLS:
    bloom_phases.insert(OT_TLS_BLOOM, 'OT TLS')
    psi_phases.insert(PSI_TLS_IND, 'PSI TLS')
    psi_phases.insert(OT_TLS_PSI, 'OT TLS')
    both_phases.insert(PSI_TLS_IND, 'PSI TLS')
    both_phases.insert(OT_TLS_BOTH, 'OT TLS')
ylabel = "Time [s]"
adjust_bar = None  # (0.095, 0.99, 0.99, 0.16)
adjust_bar2 = None  # (0.085, 0.99, 0.99, 0.16)
adjust_stacked_bar = None  # (0.085, 0.99, 0.92, 0.16)
adjust_stacked_bar2 = None  # (0.095, 0.99, 0.92, 0.16)
textboxes = [{'s': 'Standard BPE', 'y': 0.85, 'i': 0},
             {'s': 'PSI-based PPE', 'y': 0.85, 'i': 1},
             ]
backgrounds = [(0.5, 2.5, 'gray'), (2.5, 4.5, 'lightgray')]
joined_order = [0, 3, 4, 1, 2, 5, 6, 7]


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------


def remove_stacks(stack_lst: list, indexes: List[int]) -> list:
    """Remove all defined indices."""
    for j in sorted(indexes, reverse=True):
        # Start with largest value
        del stack_lst[j]
    return stack_lst


def remove_psi_stack(stack_lst: list) -> list:
    """Remove PSI Stacks and start time."""
    indexes = [3, 2, 0] if not TLS else [4, 3, 2, 0]
    return remove_stacks(stack_lst, indexes)


def remove_bloom_stacks(stack_lst: list) -> list:
    """"Remove Bloom Stacks and start time."""
    indexes = [5, 4, 0] if not TLS else [6, 5, 0]
    return remove_stacks(stack_lst, indexes)


def replace_psi_stacks(stack_lst: list) -> list:
    """Replace by 0 instead of remove"""
    ind = [2, 3]
    if TLS:
        ind.append(4)
    for index in ind:
        for k in stack_lst[index]:
            stack_lst[index][k] = [0, 0]
    del stack_lst[0]
    return stack_lst


def replace_bloom_stacks(stack_lst: list) -> list:
    """Replace by 0 instead of remove"""
    if TLS:
        ind = [5, 6]
    else:
        ind = [4, 5]
    for index in ind:
        for k in stack_lst[index]:
            stack_lst[index][k] = [0, 0]
    del stack_lst[0]
    return stack_lst


def add_tls_overhead(filename: str, stack_lst: List[dict],
                     x_ind: int = x_index):
    """Add the theoretic TLS overhead to correct pos. in lsit"""
    OT_SENT_COL = 25
    OT_RECV_COL = 27
    PSI_SENT_COL = 29
    PSI_RECV_COL = 31
    # Add PSI first
    sent = read_data(filename, x_ind, PSI_SENT_COL)
    recv = read_data(filename, x_ind, PSI_RECV_COL)
    base = {}
    for e in stack_lst[0]:
        base[e] = [0 for _ in range(len(stack_lst[0][e]))]
    tls = compute_tls_curve(base, sent, recv)
    stack_lst.insert(PSI_TLS_IND + 1, tls)  # +1 for start time
    # OT
    sent = read_data(filename, x_ind, OT_SENT_COL)
    recv = read_data(filename, x_ind, OT_RECV_COL)
    base = {}
    for e in stack_lst[0]:
        base[e] = [0 for _ in range(len(stack_lst[0][e]))]
    tls = compute_tls_curve(base, sent, recv)
    stack_lst.insert(OT_TLS_BOTH + 1, tls)  # +1 for start time


# noinspection PyShadowingNames
def substract_prev(stack_lst: List[dict]) -> List[dict]:
    """Substraact the previous time except it is 0, then go further back.
    A time might be zeor if it was not measured, e.g., PSI.
    """
    for i in range(len(stack_lst) - 1, 0, -1):
        data = stack_lst[i]
        for matches in data.keys():
            for j, v in enumerate(data[matches]):
                # Subtract prev. time
                k = i - 1
                while stack_lst[k][matches][j] == 0:
                    k -= 1
                data[matches][j] = v - stack_lst[k][matches][j]
    return stack_lst


# noinspection PyShadowingNames
def read_stacks_from_file(input_file: str) -> List[dict]:
    """Read values from file"""
    stacks = []
    for i in indices:
        d = read_data(input_file, x_index, i)
        stacks.append(d)
    return stacks


def get_stacks(filename: str) -> List[dict]:
    """Get the readily formated files"""
    stack_lst = substract_prev(read_stacks_from_file(filename))
    if TLS:
        add_tls_overhead(filename, stack_lst)
    return stack_lst


def get_tls_on_top(d1: dict) -> List[dict]:
    """Put TLS on top.
    Indices of d1: 1 - 10 (0 has been removed as start time)
    --> PSI TLS = 6
    OT TLS = 8
    """
    lower_layer = {
        j: d1[index] for j, index in enumerate([1, 2, 3, 5, 6, 7, 9, 10])}
    upper_layer = {index: [0, 0] for index in range(8)}
    upper_layer[2] = d1[4]
    upper_layer[5] = d1[8]
    return [lower_layer, upper_layer]


def get_tls_on_top_no_psi(d1: dict) -> List[dict]:
    """Put TLS on top.
    Indices of d1: 1, 5, 6,7,8,9, 10 (0 has been removed as start time)
    -->
    OT TLS = 8
    """
    lower_layer = {
        j: d1[index] for j, index in enumerate([1, 5, 6, 7, 9, 10])}
    upper_layer = {index: [0, 0] for index in range(6)}
    upper_layer[3] = d1[8]
    return [lower_layer, upper_layer]


# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Random PSI & Bloom
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_psi_vs_bloom2"
output_dir = output_dir_client + 'psi_vs_bloom/'
os.makedirs(output_dir, exist_ok=True)
input_file = input_dir + name + '.csv'
read_stacks = get_stacks(input_file)
# -----------------------------------------------------------------------------
# Bar Plot
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Joined
if 0 or PLOT_ALL:
    output_file = output_dir + f'joined_bar{EXTENSION}'
    xlabel = "Phase"
    title = "Full Client App - 500 Matches - Rel. Offset 0.3% - 10 Reps"
    data = {}
    for i, s in enumerate(read_stacks):
        if i != 0:
            data[i] = s[500]  # Only consider 500 matches
    data = get_tls_on_top(data)
    legend = Legend(['Random-0.3%'], location=Legend.TOP,
                    custom_labels=[(hatch_rec, "TLS")])
    tbs = copy.deepcopy(textboxes)
    stacked_bar_plot_mult(output_file, [data], xlabel, ylabel, title,
                          bar_legend=legend,
                          adjust=adjust_bar,  # small_xticks=True,
                          xlabels=both_phases_no_tls[:],
                          backgrounds=backgrounds,
                          text_boxes=tbs,
                          order=joined_order,
                          hatches=[None, TLS_HATCH],
                          colors_depend_on_bar=True,
                          colors=[blue, orange],
                          bar_texts=[
                              BarText(0, 0, 2, 0, r'|S|≈0.3 Mio.', 'center'),
                              BarText(0, 0, 3.5, 0, r'|S|≈0.3 Mio.',
                                      'center')],
                          y_lim=60
                          )
# -----------------------------------------------------------------------------
# Stacked Bar Plot  - Relative Offset 2 - Butthead - Bloom
# if 0 or PLOT_ALL:
#     output_file = output_dir + f'client_stacked_bloom_butthead{EXTENSION}'
#     xlabel = "Matches [#]"
#     title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
#     bloom_stacks = remove_psi_stack(copy.deepcopy(read_stacks))
#     stacked_bar_plot_mult(output_file, [bloom_stacks], xlabel,
#                           ylabel,
#                           title,
#                           stack_legend=Legend(bloom_phases[:],
#                                               empty_positions=[1]),
#                           label_step=1, colors=bloom_colors,
#                           hatches=bloom_hatches,
#                           adjust=adjust_stacked_bar,
#                           # bar_te Text(0, 1, 'all', 0, r'|S|≈0.3 Mio.',
#                           'in')]
#                           textboxes=[dict(x=0.08, y=0.7, s=r'|S|≈0.3 Mio.',
#                                           transform='transAxes', ha='center',
#                                           va='center', fontsize=font_size)]
#                           )
# -----------------------------------------------------------------------------
# Same for PSI
# -----------------------------------------------------------------------------
# Stacked Bar Plot  - Relative Offset 2 - Butthead - PSI
# if 0 or PLOT_ALL:
#     output_file = output_dir + f'client_stacked_psi_butthead{EXTENSION}'
#     xlabel = "Matches [#]"
#     title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
#     psi_stacks = remove_bloom_stacks(copy.deepcopy(read_stacks))
#     stacked_bar_plot_mult(output_file, [psi_stacks], xlabel,
#                           ylabel,
#                           title,
#                           stack_legend=Legend(psi_phases[:]),
#                           label_step=1, colors=psi_colors,
#                           hatches=psi_hatches,
#                           adjust=adjust_stacked_bar2,
#                           # bar_texts=[
#                           #     BarText(0, 1, 'all', 0, r'|S|≈0.3 Mio.',
#                           'in')]
#                           textboxes=[dict(x=0.08, y=0.9, s=r'|S|≈0.3 Mio.',
#                                           transform='transAxes', ha='center',
#                                           va='center', fontsize=font_size)],
#                           y_lim=800
#                           )
# -----------------------------------------------------------------------------
# Both  -> Replaced by divider.py
# -----------------------------------------------------------------------------
if 0 or PLOT_ALL:
    output_file = output_dir + f'client_stacked_butthead{EXTENSION}'
    xlabel = "Matches [#]"
    title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
    bloom_stacks = replace_psi_stacks(copy.deepcopy(read_stacks))
    psi_stacks = replace_bloom_stacks(copy.deepcopy(read_stacks))
    # stacked_bar_plot_two_y(output_file,
    #                        [bloom_stacks, psi_stacks], both_phases[:],
    #                        xlabel, ylabel, title,
    #                        label_step=1, colors=both_colors, hatches=hatches,
    #                        xticks=list(range(0, 1001, 100)),
    #                        adjust=(0.085, 0.9, 0.92, 0.16))
if 0 or PLOT_ALL:
    with plot_settings():
        output_file = output_dir + f'client_stacked_butthead{EXTENSION}'
        xlabel = "Matches [#]"
        title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
        bloom_stacks = replace_psi_stacks(copy.deepcopy(read_stacks))
        psi_stacks = replace_bloom_stacks(copy.deepcopy(read_stacks))
        # Shuffle order
        labels = both_phases[:]
        order = [0, 6, 7, 8, 9, 4, 5, 1, 2, 3]
        bloom_stacks = [bloom_stacks[i] for i in order]
        psi_stacks = [psi_stacks[i] for i in order]
        labels = [labels[i] for i in order]
        colors = [both_colors[i] for i in order]
        shatches = [hatches[i] for i in order]
        legend_order = [0, 7, 8, 9, 5, 6, 1, 2, 3, 4]
        stacked_bar_plot_mult(output_file,
                              [bloom_stacks, psi_stacks],
                              xlabel,
                              ylabel,
                              title,
                              stack_legend=Legend(labels, order=legend_order),
                              label_step=1,
                              colors=colors,
                              hatches=shatches,
                              xlabels=list(range(0, 1001, 100)),
                              y_lim=130,
                              # divide_y=True,
                              # ymin=0,
                              # ymax=90,
                              # ymin2=585,
                              # ymax2=690,
                              adjust=None,  # (0.09, 0.97, 0.92, 0.16),
                              textboxes=[dict(x=0.1, y=0.72, s=r'|S|≈0.3 Mio.',
                                              transform='transAxes',
                                              ha='center',
                                              va='center', fontsize=font_size)]
                              )
# -----------------------------------------------------------------------------
# Execution Time - Butthead
# if False or PLOT_ALL:
#     input_file = input_dir + name + '.csv'
#     output_file = output_dir + f'client_line_butthead{EXTENSION}'
#     xlabel = "Matches [#]"
#     title = "Full Client App - 0-1000 Matches - Rel. Offset 0.3% - 10 Reps"
#     start = read_data(input_file, 4, 6)
#     psi_start = read_data(input_file, 4, 8)
#     bloom_start = read_data(input_file, 4, 11)
#     bloom_end = read_data(input_file, 4, 11)
#     end = read_data(input_file, 4, 16)
#     bloom = {}
#     psi = {}
#     for x in end:
#         bloom[x] = []
#         psi[x] = []
#         for i, _ in enumerate(end[x]):
#             bt = end[x][i] - bloom_start[x][i] + \
#                  (psi_start[x][i] - start[x][i])
#             bloom[x].append(bt)
#             pt = (end[x][i] - bloom_end[x][i] +
#                     (bloom_start[x][i] - start[x][i]))
#             psi[x].append(pt)
#     error_plot_mult(
#         [bloom, psi],
#         output_file,
#         100,
#         0,
#         700,
#         100,
#         xlabel,
#         ylabel,
#         title,
#         ['Bloom', 'PSI'],
#         x_label_step=1,
#         xticks=sorted(end.keys()),
#         x_labels=sorted(end.keys()),
#         legend_pos=None
#
#     )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                WZL Client 1
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_wzl1"
output_dir = output_dir_client + 'wzl/'
os.makedirs(output_dir, exist_ok=True)
input_file = input_dir + name + '.csv'
read_stacks_wzl1 = get_stacks(input_file)
# -----------------------------------------------------------------------------
# Same for Joined
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Joined
# if 0:
#     output_file = output_dir + f'joined_bar{EXTENSION}'
#     xlabel = "Phase"
#     title = "Client App - WZL Data - Match all Materials - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks_wzl1):
#         if i != 0:
#             data[i] = s[10]  # Only consider 500 matches
#     bar_plot_mult(output_file, data, xlabel, ylabel, title,
#     xticks=both_phases[:],
#              small_xticks=True)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                WZL Client 2
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_wzl2"
input_file = input_dir + name + '.csv'
read_stacks_wzl2 = get_stacks(input_file)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Same for Joined
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Joined
if 0 or PLOT_ALL and TLS:
    with plot_settings():
        output_file = output_dir + f'wzl_joined_bar{EXTENSION}'
        xlabel = "Phase"
        title = "Client App - WZL Data - 10 Reps"
        data1 = {}
        for i, s in enumerate(read_stacks_wzl1):
            if i != 0:
                data1[i] = s[10]  # Only consider 500 matches
        data2 = {}
        for i, s in enumerate(read_stacks_wzl2):
            if i != 0:
                data2[i] = s[6]  # Only consider 500 matches
        data1 = get_tls_on_top(data1)
        data2 = get_tls_on_top(data2)
        legend = Legend([WZL1, WZL2], location=Legend.TOP,
                        custom_labels=[(hatch_rec, "TLS")])
        tbs = copy.deepcopy(textboxes)
        for t in tbs:
            t['y'] = 0.83
        stacked_bar_plot_mult(output_file, [data1, data2], xlabel, ylabel,
                              title,
                              xlabels=both_phases_no_tls[:],
                              adjust=adjust_bar2,  # small_xticks=True,
                              backgrounds=backgrounds,
                              text_boxes=tbs,
                              order=joined_order,
                              hatches=[None, TLS_HATCH],
                              colors_depend_on_bar=True,
                              colors=[blue, orange],
                              bar_legend=legend,
                              bar_texts=[
                                  BarText(0, 0, 2, 0, '|S|=11', 'center'),
                                  BarText(0, 0, 4, 0, '|S|=11', 'center'),
                                  BarText(1, 0, 2, 0, '|S|=701', 'center'),
                                  BarText(1, 0, 4, 0, '|S|=701', 'center')
                              ],
                              y_lim=31
                              )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Both Both
# -----------------------------------------------------------------------------
# if 0 or PLOT_ALL:
#     output_file = output_dir + f'client_wzl{EXTENSION}'
#     xlabel = "Metric"
#     title = "Full Client App - WZL Data - 10 Reps"
#     stacks = join_stack_data([read_stacks_wzl1, read_stacks_wzl2],
#                              [[WZL1], [WZL2]])
#     bloom_stacks = replace_psi_stacks(copy.deepcopy(stacks))
#     psi_stacks = replace_bloom_stacks(copy.deepcopy(stacks))
#     stacked_bar_plot_mult(output_file, [bloom_stacks, psi_stacks],
#                           xlabel, ylabel, title,
#                           stack_legend=Legend(both_phases[:]),
#                           label_step=1, colors=both_colors,
#                           hatches=hatches[:],
#                           adjust=adjust_stacked_bar, y_lim=45,
#                           bar_texts=[
#                               BarText(0, 4, 0, 0, '|S|=11', 'in', rotation=0,
#                                       color='white'),
#                               BarText(1, 2, 0, 0, '|S|=11', 'in',
#                               rotation=0),
#                               BarText(0, 4, 1, 0, '|S|=701', 'in',
#                               rotation=0,
#                                       color='white'),
#                               BarText(1, 2, 1, 0, '|S|=701', 'in',
#                               rotation=0)
#                           ]
#                           )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Client 1 - Rounding: 2, rel. Offset 2%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_ikv1"
input_file = input_dir + name + '.csv'
# Read Data
read_stacks_ikv1 = get_stacks(input_file)
# -----------------------------------------------------------------------------
if 0 or PLOT_ALL and TLS:
    output_dir = output_dir_client + 'ikv/'
    os.makedirs(output_dir, exist_ok=True)
    output_file = output_dir + f'ikv1_bar{EXTENSION}'
    xlabel = "Phase"
    title = "Client App - IKV Data - IM-2% - 10 Reps"
    data1 = {}
    for i, s in enumerate(read_stacks_ikv1):
        if i != 0:
            data1[i] = s[77]  # Only consider 500 matches
    data1 = get_tls_on_top(data1)
    legend = Legend([IKV1], location=Legend.TOP,
                    custom_labels=[(hatch_rec, "TLS")])
    tbs = copy.deepcopy(textboxes)
    y = 0.85
    tbs[0]['y'] = y
    tbs[1]['y'] = y
    # tbs.append({'s': '(Section 8.2)', 'y': y-0.09,
    #             'i': 1, 'fontsize': legend_font_size})
    stacked_bar_plot_mult(output_file, [data1], xlabel, ylabel,
                          title,
                          xlabels=both_phases_no_tls[:],
                          adjust=adjust_bar2,  # small_xticks=True,
                          backgrounds=backgrounds,
                          text_boxes=tbs,
                          order=joined_order,
                          hatches=[None, TLS_HATCH],
                          colors_depend_on_bar=True,
                          colors=[blue, orange],
                          bar_legend=legend,
                          bar_texts=[
                              BarText(0, 0, 2, 0, r'|S|≈1 Mio.', 'on'),
                              BarText(0, 1, 3.5, 0, r'|S|≈1 Mio.', 'center'),
                          ],
                          y_lim=120
                          )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Client 2 - Rounding: 2, rel. Offset 2.5%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_ikv2"
input_file = input_dir + name + '.csv'
read_stacks_ikv2 = get_stacks(input_file)
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                IKV Client 3 - Rounding: 2, rel. Offset 3%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_client_ikv3"
input_file = input_dir + name + '.csv'
read_stacks_ikv3 = get_stacks(input_file)
if 1 or PLOT_ALL and TLS:
    output_dir = output_dir_client + 'ikv/'
    os.makedirs(output_dir, exist_ok=True)
    output_file = output_dir + f'ikv3_bar{EXTENSION}'
    xlabel = "Phase"
    title = "Client App - IKV Data - IM-3% - 10 Reps"
    data1 = {}
    for i, s in enumerate(read_stacks_ikv3):
        if i not in [0, 2, 3, 4]:
            # Ignore start and PSI Stack
            data1[i] = s[77]
    data1 = get_tls_on_top_no_psi(data1)
    legend = Legend([IKV3], location=Legend.TOP,
                    custom_labels=[(hatch_rec, "TLS")])
    tbs = copy.deepcopy(textboxes)
    y = 0.85
    tbs[0]['y'] = y
    tbs[1]['y'] = y
    stacked_bar_plot_mult(output_file, [data1], xlabel, ylabel,
                          title,
                          bar_legend=Legend([IKV3],
                                            location=Legend.TOP,
                                            custom_labels=[
                                                (hatch_rec, "TLS")]),
                          ymin=0,
                          ymax=35,
                          ymin2=49000,
                          ymax2=52000,
                          y_label_coord=-0.09,
                          xlabels=bloom_phases_no_tls[:],
                          adjust=None,
                          divide_y=True,
                          colors_depend_on_bar=True,
                          colors=[blue, orange],
                          bar_texts=[
                              BarText(0, 0, 2, 1, r'|S|≈2.5 Bil.', 'center',
                                      color='white'),
                          ],
                          gridspec_kw={'height_ratios': [1, 2.5]},
                          y_lim=31,
                          y_label_coord2=-0.6
                          )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# Both Both
# -----------------------------------------------------------------------------
# if 0 or PLOT_ALL:
#     output_dir = output_dir_client + 'ikv/'
#     os.makedirs(output_dir, exist_ok=True)
#     output_file = output_dir + f'client_ikv{EXTENSION}'
#     xlabel = "Metric"
#     title = "Client App - IKV Data - rel. Offset - 10 Reps"
#     stacks1 = remove_psi_stack(copy.deepcopy(read_stacks_ikv1))
#     stacks2 = remove_psi_stack(copy.deepcopy(read_stacks_ikv2))
#     stacked_bar_plot_two_y(output_file, [stacks1, stacks2], bloom_phases[:],
#                            xlabel, ylabel, title,
#                            label_step=1, colors=bloom_colors,
#                            hatches=bloom_hatches,
#                            adjust=adjust_stacked_bar)
# -----------------------------------------------------------------------------
# Same for Joined
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Joined
if 0 or PLOT_ALL:
    output_dir = output_dir_client + 'ikv/'
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
    data1 = get_tls_on_top_no_psi(data1)
    data2 = get_tls_on_top_no_psi(data2)
    stacked_bar_plot_mult(output_file, [data1, data2], xlabel, ylabel,
                          title,
                          bar_legend=Legend([IKV1, IKV2],
                                            location=Legend.TOP,
                                            custom_labels=[(hatch_rec, "TLS")]),
                          ymin=0,
                          ymax=35,
                          ymin2=5600,
                          ymax2=6500,
                          y_label_coord=-0.09,
                          xlabels=bloom_phases_no_tls[:],
                          adjust=None,
                          divide_y=True,
                          colors_depend_on_bar=True,
                          colors=[blue, orange],
                          bar_texts=[
                              BarText(0, 0, 2, 1, r'|S|≈1 Mio.', 'in',
                                      color='white'),
                              BarText(1, 0, 2, 1, r'|S|≈143 Mio.',
                                      'center')],
                          gridspec_kw={'height_ratios': [1, 2.5]},
                          y_lim=31,
                          y_label_coord2=-0.6
                          )
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
#                Random Client 2 - Rounding: 3, ID Len 10, rel. Offset 0.5%
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
name = "butthead_bloom"
output_dir = output_dir_client + 'bloom/'
os.makedirs(output_dir, exist_ok=True)
input_file = input_dir + name + '.csv'
read_stacks = get_stacks(input_file)
# -----------------------------------------------------------------------------
# Bar Plot - Butthead Run - Bloom
# if False or PLOT_ALL:
#     output_file = output_dir + f'client_bar_bloom{EXTENSION}'
#     xlabel = "Phase"
#     title = "Full Client App - 500 Matches - Rel. Offset 0.5% - 10 Reps"
#     data = {}
#     for i, s in enumerate(read_stacks):
#         if i not in [0, 2, 3, 4]:
#             # Ignore start and PSI Stack
#             data[i] = s[500]  # Only consider one number of matches
#     stacked_bar_plot_mult(output_file, [[data]], xlabel, ylabel, title,
#                           xlabels=bloom_phases[:],
#                           adjust=adjust_bar,
#                           bar_texts=[
#                               BarText(0, 0, 2, 0, '|S|≈29 Mio.', 'in',
#                                       color='white')],
#                           )
# -----------------------------------------------------------------------------
# Stacked Bar Plot
if False or PLOT_ALL:
    output_file = output_dir + f'client_stacked_bloom{EXTENSION}'
    xlabel = "Results [#]"
    title = "Full Client legend=Legend(legend_labels)App - ID Len. 10 -" \
            " Rel. Offset 0.5% - 10 Reps"
    stacks = remove_psi_stack(copy.deepcopy(read_stacks))
    stacked_bar_plot_mult(output_file, [stacks], xlabel,
                          ylabel,
                          title,
                          stack_legend=Legend(bloom_phases[:],
                                              empty_positions=[1]),
                          adjust=adjust_stacked_bar2,
                          label_step=1, colors=bloom_colors,
                          hatches=bloom_hatches,
                          # bar_texts=[
                          #     BarText(0, 2, 'all', 0, r'|S|≈29 Mio.', 'in')],
                          textboxes=[dict(x=0.075, y=0.88, s=r'|S|≈29 Mio.',
                                          transform='transAxes', ha='center',
                                          va='center', fontsize=font_size)],
                          y_lim=450
                          )
# -----------------------------------------------------------------------------
# RAM Plot
if 0 or PLOT_ALL:
    output_file = output_dir + f'client_bloom_ram{EXTENSION}'
    xlabel = "Results [#]"
    title = "Full Client legend=Legend(legend_labels)App - ID Len. 10 -" \
            " Rel. Offset 0.5% - 10 Reps"
    d = read_ram_max(input_dir + 'butthead_bloom_ram' + '.csv', 2, 3)
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
        # auto_ylabels=True,
    )
if 0 or PLOT_ALL:
    output_file = OUTPUT_DIR + 'client/psi_vs_bloom/' + \
        f'client_ram{EXTENSION}'
    xlabel = "Results [#]"
    title = "Full Client legend=Legend(legend_labels)App - ID Len. 10 -" \
            " Rel. Offset 0.5% - 10 Reps"
    d = read_ram_max(input_dir + 'butthead_psi_vs_bloom2_ram' + '.csv', 2, 3)
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
        # auto_ylabels=True,
    )
