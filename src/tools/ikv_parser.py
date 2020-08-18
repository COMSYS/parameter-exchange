#!/usr/bin/env python3
"""Parser for IKV Lego Data.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import json

from lib.config import WORKING_DIR

with open(f"{WORKING_DIR}/data/ikv_data_unconverted.json", "r") as f:
    d = json.load(f)
result = {}
lists_only = []
for key in d:
    element = d[key]
    output = []
    if 'x' in element:
        # ignore legolist and heightlist
        for i in range(len(element['x'])):
            v = []
            # Each is own vector
            # Geometry first
            for param in element['geometry'].values():
                v.append(param)
            # Then x
            for param in element['x'][i]:
                v.append(param)
            # Last y
            for param in element['y'][i]:
                v.append(param)
            output.append(v)
    result[key] = output
    lists_only.extend(output)

with open(f"{WORKING_DIR}/data/lego_converted.txt", "w") as f:
    for key in result:
        f.write(f"{key}:\n")
        for i, v in enumerate(result[key]):
            f.write(f"\t{i}: {str(v)}\n")

with open(f"{WORKING_DIR}/data/lego_converted.json", "w") as f:
    json.dump(result, f)

print("Generated vectors: ", len(lists_only))
print("Record Length: ", len(lists_only[0]))
with open(f"{WORKING_DIR}/data/ikv_data.txt", "w") as fd:
    fd.writelines([f"{str(r)}\n" for r in lists_only])
