#!/usr/bin/env python3
"""Evaluate PSI properties.

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

sys.path.append(config.WORKING_DIR + 'cython/psi')
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSISender  # noqa
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSIReceiver  # noqa

# Constants -------------------------------------------------------------------
SET_SIZES = [1] + list(range(10 ** 6, 2 * 10 ** 7 + 1, 10 ** 6)) + \
            [2 ** i for i in range(20, 25)]
# SET_SIZES = range(10 ** 5, 10 ** 6 + 1, 10 * 5)
RESUME = False
MALSECURE = False
LATENCY = 0  # range(0, 301, 50)  # ms
BANDWIDTH = 0  # [0, 6000, 50000, 100000]
HOST = "localhost"
NUMTHREADS = 1
STATSECPARAM = 40
ROUNDS_START = 0
ROUNDS_END = 10
DIRECTORY = config.EVAL_DIR + "psi" + "/"
os.makedirs(DIRECTORY, exist_ok=True)
# -----------------------------------------------------------------------------
log = configure_root_loger(logging.INFO, None)


def write_header(eval_type: str, file_path: str, row_fmt: str):
    """Write eval header into files."""
    with open(file_path, 'w') as fd:
        fd.write("------------------------HEADER------------------------\n")
        fd.write(f"EVAL: {eval_type}\n")
        fd.write(f"Set Sizes: {SET_SIZES}\n")
        fd.write(f"Rounds: {ROUNDS_END}\n")
        fd.write(f"TLS: {TLS}\n")
        fd.write(f"SCHEME: {SCHEME}\n")
        fd.write(f"Statistical Security Paramters: {STATSECPARAM}\n")
        fd.write(f"Threads: {NUMTHREADS}\n")
        fd.write(f"Latency: {LATENCY}\n")
        fd.write(f"Bandwidth:{BANDWIDTH}\n")
        fd.write(f"RAM Measurement Interval: 0.5s\n")
        fd.write(f"RAM measurements written to filename_serverram.csv and "
                 f"filename_receiverram.csv.\n")
        fd.write(f"{row_fmt}\n")
        fd.write("----------------------END-HEADER----------------------\n")


def psi_time(base_name: str) -> None:
    """
    Main method of PSI eval.
    :param base_name: Base filename without extension
    :return:
    """
    server_ram_file = DIRECTORY + base_name + '_serverram.csv'
    client_ram_file = DIRECTORY + base_name + '_clientram.csv'
    file_path = DIRECTORY + base_name + '.csv'
    rs = ROUNDS_START
    row_fmt = f"TIMESTAMP;ROUND;SETSIZE;TLS;MALSECURE;STATSECPARAM;THREADS;" \
              f"LATENCY[ms];BANDWIDTH[kBit/s];" \
              f"SERVERTIME[s];CLIENTTIME[s];" \
              f"ClientToServer[Byte];ClientToServer[Packets];" \
              f"ServerToClient[Byte];ServerToClient[Packets];" \
              f"[ERROR]"
    if not RESUME or not os.path.exists(file_path):
        # Write header if new file only
        write_header("PSI Time Eval", file_path, row_fmt)
        row_fmt = f"TIMESTAMP;ROUND;SETSIZE;TLS;MALSECURE;STATSECPARAM;" \
                  f"THREADS;LATENCY[ms];BANDWIDTH[kBit/s];json.dumps(mem);" \
                  f"[ERROR]"
        write_header("PSI Time Eval", server_ram_file, row_fmt)
        write_header("PSI Time Eval", client_ram_file, row_fmt)
    for r in lb(range(rs, ROUNDS_END), "Rounds", leave=True):
        for s in lb(SET_SIZES, "Set Sizes", leave=False):
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
                            time.sleep(0.5)  # Wait for start
                            sp, cp = None, None
                            try:
                                sp = start(False, port, s, stat, MALSECURE,
                                           TLS, server_ram_file, r, latency,
                                           HOST, False)
                                cp = start(True, port, s, stat, MALSECURE,
                                           TLS, client_ram_file, r, latency,
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

                                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                                with open(file_path, "a") as fd:
                                    fd.write(';'.join((
                                            timestamp,
                                            str(r),
                                            str(s),
                                            str(TLS),
                                            str(MALSECURE),
                                            str(STATSECPARAM),
                                            str(NUMTHREADS),
                                            str(latency),
                                            str(bw),
                                            str(server_time),
                                            str(client_time),
                                            str(client_sent),
                                            str(client_pkts),
                                            str(server_sent),
                                            str(server_pkts),
                                            error
                                    )) + '\n')
                                # Client RAM
                                with open(client_ram_file, "a") as fd:
                                    fd.write(';'.join((
                                            timestamp,
                                            str(r),
                                            str(s),
                                            str(TLS),
                                            str(MALSECURE),
                                            str(STATSECPARAM),
                                            str(NUMTHREADS),
                                            str(latency),
                                            str(bw),
                                            str(client_mem),
                                            error
                                    )) + '\n')
                                # Server RAM
                                with open(server_ram_file, "a") as fd:
                                    fd.write(';'.join((
                                            timestamp,
                                            str(r),
                                            str(s),
                                            str(TLS),
                                            str(MALSECURE),
                                            str(STATSECPARAM),
                                            str(NUMTHREADS),
                                            str(latency),
                                            str(bw),
                                            str(server_mem),
                                            error
                                    )) + '\n')
                                success = True
                            except Exception as e:
                                log.exception("Main Loop not successful.")
                                success = False
                            finally:
                                # Clean Up
                                # Kill TCPDUMP
                                helpers.kill_tcpdump()
                                # Remove tempfiles
                                with contextlib.suppress(FileNotFoundError):
                                    os.remove(stc_file)
                                    os.remove(cts_file)
                                # Remove latency
                                if latency != 0 or bw != 0:
                                    reset_port()
                                if sp is not None:
                                    sp.kill()
                                if cp is not None:
                                    cp.kill()


def start(isClient: bool, port: int, set_size: int,
          statsecparam: int, malicious: bool, tls: bool,
          ram_file: str, rnd: int, latency: int,
          host: str = 'localhost', debug: bool = False,
          rr17: bool = False) -> subprocess.Popen:
    """Start PSI receiver/sender in own process.
    :return: Popen object of process
    """
    if isClient:
        cmd = f'python3 -m eval.psi.receiver'
    else:
        cmd = f'python3 -m eval.psi.sender'

    cmd += f" -p {port} -s {set_size} --statsecparam {statsecparam} " \
           f"--host {host} -r {rnd} -l {latency} -o {ram_file}"
    if tls:
        cmd += ' -t'
    if malicious:
        cmd += ' -m'
    if rr17:
        cmd += '--r17'

    log.debug('Execute: {}'.format(cmd))
    cmd = cmd.split(" ")
    p = subprocess.Popen(cmd, universal_newlines=True,
                         stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    return p


if __name__ == '__main__':
    p = argparse.ArgumentParser("PSI Eval")
    p.add_argument('--resume', help="Resume Eval", action="store_true")
    p.add_argument('-r', '--reps', help="Rounds", action='store', default=0,
                   type=int)
    p.add_argument('-o', '--out', type=str, action='store',
                   help="Base filename WITHOUT file-ending!", required=True)
    p.add_argument('-t', '--tls', type=int, action='store', required=True,
                   help="TLS Activated? [1 or 0]", choices=[0, 1])
    p.add_argument('-m', '--malicious', action='store_true',
                   help="Use RR16?")
    p.add_argument('--rr17', action='store_true',
                   help="Use RR17")
    p.add_argument('-b', '--bandwidth', action='store_true',
                   help="Limit bandwidth?")
    p.add_argument('-s', '--setsize',
                   help="Setsize: Either constant or 3 values.",
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
    args = p.parse_args()
    if args.resume:
        RESUME = True
    if args.malicious:
        MALSECURE = True
        SCHEME = "RR16"
    else:
        MALSECURE = False
        SCHEME = "KKRT16"
    if args.rr17:
        MALSECURE = True
        SCHEME = "RR17"
    if args.bandwidth:
        BANDWIDTH = [0, 6000, 50000, 100000]
        SET_SIZES = [1] + list(range(10 ** 5, 10 ** 6 + 1, 10 ** 5))
    else:
        BANDWIDTH = BANDWIDTH
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
    psi_time(filename)
