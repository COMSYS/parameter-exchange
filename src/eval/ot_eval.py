#!/usr/bin/env python3
"""Evaluate OT properties.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import contextlib
import logging
import os
import platform
import subprocess
import sys
import time

from lib import config, helpers
from lib.helpers import get_free_port, add_latency, reset_port, \
    add_async_bandwidth
from lib.logging import configure_root_loger
from .shared import lb, read_output, check_if_client_hangs

sys.path.append(config.WORKING_DIR + 'cython/ot')
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTSender  # noqa
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTReceiver  # noqa

# Constants -------------------------------------------------------------------
SET_SIZES = [1] + list(range(1000000, 1300001, 1000000)) + \
    [2 ** i for i in range(20, 24)]  # 2 ** 20
NUM_OTS = [1] + list(range(20, 101, 20))
LATENCY = 0  # range(0, 301, 50)  # ms
BANDWIDTH = 0  # [0, 6000, 50000, 100000]
RESUME = False
HOST = "localhost"
NUMTHREADS = 1
STATSECPARAM = 40
MALSECURE = False
INPUTBITCOUNT = 128
TLS = False
ROUNDS_START = 0
ROUNDS_END = 10
DIRECTORY = config.EVAL_DIR + "ot" + "/"
os.makedirs(DIRECTORY, exist_ok=True)
CREATE_TCPDUMP = False
# -----------------------------------------------------------------------------
log = configure_root_loger(logging.INFO, None)


def write_header(e_type: str, file_path: str, row_fmt: str):
    """Write header of eval files."""
    with open(file_path, 'w') as fd:
        fd.write("------------------------HEADER------------------------\n")
        fd.write(f"EVAL: {e_type}\n")
        fd.write(f"OT Setsize: {SET_SIZES}\n")
        fd.write(f"Performed OTs: {NUM_OTS}\n")
        fd.write(f"Rounds: {ROUNDS_END}\n")
        fd.write(f"TLS: {TLS}\n")
        fd.write(f"Malicious Secure: {MALSECURE}\n")
        fd.write(f"Latency: {LATENCY}\n")
        fd.write(f"Statistical Security Paramters: {STATSECPARAM}\n")
        fd.write(f"Input Bit Count: {INPUTBITCOUNT}\n")
        fd.write(f"Threads: {NUMTHREADS}\n")
        fd.write(f"RAM Measurement Interval: 0.5s\n")
        fd.write(f"RAM measurements written to filename_serverram.csv and "
                 f"filename_receiverram.csv.\n")
        fd.write(f"{row_fmt}\n")
        fd.write("----------------------END-HEADER----------------------\n")


def create_tcpdump(setsize: int, num_ots: int, rep: int,
                   port: int) -> subprocess.Popen:
    """Create a full pcap of the communication."""
    out_dir = DIRECTORY + 'tcpdumps/'
    os.makedirs(out_dir, exist_ok=True)
    filepath = out_dir + f'dump_{setsize}_{num_ots}_{rep}.pcap'
    cmd = ['sudo', 'tcpdump', '-i', 'lo', '-w', filepath, 'port', str(port)]

    s = subprocess.Popen(cmd)
    return s


def ot_time(base_name: str) -> None:
    """
    Main method of OT eval.
    :param base_name:
    :return:
    """
    server_ram_file = DIRECTORY + base_name + '_serverram.csv'
    client_ram_file = DIRECTORY + base_name + '_clientram.csv'
    file_path = DIRECTORY + base_name + '.csv'
    rs = ROUNDS_START
    row_fmt = f"TIMESTAMP;ROUND;SETSIZE;NUMOTS;TLS;MALSECURE;LATENCY;" \
              f"BANDWIDTH[kBit/s];STATSECPARAM;INPUTBITCOUNT;THREADS;" \
              f"SENDERTIME[s];" \
              f"RECEIVERTIME[s];" \
              f"ClientToServer[Byte];ClientToServer[Packets];" \
              f"ServerToClient[Byte];ServerToClient[Packets];" \
              f"[ERROR]"
    if not RESUME or not os.path.exists(file_path):
        # Write header if new file only
        write_header("PSI Time Eval", file_path, row_fmt)
        row_fmt = "TIMESTAMP;ROUND;SETSIZE;NUMOTS;TLS;MALICIOUS;LATENCY;" \
                  "BANDWIDTH[kBit/s];STATSECPARAM;INPUTBITCOUNT;THREADS;" \
                  "json.dumps(mem);ERROR"
        write_header("PSI Time Eval", server_ram_file, row_fmt)
        write_header("PSI Time Eval", client_ram_file, row_fmt)
    for r in lb(range(rs, ROUNDS_END), "Rounds", leave=True):
        for s in lb(SET_SIZES, "Set Sizes", leave=False):
            for o in lb(NUM_OTS, "Total OTs", leave=False):
                for stat in lb(STATSECPARAM, "StatSecParam", leave=False):
                    for latency in lb(LATENCY, "Latency", leave=False):
                        for bw in lb(BANDWIDTH, "Rate", leave=False):
                            success = False
                            while not success:
                                port = get_free_port()
                                error = ""
                                # Add latency/bw-limit to port
                                if platform.system() != "Darwin":
                                    # Latency does not work on Max
                                    reset_port()
                                    if latency != 0:
                                        add_latency(latency)
                                    if bw != 0:
                                        add_async_bandwidth(bw, port)
                                elif LATENCY != 0 or BANDWIDTH != 0:
                                    raise RuntimeError(
                                        "Mac does not support latencies and"
                                        "bandwidths.")

                                stc, stc_file = \
                                    helpers.start_trans_measurement(
                                        port, direction="src", sleep=False)
                                cts, cts_file = \
                                    helpers.start_trans_measurement(
                                        port, direction="dst", sleep=False)

                                if CREATE_TCPDUMP:
                                    tcpdump_p = create_tcpdump(s, o, r, port)

                                time.sleep(0.5)  # Wait for start
                                sp, cp = None, None
                                try:
                                    sp = start(False, port, s, o, stat,
                                               MALSECURE,
                                               TLS, server_ram_file, r,
                                               latency,
                                               HOST, False, )
                                    cp = start(True, port, s, o, stat,
                                               MALSECURE,
                                               TLS, client_ram_file, r,
                                               latency,
                                               HOST, False)

                                    # Check that connection was successful.
                                    check_if_client_hangs(cp)

                                    sp.wait()
                                    cp.wait()

                                    # Read server output
                                    output, err = sp.communicate()
                                    if err != "":
                                        log.error(err)
                                    error += err.strip().replace('\n', '\\n')
                                    server_time, server_mem, err = read_output(
                                        output)
                                    error += err

                                    # Read client output
                                    output, err = cp.communicate()
                                    err = err.replace(
                                        "client socket connect error (hangs).",
                                        "").strip()
                                    if err != "":
                                        log.error(err)
                                    error += err.strip().replace('\n', '\\n')
                                    client_time, client_mem, err = read_output(
                                        output)
                                    error += err

                                    # Stop transmission measurement
                                    # Kill TCPDUMP
                                    helpers.kill_tcpdump()
                                    stc.wait(30)
                                    cts.wait(5)

                                    server_sent, server_pkts = \
                                        helpers.read_tcpstat_from_file(
                                            stc_file)
                                    client_sent, client_pkts = \
                                        helpers.read_tcpstat_from_file(
                                            cts_file)

                                    timestamp = time.strftime(
                                        '%Y-%m-%d %H:%M:%S')
                                    # Standard File
                                    with open(file_path, "a") as fd:
                                        fd.write(';'.join((
                                            timestamp,
                                            str(r),
                                            str(s),
                                            str(o),
                                            str(TLS),
                                            str(MALSECURE),
                                            str(latency),
                                            str(bw),
                                            str(STATSECPARAM),
                                            str(INPUTBITCOUNT),
                                            str(NUMTHREADS),
                                            str(server_time),
                                            str(client_time),
                                            str(client_sent),
                                            str(client_pkts),
                                            str(server_sent),
                                            str(server_pkts),
                                            error
                                        )) + '\n')
                                    # Client RAM
                                    with open(client_ram_file, 'a') as fd:
                                        fd.write(
                                            ';'.join((
                                                timestamp,
                                                str(r),
                                                str(s),
                                                str(o),
                                                str(TLS),
                                                str(MALSECURE),
                                                str(latency),
                                                str(bw),
                                                str(STATSECPARAM),
                                                str(INPUTBITCOUNT),
                                                str(NUMTHREADS),
                                                str(client_mem),
                                                error
                                            )) + '\n'
                                        )
                                    # Server RAM
                                    with open(server_ram_file, 'a') as fd:
                                        fd.write(
                                            ';'.join((
                                                timestamp,
                                                str(r),
                                                str(s),
                                                str(o),
                                                str(TLS),
                                                str(MALSECURE),
                                                str(latency),
                                                str(bw),
                                                str(STATSECPARAM),
                                                str(INPUTBITCOUNT),
                                                str(NUMTHREADS),
                                                str(server_mem),
                                                error
                                            )) + '\n'
                                        )
                                    success = True
                                except Exception as e:
                                    log.exception(str(e))
                                    success = False
                                finally:
                                    # Clean Up
                                    # Kill TCPDUMP
                                    helpers.kill_tcpdump()
                                    # Remove tempfiles
                                    with contextlib.suppress(
                                            FileNotFoundError):
                                        os.remove(stc_file)
                                        os.remove(cts_file)
                                    if sp is not None:
                                        sp.kill()
                                    if cp is not None:
                                        cp.kill()
                                    # Remove latency
                                    if latency != 0 or bw != 0:
                                        reset_port()


def start(isClient: bool, port: int, set_size: int, num_ots: int,
          statsecparam: int, malicious: bool, tls: bool,
          ram_file: str, rnd: int, latency: int,
          host: str = 'localhost', debug: bool = False) -> subprocess.Popen:
    """
    Start OT sender/receiver in new process.
    :return: Create Popen object
    """

    # measure = '/usr/bin/time -f "%e:%M"'
    # environment = 'OMP_NUM_THREADS=' + str(C_cur)

    if isClient:
        cmd = f'python3 -m eval.ot.receiver'
    else:
        cmd = f'python3 -m eval.ot.sender'

    cmd += f" -p {port} -s {set_size} --statsecparam {statsecparam} -n " \
           f"{num_ots} --host {host} -r {rnd} -l {latency} -o {ram_file}"
    if tls:
        cmd += ' -t'
    if malicious:
        cmd += ' -m'

    log.debug('Execute: {}'.format(cmd))
    cmd = cmd.split(" ")
    proc = subprocess.Popen(cmd, universal_newlines=True,
                            stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    return proc


if __name__ == '__main__':
    p = argparse.ArgumentParser("OT Eval")
    p.add_argument('--resume', help="Resume Eval", action="store_true")
    p.add_argument('-r', '--reps', help="Rounds", action='store', default=0,
                   type=int)
    p.add_argument('-o', '--out', type=str, action='store',
                   help="Base filename WITHOUT file-ending!", required=True)
    p.add_argument('-t', '--tls', type=int, action='store',
                   help="TLS Activated? [1 or 0]", choices=[0, 1],
                   required=True)
    p.add_argument('-m', '--malicious', action='store_true',
                   help="Use OOS16?")
    p.add_argument('-s', '--setsize',
                   help="Setsize: Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('-n', '--numOTs',
                   help="# OTs to perform: Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('--statsecparam',
                   help="Statistical Sec. Parameters: "
                        "Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('-l', '--latency',
                   help="Latency: Either constant or 3 values.",
                   metavar=('CONSTANT/MIN', 'MAX STEP'),
                   nargs='+', action='store', type=int)
    p.add_argument('-b', '--bandwidth', action='store_true',
                   help="Limit bandwidth?")
    p.add_argument('--baseline', action='store_true',
                   help="76Baseline?")
    args = p.parse_args()
    if args.resume:
        RESUME = True
    if args.malicious:
        MALSECURE = True
        INPUTBITCOUNT = 76
    if args.tls > 0:
        TLS = True
    else:
        TLS = False
    if args.reps > 0:
        ROUNDS_END = args.reps
    filename = args.out
    if args.setsize is not None:
        if len(args.setsize) == 1:
            SET_SIZES = [args.setsize[0]]
        elif len(args.setsize) == 3:
            SET_SIZES = range(args.setsize[0],
                              args.setsize[1] + args.setsize[2],
                              args.setsize[2])
        else:
            raise ValueError("Either 1 or 3 setsize parameters!")
    if args.numOTs is not None:
        if len(args.numOTs) == 1:
            NUM_OTS = [args.numOTs[0]]
        elif len(args.numOTs) == 3:
            NUM_OTS = range(args.numOTs[0],
                            args.numOTs[1] + args.numOTs[2],
                            args.numOTs[2])
        else:
            raise ValueError("Either 1 or 3 # OTs parameters!")
    if args.statsecparam is not None:
        if len(args.statsecparam) == 1:
            STATSECPARAM = [args.statsecparam[0]]
        elif len(args.statsecparam) == 3:
            STATSECPARAM = range(args.statsecparam[0],
                                 args.statsecparam[1] + args.statsecparam[2],
                                 args.statsecparam[2])
        else:
            raise ValueError("Either 1 or 3 statSecParam parameters!")
    if args.latency is not None:
        if len(args.latency) == 1:
            LATENCY = [args.latency[0]]
        elif len(args.latency) == 3:
            LATENCY = range(args.latency[0],
                            args.latency[1] + args.latency[2],
                            args.latency[2])
        else:
            raise ValueError("Either 1 or 3 latency parameters!")
    if args.bandwidth:
        BANDWIDTH = [0, 6000, 50000, 100000]
    else:
        BANDWIDTH = BANDWIDTH
    if args.baseline:
        INPUTBITCOUNT = 76
    ot_time(filename)
