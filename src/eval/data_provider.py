#!/usr/bin/env python3
"""Evaluates Data Provider App.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
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
from typing import List, Iterable

from data_provider import DataProvider
from eval import shared as shd
from eval.shared import lb
from lib import config, helpers, logging as logg
from lib import db_cli as db
from lib.base_client import UserType, ServerType

# Constants -------------------------------------------------------------------
LOGLVL = logging.INFO
TIME_PER_UPLOAD = 10  # s
TIME_OFFSET = 100
DIRECTORY = config.EVAL_DIR + "provider" + "/"
os.makedirs(DIRECTORY, exist_ok=True)
DIFF = 100  # Maximal difference each entry of the records may have from target
ROUNDS = 10
NUM_UPLOADS = [1] + list(range(100, 1001, 100))
REC_LEN = 100
REC_ID_LEN = 10
REC_ROUND = [3 for _ in range(REC_ID_LEN)]
TLS = config.OT_TLS
MODE = "RANDOM"
log = logg.configure_root_loger(
    LOGLVL, config.WORKING_DIR + 'data/dp_eval.log')
atexit.register(shutil.rmtree, config.TEMP_DIR, True)
if config.OT_TLS or config.PSI_TLS:
    raise RuntimeError("TLs should be disabled.")
# -----------------------------------------------------------------------------


def write_header(file_path: str, row_fmt: str):
    """Write header into csv File."""
    with open(file_path, 'w') as fd:
        fd.write("------------------------HEADER------------------------\n")
        fd.write(f"MODE: {MODE}\n")
        fd.write(f"TLS: {TLS}\n")
        # fd.write(f"Target: {TARGET}\n")
        fd.write(f"Num Uploads (% for Scenario Evals): {NUM_UPLOADS}\n")
        if MODE == "RANDOM":
            fd.write(f"Diffence of each element: {DIFF}\n")
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


def generate_records(t: List[float], num: int) -> Iterable[List[float]]:
    """
    Generate 'num' many vectors based on the target 't'.
    :param num: # of records to generate
    :param t: Target record
    :return: List of matching records
    """
    candidates = (
        [i + random.uniform(0, DIFF) for i in t]
        for _ in range(num)
    )
    log.info(f"Generated {num} records.")
    return candidates


def kill_bg_servers():
    """Kill old processes if running"""
    subprocess.run(["tmux", "kill-session", "-t", "eval"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "celery"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


atexit.register(kill_bg_servers)


def preparation():
    """Prepare databases and start background tasks."""
    # Kill old processes if running
    kill_bg_servers()
    time.sleep(10)

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
    time.sleep(10)
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
                time.sleep(10)
                subprocess.run(
                    [f"{config.WORKING_DIR}src/allStart.sh", "eval"])
                time.sleep(10)
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


def start(filename: str, com_file: str) -> subprocess.Popen:
    """Start a data provider App process and return it.
    :param filename: The file containing the records to upload.
    :param com_file: Communication file.
    :return: The created process
    """
    cmd = ["python3", "data_provider.py", "testprovider", "password", "-f",
           filename, "-e", com_file]
    proc = subprocess.Popen(cmd, universal_newlines=True,
                            stderr=subprocess.PIPE)
    # , stdout=subprocess.PIPE)
    return proc


def main(base_filename: str, resume: bool = False):
    """Execute evaluaiton."""
    file_path = DIRECTORY + base_filename + ".csv"
    ram_path = DIRECTORY + base_filename + '_ram.csv'
    row_fmt = (f"TIMESTAMP;"
               f"ROUND;"
               f"#Uploads;"
               f"TotalRecLen;"
               f"StartTime[s];"
               f"ParseListTime[s];"
               f"HashKeyTime[s];"
               f"HashSetTime[s];"
               f"OTIndexTime[s];"
               f"KeyRetrievalTime(OT)[s];"
               f"SetKeyTime[s];"
               f"EncryptionTime[s];"
               f"SendTime[s];"
               f"FromKS[Byte];"
               f"FromKS[Pkt];"
               f"ToKS[Byte];"
               f"ToKs[Pkt];"
               f"FromSS[Byte];"
               f"FromSS[Pkt];"
               f"ToSS[Byte];"
               f"ToSS[Pkt];"
               f"ToOTSvr[Byte];"
               f"ToOTSvr[Pkt];"
               f"FromOTSvr[Byte];"
               f"FromOTSvr[Pkt];"
               f"SentJSONSize[Length];"
               f"Error")
    if not resume or not os.path.exists(file_path):
        write_header(file_path, row_fmt)
        row_fmt = "TIMESTAMP;ROUND;UPLOADS;TotalRecLen;json.dumps(ram_usage)"
        write_header(ram_path, row_fmt)
    for r in lb(range(ROUNDS), "Rounds", leave=True):
        failed = True
        for m in lb(NUM_UPLOADS, "Uploads", leave=True):
            for rec_len in lb(REC_LEN, "Total Length", leave=False):
                success = False
                # On preserver, the time per upload is approx 1s
                while not success:
                    # Reset config
                    shd.reset_config()
                    # Configuration
                    shd.set_rounding(REC_ROUND)
                    shd.set_rec_id_len(REC_ID_LEN)
                    shd.set_total_rec_len(rec_len)

                    log.info("Doing Preparation.")
                    preparation()
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

                        upload_file = helpers.get_temp_file() + "_upload.txt"
                        if MODE == "IKV" or MODE == "WZL" or MODE == "IKV2":
                            if "IKV" in MODE:
                                source_file = f"{config.WORKING_DIR}data/" \
                                              f"ikv_data.txt"
                            else:
                                source_file = f"{config.WORKING_DIR}data/" \
                                              f"wzl_data.txt"
                            # Only upload m%
                            with open(source_file, "r") as f:
                                lines = f.readlines()
                            num = int(len(lines) / 100 * m)
                            if MODE == "IKV2":
                                # non-random
                                uploads = lines[:num]
                            else:
                                uploads = random.choices(lines, k=num)
                            with open(upload_file, "w") as f:
                                f.writelines(uploads)
                            # Update Value
                            m = num
                        else:
                            recs = generate_records(
                                [float(i + 1) for i in range(rec_len)],
                                m)
                            with open(upload_file, "w") as f:
                                for rec in recs:
                                    f.write(str(rec) + '\n')

                        longest_exec_time = TIME_PER_UPLOAD * m + TIME_OFFSET
                        start_runtime = time.monotonic()
                        process = start(upload_file, com_file)
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
                                if total_wait_time > longest_exec_time:
                                    raise RuntimeError(
                                        "Execution time too long.")
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
                        if e['error'] is not None:
                            raise RuntimeError(e['error'])
                        result = e['result']
                        ram_usage = e['ram_usage']
                        ot_files_sent = e['ot_tcpdump_sent']
                        ot_files_recv = e['ot_tcpdump_recv']

                        # Kill TCPDUMP
                        helpers.kill_tcpdump()
                        for proc in measurements:
                            # Wait for termination
                            proc.wait(30)

                        # Check files exist
                        if m > 0 and (len(ot_files_sent) == 0 or
                                      len(ot_files_recv) == 0):
                            raise RuntimeError(
                                'OT executed but no pcap files available.')

                        # Get Data Amount results
                        fks_byte, fks_pkt = helpers.read_tcpstat_from_file(
                            fks_file)
                        tks_byte, tks_pkt = helpers.read_tcpstat_from_file(
                            tks_file)
                        fss_byte, fss_pkt = helpers.read_tcpstat_from_file(
                            fss_file)
                        tss_byte, tss_pkt = helpers.read_tcpstat_from_file(
                            tss_file)

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

                        with open(file_path, "a") as fd:
                            row = ';'.join((
                                time.strftime('%Y-%m-%d %H:%M:%S'),
                                str(r),
                                str(m),
                                str(rec_len),
                                str(e['start_time']),
                                str(e['parsed_list_time']),
                                str(e['hash_key_time']),
                                str(e['hash_set_time']),
                                str(e['ot_index_time']),
                                str(e['key_retrieve_time']),
                                str(e['set_key_time']),
                                str(e['encryption_time']),
                                str(e['send_time']),
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
                                str(e['json_length']),
                                error
                            ))
                            fd.write(
                                f"{row}\n")
                        with open(ram_path, 'a') as fd:
                            fd.write(
                                ';'.join(
                                    (
                                        time.strftime('%Y-%m-%d %H:%M:%S'),
                                        str(r),
                                        str(m),
                                        str(rec_len),
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
                        # Reset config file
                        shd.reset_config()


def get_client_parser() -> argparse.ArgumentParser:
    """Return an argparser for the client eval."""
    parser = argparse.ArgumentParser(description="Data Provider Eval")
    parser.add_argument('-r', '--reps', help="Rounds", action='store',
                        default=ROUNDS, type=int)
    # parser.add_argument('-n', '--num', help="# records to upload",
    #                     action='store',
    #                     default=NUM_UPLOADS, type=int)
    parser.add_argument('-o', '--out', type=str, action='store',
                        help="Base filename WITHOUT file-ending!",
                        required=True)
    # parser.add_argument('-l', '--length', type=int,
    #                     default=config.RECORD_LENGTH,
    #                     help="Length of randomrecords")
    parser.add_argument('--resume', action="store_true",
                        help="Append to file.",
                        default=False)
    action_group = parser.add_mutually_exclusive_group(required=False)
    action_group.add_argument('--wzl', action='store_true',
                              help='Use WZL Data.')
    action_group.add_argument('--ikv', action='store_true',
                              help='Use IKV Data.')
    action_group.add_argument('--ikv2', action='store_true',
                              help='Use non-random IKV Data.')
    action_group.add_argument('--uploads', action='store_true',
                              help='Use Random Data and vary num uploads.')
    action_group.add_argument('--rec_len', action='store_true',
                              help='Use Random Data and vary record length.')
    action_group.add_argument('--debug', action='store_true',
                              help='Debug Mode.')
    return parser


if __name__ == '__main__':
    if not config.EVAL:
        log.error("config.EVAL has to be True.")
        sys.exit(-1)
    p = get_client_parser()
    args = p.parse_args()
    ROUNDS = args.reps
    # NUM_UPLOADS = args.num
    if args.wzl:
        MODE = "WZL"
        REC_LEN = 19
        REC_ID_LEN = 17
        REC_ROUND = [0, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 3, 0, 0, 3]
        # Upload in Percent
        NUM_UPLOADS = range(10, 101, 10)
    elif args.ikv:
        MODE = "IKV"
        REC_LEN = 28
        REC_ID_LEN = 21
        REC_ROUND = [2 for _ in range(REC_ID_LEN)]
        # Upload in Percent
        NUM_UPLOADS = range(10, 101, 10)
    elif args.ikv2:
        MODE = "IKV2"
        REC_LEN = 28
        REC_ID_LEN = 21
        REC_ROUND = [2 for _ in range(REC_ID_LEN)]
        # Upload in Percent
        NUM_UPLOADS = range(10, 101, 10)
    elif args.uploads:
        MODE = "RANDOM"
        REC_LEN = 100
        REC_ID_LEN = 10
        REC_ROUND = [3 for _ in range(REC_ID_LEN)]
        NUM_UPLOADS = [1] + list(range(100, 1001, 100))
    elif args.rec_len:
        MODE = "RANDOM"
        REC_LEN = list(range(100, 1001, 100))
        REC_ID_LEN = 10
        REC_ROUND = [3 for _ in range(REC_ID_LEN)]
        NUM_UPLOADS = 100
    elif args.debug:
        # Debug
        MODE = "RANDOM"
        REC_LEN = 100
        REC_ID_LEN = 10
        REC_ROUND = [3 for _ in range(REC_ID_LEN)]
        NUM_UPLOADS = list(range(500, 501, 100))
        REPS = 5
    main(args.out, args.resume)
