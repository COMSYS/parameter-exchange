#!/bin/bash

# Variables --------------------------------------------------------------------
LIBDIR="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"
# Relativ path to make installation independet of path
WOLFSSL_FILENAME="libwolfssl.so"
if [ "$(uname)" == "Darwin" ]; then
  # Mac OS uses .dylib instead of .so for shared libraries
  WOLFSSL_FILENAME="libwolfssl.dylib"
  # Add /usr/local/include to environment so that boost is found
  # Standard location on Linux
  CPLUS_INCLUDE_PATH="/usr/local/include:${CPLUS_INCLUDE_PATH}"
  export CPLUS_INCLUDE_PATH
fi
WOLFSSL_LOC="$HOME/lib/$WOLFSSL_FILENAME"
NUM_THREADS=""

# Argument parser --------------------------------------------------------------
BUILD_LIBOTE=1  # By default build both libraries
BUILD_LIBPSI=1
OPTIND=1         # Reset in case getopts has been used previously in the s
while getopts "h?op" opt; do
    case "$opt" in
    h|\?)
        show_help
        exit 0
        ;;
    o) BUILD_LIBPSI=0
        break
        ;;
    p) BUILD_LIBOTE=0
        break
        ;;
    esac
done

# Install boost if necessary
if [ ! -d "${LIBDIR}/libOTe/cryptoTools/thirdparty/linux/boost" ]; then
    echo -e "Install boost. ---------------------------------------------------------------"
    cd "${LIBDIR}/libOTe/cryptoTools/thirdparty/linux" || exit
    bash boost.get
fi
# Install miracl if necessary
if [ ! -d "${LIBDIR}/libOTe/cryptoTools/thirdparty/linux/miracl" ]; then
    echo -e "Install MIRACL. ---------------------------------------------------------------"
    cd "${LIBDIR}/libOTe/cryptoTools/thirdparty/linux" || exit
    bash miracl.get
    cd "${LIBDIR}/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/" || exit
    sed -i -- 's|g++|g++ -fPIC|g' linux64
    bash linux64
fi

if [ ${BUILD_LIBOTE} -gt 0 ]; then
  echo -e "Build libOTe ---------------------------------------------------------------"
  cd "${LIBDIR}/libOTe" || exit
  # Remove CMakeFiles
  rm -rf CMakeCache.txt CMakeFiles/ Makefile cmake_install.cmake cryptoTools/CMakeFiles/ cryptoTools/Makefile \
      cryptoTools/cmake_install.cmake frontend_cryptoTools/CMakeFiles/ frontend_cryptoTools/Makefile \
      frontend_cryptoTools/cmake_install.cmake tests_cryptoTools/CMakeFiles/ tests_cryptoTools/Makefile \
      tests_cryptoTools/cmake_install.cmake lib/ bin/

  # Fix Typo in cryptoTools --> Fixed by commit 572763dc3feda7e73ea04e88e3f9ae63e6c10f05 of cryptoTools,
  # but libOTe still uses older version of cryptoTools.
  cd "${LIBDIR}/libOTe/cryptoTools" || exit
  git checkout -f
  git pull origin master
  git checkout -f 572763dc3feda7e73ea04e88e3f9ae63e6c10f05

  # Add wolfssl path
  cd "${LIBDIR}/libOTe" || exit
  if [ -f "${WOLFSSL_LOC}" ]; then
      # WOLFSSL has been installed into home, hence we have to adapt the paths.
      sed -i -- "s|WolfSSL_DIR \"/usr/local/\"|WolfSSL_DIR \"$HOME/\"|g" cryptoTools/cryptoTools/CMakeLists.txt
      sed -i -- "s|find_library(WOLFSSL_LIB NAMES wolfssl  HINTS \"\${WolfSSL_DIR}\")|set\(WOLFSSL_LIB \"\${WolfSSL_DIR}lib/${WOLFSSL_FILENAME}\"\)|g" cryptoTools/cryptoTools/CMakeLists.txt
      LD_LIBRARY_PATH="${HOME}/lib:${LD_LIBRARY_PATH}"
      export LD_LIBRARY_PATH
  fi

  # Compile ----------------------------------------------
  # Following line valid up to libOTe commit 06ff980
  # cmake . -DENABLE_MIRACL=ON -DENABLE_WOLFSSL=ON -DENABLE_SIMPLESTOT=OFF -DENABLE_KYBEROT=OFF -DENABLE_SILENTOT=OFF
  #
  # Following after cmake change in commit 5e5b44
  #
  # First line stays same. The following changes were made to the config:
  # Always ON before: KOS, IKNP, DELTA_KOS, DELTA_IKNP, OOS, KKRT, RR, AKN [I.e. those were ON by default in old config,
  # hence we should set them ON know.]
  # Implied by MIRACL before: NP (Naor Pinkas) --> Should be ON [Because MIRCAL was ON before]
  # Implied by RELIC before: MR (Masny Rindal) --> Should be OFF [Because no RELIC used]
  # Renamed: KYBEROT --> MR_KYBER [OFF before, now still OFF just with other name]
  # Split: SIMPLESTOT --> SIMPLESTOT & SIMPLESTOT_ASM [Both OFF]
  # Remainder stays same (SILENTOT, MIRACL, RELIC, WOLFSSL, NET_LOG, CIRCUITS)
  cmake . -DENABLE_MIRACL=ON -DENABLE_WOLFSSL=ON -DENABLE_SIMPLESTOT=OFF -DENABLE_SILENTOT=OFF \
          -DENABLE_MR_KYBER=OFF \
          -DENABLE_MR=OFF -DENABLE_NP=ON -DENABLE_KOS=ON -DENABLE_IKNP=ON -DENABLE_DELTA_KOS=ON -DENABLE_DELTA_IKNP=ON \
          -DENABLE_OOS=ON -DENABLE_KKRT=ON -DENABLE_RR=ON -DENABLE_AKN=ON
  make -j $NUM_THREADS
fi

if [ ${BUILD_LIBPSI} -gt 0 ]; then
  echo -e "Build libPSI ---------------------------------------------------------------"
  cd "${LIBDIR}/libPSI" || exit
  git clean -d -f -x  # Remove previous cmake changes
  # Add - fPIC to generate position-independent code
  echo 'set(CMAKE_CXX_FLAGS "-fPIC ${CMAKE_CXX_FLAGS}")' >> libPSI/CMakeLists.txt
  # Add wolfssl to linker
  if [ -f "$WOLFSSL_LOC" ]; then
    # Wolfssl installed into $HOME
    sed -i -- "s|WolfSSL_DIR \"/usr/local/\"|WolfSSL_DIR \"$HOME/\"|g" CMakeLists.txt
    sed -i -- "s|find_library(WOLFSSL_LIB NAMES wolfssl  HINTS \"\${WolfSSL_DIR}\")|set\(WOLFSSL_LIB \"\${WolfSSL_DIR}lib/${WOLFSSL_FILENAME}\"\)|g" libPSI/CMakeLists.txt
  fi
  # Compile ----------------------------------------------
  # First line valid until commit 130dd2a (TESTED UNTIL b882dc6)
  # cmake . -DENABLE_MIRACL=ON -DENABLE_SIMPLESTOT=OFF -DENABLE_RELIC=OFF  # until commit b882dc6
  #
  # New cmake valid from 0fd8e28
  # MIRACL, SIMPLESTOT and RELIC stay the same (first line)
  # MR_KYBER is new. OFF because not compiled into libOTe
  # Always ON before [old default settings]: (DRRN_PSI), RR17_PSI, RR17B_PSI, KKRT_PSI, GRR_PSI, RR16_PSI
  # DRRN_PSI has to be set to OFF because of an compiler error occuring otherwise. We do not know the reason for that.
  # New PSI (not existing before --> OFF): DCW_PSI
  # Dependent on RELIC (auto implied by RELIC=ON before --> set OFF): DKT_PSI, ECDH_PSI

  cmake . -DENABLE_MIRACL=ON -DENABLE_SIMPLESTOT=OFF -DENABLE_RELIC=OFF -DENABLE_WOLFSSL=ON\
          -DENABLE_MR_KYBER=OFF \
          -DENABLE_DRRN_PSI=OFF -DENABLE_RR17_PSI=ON -DENABLE_RR17B_PSI=ON -DENABLE_KKRT_PSI=ON -DENABLE_GRR_PSI=ON \
          -DENABLE_RR16_PSI=ON -DENABLE_DCW_PSI=OFF -DENABLE_DKT_PSI=OFF -DENABLE_ECDH_PSI=OFF

  make -j $NUM_THREADS
fi
