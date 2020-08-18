#!/usr/bin/env python3
"""Parser for WZL Data.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import json

from lib.config import WORKING_DIR

# Mappings from Names to Ints--------------------------------------------------
steuerung = {
    'Siemens': 1
}
motor = {
    '1FT7034-5AK7': 1,
    '1FT7036-5AK7': 2,
    '1FT7042-5AK7': 3,
}
werkstuek = {
    'Einsatzstahl': 1,
    'Grauguss': 2,
    'Aluminium gewalzt': 3,
    'Rostfreier Stahl': 4,
    'Temperguss': 5,
    'Superlegierungen': 6,
    'Automatenstahl': 7,
    'Aluminium gegossen': 8,
    'Werkzeugstahl': 9,
    'Kupferlegierungen': 10,
}
werkzeug = {
    'HSS': 1,
}
result = []
with open(f"{WORKING_DIR}/data/wzl_data_unconverted.csv", "r") as f:
    lines = f.readlines()
# Skip header
lines = lines[1:]
string_fields = [0, 8, 9, 10, 14, 15]
for line in lines:
    values = line.split(';')
    values = [float(v) if i not in string_fields else v for i,
                    v in enumerate(values)]
    # Map Names to ints, because we cannot handle Names
    values[0] = steuerung[values[0]]
    values[8] = motor[values[8]]
    values[9] = motor[values[9]]
    values[10] = motor[values[10]]
    values[14] = werkstuek[values[14]]
    values[15] = werkzeug[values[15]]
    result.append([float(i) for i in values])

rounding_vec = [3 if i not in string_fields else 0 for i in range(len(values))]
print("Generated vectors: ", len(result))
print("Rounding vector = ", rounding_vec)
print("Record Length: ", len(result[0]))
with open(f"{WORKING_DIR}/data/wzl_data.txt", "w") as fd:
    fd.writelines([f"{str(r)}\n" for r in result])
