#!/usr/bin/env python3
"""This module tests the TLS Handshake and Record Protocol Performance.
Start echo_server.sh in another terminal.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import argparse
import os
import socket
import ssl
import time

from tqdm import tqdm

# CONSTANTS -------------------------------------------------------------------
# You may have to adapt the constants in echo_server.sh accordingly
HOST = "127.0.0.1"
PORT = 5000
REPS = 10000
CURVES = ["prime256v1"]  # secp256r1 is called prime256v1 in OpenSSL
CIPHERS = [
    "ECDHE-RSA-AES256-GCM-SHA384",
    # "ECDHE-ECDSA-AES256-GCM-SHA384",  # Not working on Preserver
    "DHE-RSA-AES256-GCM-SHA384",

]
SENT_BYTES = 10 * 10 ** 6  # 10MB
PROTOCOL = ssl.PROTOCOL_TLSv1_2
# -----------------------------------------------------------------------------
# DIRECTORIES -----------------------------------------------------------------
_cur_dir = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
WORKING_DIR = os.path.abspath(_cur_dir) + '/'
DATA_DIR = WORKING_DIR + 'data/'
TLS_CERT_DIR = DATA_DIR + "certs/"
ROOT_CA = TLS_CERT_DIR + "rootCA.crt"
EVAL_DIR = WORKING_DIR + 'eval/'
output_dir = EVAL_DIR + "tls/"


# -----------------------------------------------------------------------------

def main(base_filename: str):
    for cipher in CIPHERS:
        for curve in CURVES:
            print("Testing cipher\033[1m", cipher, "\033[0m with curve\033[1m",
                  curve, "\033[0m.")
            # TLS
            # SETTINGS-----------------------------------------------------------------
            context = ssl.SSLContext(PROTOCOL)
            context.verify_mode = ssl.CERT_REQUIRED
            context.check_hostname = True  # Required for CERT_REQUIRED
            context.load_verify_locations(ROOT_CA)
            context.set_ecdh_curve(curve)
            context.set_ciphers(cipher)
            # -----------------------------------------------------------------------------
            send_times = []
            hs_times = []
            used_cipher = ""
            used_protocol = ""
            sent_bytes = SENT_BYTES  # 10MB
            # recv_bytes = 10 * 10 ** 6 - 10000  # sent_bytes
            data = b'1' * sent_bytes

            for _ in tqdm(range(REPS)):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = context.wrap_socket(
                    s, server_hostname='localhost',
                    do_handshake_on_connect=False)
                ssl_sock.connect((HOST, PORT))
                start = time.monotonic()
                ssl_sock.do_handshake(block=True)
                handshake_time = time.monotonic() - start
                hs_times.append(handshake_time)
                # print("Handshake: ", handshake_time * 1000, "ms")
                # print("Used Cipher: ", ssl_sock.cipher())
                used_cipher = ssl_sock.cipher()[0]
                used_protocol = ssl_sock.version()
                # print("Supported Ciphers: ", ssl_sock.shared_ciphers())

                start = time.monotonic()
                ssl_sock.send(data)
                send_time = time.monotonic() - start
                send_times.append(send_time)

                # time.sleep(1)
                # read_bytes = 0
                # start = time.monotonic()
                # while read_bytes < recv_bytes:
                #     read = ssl_sock.recv(recv_bytes)
                #     read_bytes += len(read)
                # recv_time = time.monotonic() - start

            print(
                "###########################################################")
            print("Used Protocol:\033[1m", used_protocol, "\033[0m")
            print("Used Cipher: \033[1m", used_cipher, "\033[0m")
            print("Used Curve: \033[1m", curve, "\033[0m",
                  "[Note: secp256r1 is called prime256v1 in OpenSSL]")
            print("Rounds: \033[1m", REPS, "\033[0m")
            print("Transmitted Data: \033[1m", sent_bytes / 1000000, "MB",
                  "\033[0m")
            avg_hs = sum(hs_times) / REPS
            print("Average Handshake: \033[1m", round(avg_hs * 1000, 2), "ms",
                  "\033[0m")
            avg_send = sum(send_times) / REPS
            print("Average Sending: \033[1m", round(avg_send * 1000, 2), "ms",
                  "\033[0m")
            print("Average Sending: \033[1m",
                  round(sent_bytes / avg_send / 1000000, 2), "MB/s", "\033[0m")

            # Write to file
            if base_filename is not None:
                os.makedirs(output_dir, exist_ok=True)
                filename = f"{base_filename}_{cipher}_{curve}.csv"
                with open(output_dir + filename, "w") as f:
                    f.write(
                        "------------------------HEADER------------------------;;;;;;\n")
                    f.write(f"Protocol: {used_protocol};;;;;;\n")
                    f.write(f"Cipher: {used_cipher};;;;;;\n")
                    f.write(
                        f"Curve: {curve} [Note: secp256r1 is called "
                        f"prime256v1 in OpenSSL];;;;;;\n")
                    f.write(f"Rounds: {REPS};;;;;;\n")
                    f.write(
                        f"Transmitted Data per Measurement: "
                        f"{sent_bytes / 1000000}MB;;;;;;\n")
                    f.write(
                        f"Average Handshake Duration: "
                        f"{round(avg_hs * 1000, 2)}ms;;;;;;\n")
                    f.write(
                        f"Average Sending: "
                        f"{round(sent_bytes / avg_send / 1000000, 2)}MB/s;;;;;;\n")
                    f.write(
                        "----------------------END-HEADER----------------------;;;;;;\n")
                    f.write(
                        "ROUND;PROTOCOL;CIPHER;CURVE;SENT_DATA["
                        "Byte];HANDSHAKE[s];SENDING[s]\n")
                    for i, _ in enumerate(hs_times):
                        f.write(
                            f"{i + 1};{used_protocol};{used_cipher};{curve};{SENT_BYTES};{hs_times[i]};{send_times[i]}\n")


if __name__ == '__main__':
    p = argparse.ArgumentParser("TLS Client.")
    p.add_argument('-o', '--out', type=str, action='store',
                   help="Base Filename", default=None)
    args = p.parse_args()
    main(args.out)
