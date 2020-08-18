#!/usr/bin/env python3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
# noinspection PyUnresolvedReferences
from cPSIInterface import PyPSISender
import os
import sys
from config import (
    hostname, port, numThreads, certPath, setSize, psi_name
)

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

print("Sender: Starting sender for: ", psi_name)

send = PyPSISender()
send.hostName = hostname
send.port = port
send.numThreads = numThreads
send.setSize = setSize
send.serverCert = certPath + "keyserver.crt"
send.serverKey = certPath + "keyserver.key"

sendSet = []
for x in range(setSize):
    sendSet.append(x)

print("HbC Sender [KKRT16]: Execute without "
      "TLS----------------------------------------------------")
send.tls = False
send.execute("KKRT16", sendSet)
print("HbC Sender [KKRT16]: "
      "-----------------------------------------------------------------------")
print("Sender: Execute with "
      "TLS-------------------------------------------------------")
send.tls = True
send.execute("KKRT16", sendSet)
print("Sender: "
      "-----------------------------------------------------------------------")
print("Malicious Sender [RR17]: Execute without "
      "TLS----------------------------------------------------")
send.tls = False
send.execute("RR17", sendSet)
print("Malicious Sender [RR17]: "
      "-----------------------------------------------------------------------")
print("Sender: Execute with "
      "TLS-------------------------------------------------------")
send.tls = True
send.execute("RR17", sendSet)
print("Sender: "
      "-----------------------------------------------------------------------")
