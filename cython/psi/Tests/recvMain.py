#!/usr/bin/env python3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSIReceiver
import os
import sys
from config import (
    hostname, port, numThreads, certPath, setSize, psi_name
)

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

print("Receiver: Starting receiver for: ", psi_name)

recv = PyPSIReceiver()
recv.hostName = hostname
recv.port = port
recv.numThreads = numThreads
recv.setSize = setSize
recv.rootCA = certPath + "rootCA.crt"

recvSet = []
for x in range(setSize):
    recvSet.append(x + x % 2 * setSize)

print("HbC Receiver [KKRT16]: Execute without "
      "TLS----------------------------------------------------")
recv.tls = False
intersection: list = recv.execute("KKRT16", recvSet)
intersection.sort()
print("Receiver: Found " + str(len(intersection)))
print("Receiver: Intersection: ", intersection)
print("Receiver: "
      "-----------------------------------------------------------------------")
print("HbC Receiver [KKRT16]: Execute with "
      "TLS-------------------------------------------------------")
recv.tls = True
intersection = recv.execute("KKRT16", recvSet)
intersection.sort()
print("Receiver: Found " + str(len(intersection)))
print("Receiver: Intersection: ", intersection)
print("Receiver: "
      "-----------------------------------------------------------------------")
print("Malicious Receiver [RR17]: Execute without "
      "TLS----------------------------------------------------")
recv.tls = False
intersection: list = recv.execute("RR17", recvSet)
intersection.sort()
print("Receiver: Found " + str(len(intersection)))
print("Receiver: Intersection: ", intersection)
print("Receiver: "
      "-----------------------------------------------------------------------")
print("Malicious Receiver [RR17]: Execute with "
      "TLS-------------------------------------------------------")
recv.tls = True
intersection = recv.execute("RR17", recvSet)
intersection.sort()
print("Receiver: Found " + str(len(intersection)))
print("Receiver: Intersection: ", intersection)
print("Receiver: "
      "-----------------------------------------------------------------------")
