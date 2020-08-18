#!/usr/bin/env python3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
from cOTInterface import PyOTSender
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cython_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)

print("Sender: Starting.")

send = PyOTSender()
send.totalOTs = 10
send.numChosenMsgs = 2 ** 10  # max 2^25 60+s
send.hostName = "127.0.0.1"
send.port = 1213
send.serverCert = f"{cython_dir}/certs/keyserver.crt"
send.serverKey = f"{cython_dir}/certs/keyserver.key"

print("numChosenMsgs: " + str(send.numChosenMsgs))
print("totalOTs: " + str(send.totalOTs))

messages = []
for y in range(send.numChosenMsgs):
    messages.append(y)

print("Sender (KKRT16): Execute without "
      "TLS------------------------------------------------------")
send.executeSame(messages, False)
print("Sender (KKRT16): Execute with "
      "TLS---------------------------------------------------------")
send.executeSame(messages, True)
send.maliciousSecure = True
send.inputBitCount = 76
print("Sender (OOS16): Execute without "
      "TLS------------------------------------------------------")
send.executeSame(messages, False)
print("Sender (OOS16): Execute with "
      "TLS---------------------------------------------------------")
send.executeSame(messages, True)
