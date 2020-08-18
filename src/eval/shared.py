#!/usr/bin/env python3
"""Shared eval methods.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
import select
import subprocess
from collections.abc import Iterable
from typing import TextIO, Any, List

from tqdm import tqdm

from lib.config import WORKING_DIR

log = logging.getLogger(__name__)


def reset_config() -> None:
    """Reset the config file."""
    subprocess.run(['git', 'checkout', '-f', 'lib/config.py'])


def set_config(variable: str, v: Any) -> None:
    """Set a certain variable in the config file to the given value."""
    with open(WORKING_DIR + "src/lib/config.py", "r") as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if f"{variable} =" in line:
            lines[i] = f"{variable} = {str(v)}\n"
    # Overwrite
    with open(WORKING_DIR + "src/lib/config.py", "w") as f:
        f.writelines(lines)


def set_total_rec_len(v: int) -> None:
    """Set the total record length."""
    set_config("RECORD_LENGTH", v)


def set_rec_id_len(v: int) -> None:
    """Set the record id length."""
    set_config("RECORD_ID_LENGTH", v)


def set_rounding(v: List[int]) -> None:
    """Set the rounding vector."""
    set_config("ROUNDING_VEC", v)


def get_last_line(f: TextIO) -> str:
    """Return last line of file descriptor."""
    lines = f.readlines()
    return lines[-1]


def lb(o, *args, **kwargs):
    """Return a tqdm object if there is more than one element"""
    if ((isinstance(o, list) or isinstance(o, tuple)) and
            len(o) == 1):
        return o
    elif isinstance(o, Iterable):
        return tqdm(o, *args, **kwargs)
    else:
        return [o]


def read_output(output: str) -> (str, str, str):
    """Read the output of the ot and psi processes."""
    runtime, mem, error = ['0', '0', '0']
    for line in output.split(os.linesep):
        if not line.startswith('['):
            if not line.startswith('C'):
                if line.split(':') != ['']:
                    runtime, mem, error = line.split(':')
    return runtime, mem, error


def check_if_client_hangs(cp: subprocess.Popen) -> None:
    """Raise error if client process hangs."""
    counter2 = 0
    try:
        cp.wait(30)
    except subprocess.TimeoutExpired:
        # Not terminated
        # Count current outputs
        counter = 0
        poll_obj = select.poll()
        poll_obj.register(cp.stderr,
                          select.POLLIN)
        while poll_obj.poll(0):
            line = cp.stderr.readline()
            if "client socket connect error" in line:
                counter += 1
        log.debug(f"Counted after first timeout: "
                  f"{counter}")
        # Wait again
        try:
            cp.wait(30)
        except subprocess.TimeoutExpired:
            # Still unfinished
            counter2 = 0
            while poll_obj.poll(0):
                line = cp.stderr.readline()
                if "client socket connect error" in \
                        line:
                    counter2 += 1
            log.debug(f"Counted after 2nd timeout: "
                      f"{counter2}")
    if counter2 > 0:
        # Connection still hangs, restart
        raise RuntimeError("Conection hangs.")
