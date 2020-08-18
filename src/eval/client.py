#!/usr/bin/env python3
"""Evaluates Client App.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""

# Constants -------------------------------------------------------------------
import argparse
import atexit
import contextlib
import json
import logging
import os
import pickle
import random
import select
import shutil
import subprocess
import sys
import time
from typing import List
from unittest.mock import patch, Mock

import numpy

from data_provider import DataProvider
from eval import shared as shd
from eval.shared import lb
from lib import config, helpers, logging as logg
from lib import db_cli as db
from lib.base_client import UserType, ServerType
from lib.key_server_backend import KeyServer
from lib.record import Record
from lib.similarity_metrics import map_metric

DEBUG = False
LOGLVL = logging.INFO
SLEEP_TIME = 4 if DEBUG else 10
TIME_PER_MATCH = 10  # s (Observed on Preserver)
EXEC_TIME_OFFSET = 2 * 3600  # s Time for matching mainly
DIRECTORY = config.EVAL_DIR + "client" + "/"
os.makedirs(DIRECTORY, exist_ok=True)
ROUNDS = 10
NUM_MATCHES = range(0, 1001, 100)
# Default values
REC_LEN = 100
REC_ID_LEN = 10
REC_ROUND = [3 for _ in range(REC_ID_LEN)]
PSI = True
METRIC = "relOffset-0.3"  # 0.3 with PSI, 1 for Bloom Only
TLS = config.OT_TLS
MODE = "RANDOM"
if config.OT_TLS or config.PSI_TLS:
    raise RuntimeError("TLs should be disabled.")
log = logg.configure_root_loger(LOGLVL,
                                config.WORKING_DIR + 'data/client_eval.log')
atexit.register(shutil.rmtree, config.TEMP_DIR, True)
# -----------------------------------------------------------------------------


def write_header(file_path: str, row_fmt: str):
    """Write header into csv File."""
    with open(file_path, 'w') as fd:
        fd.write("------------------------HEADER------------------------\n")
        fd.write(f"MODE: {MODE}\n")
        fd.write(f"TLS: {TLS}\n")
        fd.write(f"Metric: {METRIC}\n")
        fd.write(f"Num Matches: {NUM_MATCHES}\n")
        fd.write(f"\n")
        fd.write(f"Bloom Capacity: {config.BLOOM_CAPACITY:,}\n")
        fd.write(f"Bloom Error Rate: {config.BLOOM_ERROR_RATE}\n")
        fd.write(f"Parallel Matching: {config.PARALLEL}\n")
        fd.write(f"\n")
        fd.write(f"OT Malicious Secure: {config.OT_MAL_SECURE}\n")
        fd.write(f"OT TLS: {config.OT_TLS}\n")
        fd.write(f"OT Setsize/Number of keys: {config.OT_SETSIZE:,}\n")
        fd.write(f"Hash Key Length: {config.HASHKEY_LEN}\n")
        fd.write(f"Encryption Key Length: {config.ENCKEY_LEN}\n")
        fd.write(f"\n")
        fd.write(f"PSI Mode: {PSI}\n")
        if PSI:
            fd.write(f"PSI Index Length: {config.PSI_INDEX_LEN}\n")
            fd.write(f"PSI Setsize: {config.PSI_SETSIZE:,}\n")
            fd.write(f"PSI Scheme: {config.PSI_SCHEME}\n")
            fd.write(f"PSI TLS: {config.PSI_TLS}\n")
        fd.write(f"\n")
        fd.write(f"Record Length: {REC_LEN}\n")
        fd.write(f"Record ID Length: {REC_ID_LEN}\n")
        fd.write(f"Record Rounding: {REC_ROUND}\n")
        fd.write(f"\n")
        fd.write(f"Rounds: {ROUNDS}\n")
        fd.write(f"Interval of RAM measurements: {config.RAM_INTERVAL}s\n")
        fd.write(f"All times in Seconds! Timer start with 'StartTime' and is "
                 f"monotonic clock. Only differences are meaningful.\n")
        fd.write(f"{row_fmt}\n")
        fd.write("----------------------END-HEADER----------------------\n")


def compute_matches(t: List[float], num: int) -> List[Record]:
    """
    Compute matching vectors around the target.
    :param num: # of matches
    :param t: Target record
    :return: List of matching records
    """
    metric, ars = map_metric(METRIC)
    m = metric(t, *ars)
    for i in numpy.arange(0.1, ars[0], 0.1):
        m = metric(t, float(i))
        if len(m) > 2 * num:
            break
    candidates = list(m)
    random.shuffle(candidates)
    candidates = candidates[:num]
    if len(candidates) < num:
        raise RuntimeError("Not enough candidates!")
    log.info(f"Generated {len(candidates)} candidates.")
    return [Record(v) for v in candidates]


def kill_bg_servers():
    """Kill old processes if running"""
    subprocess.run(["tmux", "kill-session", "-t", "eval"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "celery"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


atexit.register(kill_bg_servers)


def preparation(num_matches, target, id_len, rounding):
    """Prepare databases and start background tasks."""
    # Kill old processes if running
    kill_bg_servers()
    time.sleep(SLEEP_TIME)

    data_dir = config.DATA_DIR

    log.info("Removing Databases.")
    with contextlib.suppress(FileNotFoundError):
        # Remove Bloom Filter
        os.remove(data_dir + config.BLOOM_FILE)
        # Remove Databases
        os.remove(data_dir + config.KEYSERVER_DB)
        os.remove(data_dir + config.STORAGE_DB)

    # Add User
    log.info("Prepare User DB.")
    db.main(UserType.CLIENT, ['testuser', 'password', '-a'], no_print=True)
    db.main(UserType.OWNER, ['testprovider', 'password', '-a'], no_print=True)

    log.info("Starting Background Servers.")
    subprocess.run([f"{config.WORKING_DIR}src/allStart.sh", "eval"])
    time.sleep(SLEEP_TIME)

    # Create data provider client
    d = DataProvider('testprovider')
    d.set_password('password')

    # Check that servers are really online
    tries = 0
    done = False
    while not done:
        try:
            if tries >= 1:
                # Try to start servers again.
                kill_bg_servers()
                time.sleep(SLEEP_TIME)
                subprocess.run(
                    [f"{config.WORKING_DIR}src/allStart.sh", "eval"])
                time.sleep(SLEEP_TIME)
                tries = 0
            # Check Key Server
            d.get_token(ServerType.KeyServer)
            # Check celery
            r = d.get(d.KEYSERVER.replace('provider', 'celery'))
            if r.content != b"True":
                raise RuntimeError("Celery of keyserver not started.")
            # Check Storage Server
            d.get_token(ServerType.StorageServer)
            # Check celery
            r = d.get(d.STORAGESERVER.replace('provider', 'celery'))
            if r.content != b"True":
                raise RuntimeError("Celery of storage-server not started.")
            # Success
            done = True
        except Exception as e:
            log.error(f"Server not up, yet. Try: {tries}. Error: {str(e)}")
            tries += 1
            time.sleep(5)

    k = KeyServer()

    def get_enc_keys(indices: List[int]):
        """Mock OT for performance."""
        keys = k._enc_keys
        return [keys[i] for i in indices]

    m1 = Mock(return_value=k.get_hash_key())
    with patch.object(d, "_get_enc_keys", get_enc_keys), \
            patch.object(d, "get_hash_key", m1), \
            patch("lib.config.RECORD_ID_LENGTH", id_len), \
            patch("lib.config.RECORD_LENGTH", len(target)), \
            patch("lib.config.ROUNDING_VEC", rounding):
        # Add Records
        if MODE == "IKV":
            d.store_from_file(f"{config.WORKING_DIR}data/ikv_data.txt")
        elif MODE == "WZL":
            d.store_from_file(f"{config.WORKING_DIR}data/wzl_data.txt")
        elif num_matches == 0:
            # No need to store anything
            pass
        else:
            start = time.monotonic()
            matches = compute_matches(target, num_matches)
            log.info(f"Dummy Record Computation took:"
                     f"{str(time.monotonic() - start)}")
            d.store_records(matches)


def start(com_file: str, target: List[float]) -> subprocess.Popen:
    """Start a client App process and return it."""
    cmd = ["python3", "client.py", "testuser", "password", "-r", str(target),
           "-m", METRIC, "-e", com_file]
    if DEBUG:
        cmd.append('-vv')
    if PSI:
        cmd.append("--psi")  # Measure PSI, too.
    proc = subprocess.Popen(cmd, universal_newlines=True,
                            stderr=subprocess.PIPE)
    #                         , stdout=subprocess.PIPE)
    return proc


def main(base_filename: str, resume: bool = False):
    """Execute evaluaiton."""
    file_path = DIRECTORY + base_filename + ".csv"
    ram_path = DIRECTORY + base_filename + '_ram.csv'
    row_fmt = (f"TIMESTAMP;"
               f"ROUND;"
               f"#BloomMatches;"
               f"#PSIMatches;"
               f"#Matches;"
               f"#Results;"
               f"StartTime[s];"
               f"CandidateComputationTime[s];"
               f"HashKeyTime[s];"
               f"PSIPreparationTime[s];"
               f"PSIExecutionTime[s];"
               f"PSISetConstructionTime[s];"
               f"BloomFilterRetrievalTime[s];"
               f"MatchingTime[s];"
               f"KeyRetrievalTime(OT)[s];"
               f"RecordRetrievalTime[s];"
               f"DecryptionTime[s];"
               f"FromKS[Byte];FromKS[Pkt];"
               f"ToKS[Byte];ToKs[Pkt];"
               f"FromSS[Byte];FromSS[Pkt];"
               f"ToSS[Byte];ToSS[Pkt];"
               f"ToOTSvr[Byte];ToOTSvr[Pkt];"
               f"FromOTSvr[Byte];FromOTSvr[Pkt];"
               f"ToPSISvr[Byte];ToPSISvr[Pkt];"
               f"FromPSISvr[Byte];FromPSISvr[Pkt];"
               f"Error")
    if not resume or not os.path.exists(file_path):
        write_header(file_path, row_fmt)
        row_fmt = "TIMESTAMP;ROUND;MATCHES;json.dumps(ram_usage)"
        write_header(ram_path, row_fmt)
    for r in lb(range(ROUNDS), "Rounds", leave=True):
        failed = True
        for m in lb(NUM_MATCHES, "Matches", leave=True):
            success = False
            while not success:
                # Reset config file
                shd.reset_config()
                # Configuration
                shd.set_rounding(REC_ROUND)
                shd.set_rec_id_len(REC_ID_LEN)
                shd.set_total_rec_len(REC_LEN)

                log.info("Doing Preparation.")
                # comp Target
                if MODE == "WZL":
                    target = [1, 2.2, 60.0, 20.0, 60.0, 20.0, 60.0, 20.0,
                              1, 1, 2, 22.5, 23.6, 30.2, 1, 1, 40.0, 165.0, 0.08]
                elif MODE == "IKV":
                    target = [12732.0, 12496.0, 0.20453525295926794, 12496.949, 1.962849116, 2.0, 2.0, 56.4, 1.019, 28.73374196, 1.0, 1.072714416,
                              0.257196124, 0.628290524, 4.359, 4.359, 2.435, 1.0, 1.0, 23.0, 36.0, 101.0567, 173.0, 226.0, 26.0, 4.9, 18.3, 10.782]
                else:
                    target = [float(i + 2) for i in range(REC_LEN)]
                preparation(m, target, REC_ID_LEN, REC_ROUND)
                failed = False
                tempfiles = []
                process = None
                com_file = helpers.get_temp_file() + '_comfile.pyc'
                e = None
                # May be deleted by clean-up of prev. round
                os.makedirs(config.TEMP_DIR, exist_ok=True)
                try:
                    error = ""
                    # Start data measurements
                    tks, tks_file = helpers.start_trans_measurement(
                        config.KEY_API_PORT, direction="dst", sleep=False
                    )
                    fks, fks_file = helpers.start_trans_measurement(
                        config.KEY_API_PORT, direction="src", sleep=False
                    )
                    tss, tss_file = helpers.start_trans_measurement(
                        config.STORAGE_API_PORT, direction="dst", sleep=False
                    )
                    fss, fss_file = helpers.start_trans_measurement(
                        config.STORAGE_API_PORT, direction="src", sleep=False
                    )
                    tempfiles = [tks_file, fks_file, tss_file, fss_file]
                    measurements = [tks, fks, tss, fss]
                    time.sleep(0.5)

                    longest_exec_time = TIME_PER_MATCH * m + \
                                        EXEC_TIME_OFFSET  # s
                    start_runtime = time.monotonic()
                    process = start(com_file, target)
                    # Check if client socket hangs
                    poll_err = select.poll()
                    poll_err.register(process.stderr,
                                      select.POLLIN)
                    hangs = False
                    ctr = 0
                    while True:
                        try:
                            process.wait(30)
                            # Terminated
                            break
                        except subprocess.TimeoutExpired:
                            ctr += 1
                            total_wait_time = time.monotonic() - start_runtime
                            # if total_wait_time > longest_exec_time:
                            #     raise RuntimeError("Execution time too
                            #     long.")
                            # check if there is something on stderr
                            hang_detected = False
                            while poll_err.poll(0):
                                line = process.stderr.readline().strip()
                                if line != "":
                                    print(f"Read Line: '{line}'")
                                if "client socket connect error" in line:
                                    hang_detected = True
                            if hangs and hang_detected:
                                # Still hangs after 30s. Restart.
                                raise RuntimeError("Client hangs.")
                            hangs = hang_detected

                    # Load com file
                    with open(com_file, "rb") as fd:
                        e = pickle.load(fd)
                    if e['result'] is None:
                        # full_retrieve did not terminate
                        raise RuntimeError(e['error'])
                    result = e['result']
                    ram_usage = e['ram_usage']
                    ot_files_sent = e['ot_tcpdump_sent']
                    ot_files_recv = e['ot_tcpdump_recv']
                    psi_files_sent = e['psi_tcpdump_sent']
                    psi_files_recv = e['psi_tcpdump_recv']

                    # Kill TCPDUMP
                    helpers.kill_tcpdump()
                    for proc in measurements:
                        # Wait for termination
                        proc.wait(30)

                    # Get Data Amount results
                    fks_byte, fks_pkt = helpers.read_tcpstat_from_file(
                        fks_file)
                    tks_byte, tks_pkt = helpers.read_tcpstat_from_file(
                        tks_file)
                    fss_byte, fss_pkt = helpers.read_tcpstat_from_file(
                        fss_file)
                    tss_byte, tss_pkt = helpers.read_tcpstat_from_file(
                        tss_file)

                    # Check files exist
                    if e['num_matches'] > 0 and (len(ot_files_sent) == 0 or
                                                 len(ot_files_recv) == 0):
                        raise RuntimeError(
                            'OT executed but no pcap files available.')

                    if (len(psi_files_recv) == 0 or
                            len(psi_files_sent) == 0) and PSI:
                        raise RuntimeError(
                            'PSI executed but no pcap files available.')

                    if (MODE == "RANDOM" and e['num_matches'] != m) or (
                            MODE == "IKV" and len(result) != m) or (
                            MODE == "WZL" and len(result) != m):
                        s = (f"Mismatch of number matches. Expected: {m}"
                             f" Got: {e['num_matches']}")
                        error += s
                        log.error(s)

                    # Get OT Transmission info
                    ot_byte_sen = 0
                    ot_pkt_sen = 0
                    ot_byte_rec = 0
                    ot_pkt_rec = 0
                    for file in ot_files_sent:
                        b, pkt = helpers.read_tcpstat_from_file(file)
                        ot_byte_sen += b
                        ot_pkt_sen += pkt
                        os.remove(file)
                    for file in ot_files_recv:
                        b, pkt = helpers.read_tcpstat_from_file(file)
                        ot_byte_rec += b
                        ot_pkt_rec += pkt
                        os.remove(file)

                    # Get PSI Transmission info
                    psi_byte_sen = 0
                    psi_pkt_sen = 0
                    psi_byte_rec = 0
                    psi_pkt_rec = 0
                    for file in psi_files_sent:
                        b, pkt = helpers.read_tcpstat_from_file(file)
                        psi_byte_sen += b
                        psi_pkt_sen += pkt
                        os.remove(file)
                    for file in psi_files_recv:
                        b, pkt = helpers.read_tcpstat_from_file(file)
                        psi_byte_rec += b
                        psi_pkt_rec += pkt
                        os.remove(file)

                    with open(file_path, "a") as fd:
                        row = ";".join((
                            time.strftime('%Y-%m-%d %H:%M:%S'),
                            str(r),
                            str(e['bloom_matches']),
                            str(e['psi_matches']),
                            str(e['num_matches']),
                            str(len(result)),
                            str(e['start_time']),
                            str(e['compute_candidates_time']),
                            str(e['hash_key_time']),
                            str(e['psi_preparation_time']),
                            str(e['psi_execution_time']),
                            str(e['psi_set_construction_time']),
                            str(e['bloom_filter_retrieve_time']),
                            str(e['bloom_matching_time']),
                            str(e['key_retrieve_time']),
                            str(e['record_retrieve_time']),
                            str(e['decryption_time']),
                            str(fks_byte),
                            str(fks_pkt),
                            str(tks_byte),
                            str(tks_pkt),
                            str(fss_byte),
                            str(fss_pkt),
                            str(tss_byte),
                            str(tss_pkt),
                            str(ot_byte_sen),
                            str(ot_pkt_sen),
                            str(ot_byte_rec),
                            str(ot_pkt_rec),
                            str(psi_byte_sen),
                            str(psi_pkt_sen),
                            str(psi_byte_rec),
                            str(psi_pkt_rec),
                            error
                        ))
                        fd.write(f"{row}\n")
                    with open(ram_path, 'a') as fd:
                        fd.write(
                            ';'.join(
                                (
                                    time.strftime('%Y-%m-%d %H:%M:%S'),
                                    str(r),
                                    str(m),
                                    json.dumps(ram_usage)
                                )
                            ) + '\n'
                        )
                    success = True
                except Exception as e:
                    log.exception(str(e))
                    success = False
                    failed = True  # Restart server
                finally:
                    # Reset config file
                    shd.reset_config()
                    # Clean Up
                    if process is not None:
                        process.terminate()
                        try:
                            process.wait(5)
                        except subprocess.TimeoutExpired:
                            # Terminate was not enough
                            process.kill()
                    # Kill TCPDUMP
                    helpers.kill_tcpdump()
                    # Remove Tempfiles
                    shutil.rmtree(config.TEMP_DIR, ignore_errors=True)


def get_client_parser() -> argparse.ArgumentParser:
    """Return an argparser for the client eval."""
    parser = argparse.ArgumentParser(description="Client Eval")
    parser.add_argument('-m', "--metric", help="Name of similarity metric",
                        type=str, action="store", default=METRIC)
    parser.add_argument('-r', '--reps', help="Rounds", action='store',
                        default=ROUNDS, type=int)
    parser.add_argument('-n', '--num', help="# Matches", action='store',
                        default=NUM_MATCHES,
                        type=int)
    parser.add_argument('-o', '--out', type=str, action='store',
                        help="Base filename WITHOUT file-ending!",
                        required=True)
    parser.add_argument('--resume', action="store_true",
                        help="Append to file.",
                        default=False)
    parser.add_argument('-p', "--psi", help="Also evaluate PSI.",
                        action="store_true", default=False)
    action_group = parser.add_mutually_exclusive_group(required=False)
    action_group.add_argument('--wzl1', action='store_true',
                              help='Use WZL Data.')
    action_group.add_argument('--wzl2', action='store_true',
                              help='Use WZL Data.')
    action_group.add_argument('--ikv', action='store_true',
                              help='Use IKV Data.')
    action_group.add_argument('--random', action='store_true',
                              help='Use Random Data.')
    return parser


if __name__ == '__main__':
    if not config.EVAL:
        log.error("config.EVAL has to be True.")
        sys.exit(-1)
    log.setLevel(LOGLVL)
    p = get_client_parser()
    args = p.parse_args()
    ROUNDS = args.reps
    METRIC = args.metric
    NUM_MATCHES = args.num
    PSI = args.psi
    if args.wzl1 or args.wzl2:
        MODE = "WZL"
        PSI = True
        REC_LEN = 19
        REC_ID_LEN = 17
        REC_ROUND = [0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 3, 0, 0, 3]
        if args.wzl1:
            METRIC = "wzl1"
            NUM_MATCHES = 10
        elif args.wzl2:
            METRIC = "wzl2"
            NUM_MATCHES = 6
    elif args.ikv:
        MODE = "IKV"
        PSI = False
        REC_LEN = 28
        REC_ID_LEN = 21
        REC_ROUND = [2 for _ in range(REC_ID_LEN)]
        METRIC = "relOffset-3"
        NUM_MATCHES = 77
    else:
        MODE = "RANDOM"
        PSI = True
        # Use above default values
        REC_LEN = 100
        REC_ID_LEN = 10
        REC_ROUND = [3 for _ in range(REC_ID_LEN)]
    main(args.out, args.resume)
