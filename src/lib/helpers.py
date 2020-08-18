#!/usr/bin/env python3
"""This module contains small helper functions.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import base64
import logging
import multiprocessing
import os
import platform
import random
import re
import socket
import ssl
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from io import StringIO
from typing import List, Tuple

import lib.config as config

log: logging.Logger = logging.getLogger(__name__)


def get_temp_file() -> str:
    """Generate random tempfile and create directory if not exits."""
    return config.TEMP_DIR + str(uuid.uuid4())


def queue_to_list(q: multiprocessing.Queue) -> list:
    """
    Convert a multiprocessing.Queue into a list.
    :param q: mp.Queue
    :return: Queue converted to list.
    """
    result = []
    q.put('STOP')
    for i in iter(q.get, 'STOP'):
        result.append(i)
    return result


def start_trans_measurement(
        port: int, protocol: str = None,
        direction: str = "both",
        sleep: bool = True,
        file=None) -> (
        subprocess.Popen, str):  # pragma no cover
    """
    Measure transmitted data on port.
    :param file: File to write pcap to. If undef. a tempfile is used
    :param sleep: Attention: Short manual sleep required (0.01s)
    :param port: Port to listen on
    :param protocol: [OPTIONAL] Protocol to listen for, otherwise all
    :param direction: [OPTIONAL] € {src, dst}
    :return: Popen object that can be given to stop_trans_measurement
    """
    """
    TCPSTAT Command:
    -i Interface. Loopback 'lo' for Linux and 'lo0' for Mac
    -f FilterRule. See TCPDUMP.
    -o Output Format.  %N = # Bytes, %n = # packets
    -1 Measure until termination
    sudo tcpstat -i lo -f "dst port 1213 and tcp" -o "b=%N\np=%n\n" -1
    """
    # TCPSTAT -----------------------------------------------------------------
    # if platform.system() == "Darwin":  # pragma no cover
    #     interface = 'lo0'
    #     base_cmd = ["tcpstat"]
    # else:  # pragma no cover
    #     interface = 'lo'
    #     base_cmd = ["sudo", "tcpstat"]
    # if direction == "both":
    #     flt = f"(dst port {port} or src port {port})"
    # else:
    #     flt = f"({direction} port {port})"
    # if protocol is not None:
    #     flt += f" and {protocol}"
    # log.debug(f"Starting transmission measurement: {flt}")
    # out_fmt = 'B=%N:p=%n'
    # cmd = base_cmd + ["-i", f"{interface}",
    #                   "-f", f"{flt}", "-o", f"{out_fmt}", "-1"]
    # s = subprocess.Popen(cmd, stdout=subprocess.PIPE,
    #                      stderr=subprocess.PIPE)
    # -------------------------------------------------------------------------
    # Use TCPDUMP because of issue on butthead
    if file is None:
        file = get_temp_file()
    if platform.system() == "Darwin":  # pragma no cover
        interface = 'lo0'
    else:  # pragma no cover
        interface = 'lo'
    cmd = ['sudo', 'tcpdump', '-i', interface, '-w', file, '-U',
           '--immediate-mode']
    # -U is no buffer
    if direction != 'both':
        cmd.append(direction)
    cmd.extend(['port', str(port)])
    if protocol is not None:
        cmd.append('and')
        cmd.append(str(protocol))
    log.debug(f"Starting transmission measurement: f{str(cmd)}")
    s = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    if sleep:
        time.sleep(0.01)
    return s, file


def read_tcpstat_from_file(file: str) -> (int, int):  # pragma no cover
    """
    Read transmitted bytes and packets from pcap file.
    :param file:
    :return:
    """
    out_fmt = 'B=%N:p=%n'
    s = subprocess.run(["tcpstat", "-r", file, "-o", f"{out_fmt}", "-1"],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    out = s.stdout
    try:
        m = re.search("B=(\d+):p=(\d+)", str(out))
        b = int(m.group(1))
        packets = int(m.group(2))
    except AttributeError:  # pragma no cover
        raise (ValueError("No valid output of TCPSTAT."))
    if b == 0:
        raise RuntimeError("Capturing Packets failed.")
    return b, packets


def kill_tcpdump() -> None:  # pragma no cover
    """
    Kill all TCPDUMP processes with SIGINT signal.
    :return: None
    """
    # Kill tcpdump gracefully
    if platform.system() == "Darwin":
        subprocess.run(["sudo", "pkill", "-2", "tcpdump"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run(["sudo", "killall", "-s", "2", "tcpdump"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def reset_port():  # pragma no cover
    """
    Removes artifical latency and bandwidth limits
    from the port or from all ports [Linux only]
    # :param port: Only remove latency of one port
    :return:
    """
    # if port is None:
    log.debug("Reset Latency and Rate for all ports.")
    s = subprocess.Popen(["sudo", "tcdel", "lo", "--all"],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = s.communicate()
    # Error msg if there is no rule set.
    # if err != b'':
    #     log.warning(str(err))
    # else:
    #     log.debug(f"Reset Latency and Rate for port {port}.")
    #     subprocess.run(["sudo", "tcdel", "lo", "--port", str(port)],
    #                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    #     subprocess.run(["sudo", "tcdel", "lo", "--src-port", str(port)],
    #                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def add_latency(latency: int):  # pragma no cover
    """
    Adds latency to the defined port. [Linux only]
    :param latency: Amount of latency in ms
    :return:
    """
    log.debug(f"Set Latency of {latency}ms for all ports.")
    s = subprocess.Popen(
        ["sudo", "tcset", "lo", "--delay",
         f"{latency}ms"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = s.communicate()
    if err != b'':
        log.warning(str(err))


def add_bandwidth(bw: int) -> None:  # pragma no cover
    """Limit bandwidth.
    :param bw: Bandwidth in kbit/s
    :return: None
    """
    log.debug(f"Set  bandwidth of {bw}kbit/s for all ports.")
    s = subprocess.Popen(
        ["sudo", "tcset", "lo", "--rate", f"{bw}kbit/s"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = s.communicate()
    if err != b'':
        log.warning(str(err))


def add_async_bandwidth(bw: int, port: int) -> None:  # pragma no cover
    """
    Limit bandwith with ratio 1:10.
    :param port: Port to apply restriction to (assumed to be server)
    :param bw: Downrate
    :return:
    """
    # Upload
    cmd = ["sudo", "tcset", "--add", "lo", "--rate", f"{int(bw/10)}kbit/s",
           "--dst-port", str(port)]
    # log.info(f"Execute: {str(cmd)}")
    s = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = s.communicate()
    if err != b'':
        log.warning(str(err))
    # Download
    cmd = ["sudo", "tcset", "--add", "lo", "--rate", f"{int(bw)}kbit/s",
           "--src-port", str(port)]
    # log.info(f"Execute: {str(cmd)}")
    s = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = s.communicate()
    if err != b'':
        log.warning(str(err))


def to_base64(b: bytes) -> str:
    """
    Transfer a bytes object to a Base64 encoded string for transmission.
    :param b: The bytes object to transmit
    :return: Base64 encoded string for transmission
    """
    return base64.b64encode(b).decode()


def from_base64(b64: str) -> bytes:
    """
    Convert as Base64 encoded string back into the bytes object.
    :param b64: Base64 encoded string
    :return: Bytes object
    """
    return base64.b64decode(b64.encode())


def encryption_keys_from_int(in_list: List[int]) -> List[bytes]:
    """
    Convert a list of integers into 128 Bit encryption keys
    :param in_list: List of Integers to be converted
    :return: List of bytes
    """
    return [
        i.to_bytes(128 // 8, 'big')
        for i in in_list
    ]


def keys_to_int(keys: List[bytes]) -> List[int]:
    """
    Convert a list of bytes encryption keys to integers
    :param keys: List of encryption keys as bytes objects
    :return: List of Integers
    """
    return [
        int.from_bytes(i, 'big') for i in keys]


@contextmanager
def captured_output():
    """Capture outputs to StdOut and StdErr."""
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def create_data_dir(data_dir: str) -> None:
    """Create the data directory and a contained log directory if it does
    not exists, yet."""
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(data_dir + '/logs/', exist_ok=True)


def parse_list(string: str) -> List[float]:
    """Convert a string list into a list object."""
    r_list = string.strip('][\n').split(',')
    r_list = [float(i) for i in r_list]
    return r_list


def get_tls_context(cert: str, key: str) -> ssl.SSLContext:
    """Return an SSL Context with high security level"""
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_dh_params(config.TLS_CERT_DIR + 'dhparam.pem')
    context.set_ecdh_curve('secp384r1')
    context.set_ciphers('AES256+EDH:AES256+EECDH')
    context.load_cert_chain(cert, key)
    return context


def port_free(port: int) -> bool:
    """
    Return True if port can be used.
    https://docs.python.org/2/library/socket.html#example
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', port))  # Try to open port
    except OSError as e:
        if e.errno is 98 or e.errno is 48:  # Errno 98 means address already
            # bound
            s.close()
            return False
        raise e  # pragma no cover
    except Exception as e:
        s.close()
        raise e
    s.close()
    return True


def get_free_port() -> int:
    """
    Return a free port.
    :return: Available port
    """
    while True:
        port = random.randint(1024, 65535)
        if port_free(port):
            return port


def generate_auth_header(user: str, token: str) -> List[Tuple[str, str]]:
    """Generate a valid HTTPBasicAuth Header for the given username and
    password."""
    b64: bytes = base64.b64encode(bytes(f"{user}:{token}",
                                        encoding='UTF-8'))
    return [('Authorization', f'Basic {b64.decode()}')]


def print_time(t: float) -> str:
    """Convert time to human readable representation.
    :param t: Time in seconds.
    :return: String representation
    """
    t = t * 1000  # to ms
    if t < 1000:
        return f"{round(t, 2)}ms"
    elif t < 60000:
        return f"{round(t / 1000, 2)}s"
    elif t < 3600000:
        sec = t / 1000
        minute = int(sec // 60)
        sec = sec % 60
        return f"{minute}min {round(sec, 2)}s"
    else:
        sec = t / 1000
        minute = sec // 60
        sec = sec % 60
        h = int(minute // 60)
        minute = int(minute % 60)
        return f"{h}h {minute}min {round(sec, 2)}s"
