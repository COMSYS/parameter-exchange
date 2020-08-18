#!/usr/bin/env python3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import datetime
# noinspection PyUnresolvedReferences
from cOTInterface import PyOTReceiver
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cython_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)

print("Receiver: Starting.")

recv = PyOTReceiver()

recv.totalOTs = 10
recv.numChosenMsgs = 2 ** 10  # max 2^25 60+s
recv.hostName = "127.0.0.1"
recv.port = 1213
recv.rootCA = f"{cython_dir}/certs/rootCA.crt"

choices = []

for x in range(recv.totalOTs):
    choices.append(x)
print("Receiver (KKRT): Execute without "
      "TLS------------------------------------------------------")
time1 = datetime.datetime.now().timestamp()
result = recv.execute(choices, False)
time2 = datetime.datetime.now().timestamp()
print(f"Receiver: Took: {time2 - time1}s")
print(f"Receiver: Result: {result}")
print("Receiver (KKRT): Execute with "
      "TLS---------------------------------------------------------")
time1 = datetime.datetime.now().timestamp()
result = recv.execute(choices, True)
time2 = datetime.datetime.now().timestamp()
print(f"Receiver: Took: {time2 - time1}s")
print(f"Receiver: Result: {result}")
recv.maliciousSecure = True
recv.inputBitCount = 76
print("Receiver (OOS): Execute without "
      "TLS------------------------------------------------------")
time1 = datetime.datetime.now().timestamp()
result = recv.execute(choices, False)
time2 = datetime.datetime.now().timestamp()
print(f"Receiver: Took: {time2 - time1}s")
print(f"Receiver: Result: {result}")
print("Receiver (OOS): Execute with "
      "TLS---------------------------------------------------------")
time1 = datetime.datetime.now().timestamp()
result = recv.execute(choices, True)
time2 = datetime.datetime.now().timestamp()
print(f"Receiver: Took: {time2 - time1}s")
print(f"Receiver: Result: {result}")
