#!/usr/bin/env bash

# Colors
ncolors=$(tput colors)
big="$(tput bold)"
normal="$(tput sgr0)"

cd wolfssl
./autogen.sh
if [[ $EUID -eq 0 ]]; then
  # Script has root rights
  CMD="./configure --enable-opensslextra --enable-debug CFLAGS=-DKEEP_PEER_CERT"
else
  # No root rights --> install into home
  CMD="./configure --enable-opensslextra --enable-debug CFLAGS=-DKEEP_PEER_CERT --prefix=$HOME"
fi
echo -e "Executing: ${big}${CMD}${normal}"
$CMD
make -j
make install
ldconfig || true  # Not necessary on all OSes