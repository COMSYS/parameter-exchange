#!/usr/bin/env bash

# Colors
ncolors=$(tput colors)
big="$(tput bold)"
end="$(tput sgr0)"
CURRENT_DIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

echo -e "${big}Testing OT Python interface:${end}"
python3 ${CURRENT_DIR}/ot/Test/sendMain.py & python3 ${CURRENT_DIR}/ot/Test/recvMain.py
echo -e "${big}Testing PSI Python interface:${end}"
python3 ${CURRENT_DIR}/psi/Tests/sendMain.py & python3 ${CURRENT_DIR}/psi/Tests/recvMain.py