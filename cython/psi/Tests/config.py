#!/usr/bin/env python3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import os


def parent(path: str):
    return os.path.dirname(path)


hostname = "127.0.0.1"
port = 12345
numThreads = 1
current_dir = os.path.dirname(os.path.abspath(__file__))
certPath = parent(parent(parent(current_dir))) + "/data/certs/"
setSize = 100
psi_name = "KKRT16"
