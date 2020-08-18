#!/usr/bin/env bash

# Colors
ncolors=$(tput colors)
big="$(tput bold)"
end="$(tput sgr0)"

# Variables
CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$1'))")
REPO_BASE_DIR="$(dirname "$CURRENT_DIR")"
echo -e "Base directory: ${big}${REPO_BASE_DIR}${end}"

# Move pre-commit hock
echo "Move pre-commit hook."
cp ${REPO_BASE_DIR}/docker/pre-commit ${REPO_BASE_DIR}/.git/hooks/

# Install pre-requesites BOOST and MIRCAL
echo "Install BOOST and MIRACL."
cd ${REPO_BASE_DIR}/libraries/libOTe/cryptoTools/thirdparty/linux || exit
rm -rf miracl
bash all.get
# Add -fPIC to MIRACL linux64 file
cd ${REPO_BASE_DIR}/libraries/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/ || exit
# Add - fPIC to generate position-independent code
sed -i -- 's|g++|g++ -fPIC|g' linux64
# And execute it
bash linux64

# Build libOTe and libPSI ------------------------------------------------------
echo "Build libOTe and libPSI."
cd ${REPO_BASE_DIR}/libraries/ || exit
bash build_libraries.sh

# Compile Cython Code
echo "Compile cython code."
cd ${REPO_BASE_DIR}/cython || exit
cmake .
make -j $NUM_THREADS
cd ${REPO_BASE_DIR}/cython/ot || exit
bash runSetup.sh
cd ${REPO_BASE_DIR}/cython/psi || exit
bash runSetup.sh

echo "Setup Finished!"

echo "Running Unit-Tests of libraries. Please confirm positive results."
echo "Testing ${big}libPSI${end} now:"
sleep 2s
${REPO_BASE_DIR}/libraries/libPSI/bin/frontend.exe -u
echo "Testing ${big}libPSI${end} completed."
echo "Testing ${big}libOTe${end} now:"
sleep 3s
${REPO_BASE_DIR}/libraries/libOTe/bin/frontend_libOTe -u
echo "Testing ${big}libOTe${end} completed."
echo "Testing ${big}cryptoTools${end} now:"
sleep 3s
${REPO_BASE_DIR}/libraries/libOTe/bin/frontend_cryptoTools -u
echo "Testing ${big}cryptoTools${end} completed."
echo "Testing ${big}cython${end} interfaces now:"
sleep 3s
cd ${REPO_BASE_DIR}/cython
./bin/interface_test -d yes
