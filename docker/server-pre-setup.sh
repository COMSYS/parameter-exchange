#!/usr/bin/env bash

# Colors
ncolors=$(tput colors)
big="$(tput bold)"
normal="$(tput sgr0)"

CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$1'))")


echo -e "${big}Install packages.${normal}"
if [[ $EUID -eq 0 ]]; then
  # Script has root rights
  if [ "$(uname)" != "Darwin" ]; then
    apt-get -yqq update
    apt-get -yqq install python3-pip python3-dev
    apt-get -yqq install wget git g++ cmake vim tmux htop
    apt-get -yqq install redis libssl-dev dh-autoreconf colordiff
  fi
fi

echo -e "${big}Install pip packages.${normal}"
pip3 install --requirement "${CURRENT_DIR}/requirements.txt"

echo -e "${big}Install Wolfssl.${normal}"
${CURRENT_DIR}/install_wolfssl.sh

echo -e "${big}Finished.${normal}"