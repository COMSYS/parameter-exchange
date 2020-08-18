# Copyright (c) 2020.
# @author: Erik Buchholz
# @maintainer: Erik Buchholz
# @email: buchholz@comsys.rwth-aachen.de

cmake_minimum_required(VERSION 3.10)
project(masterarbeit)
set(CMAKE_CXX_STANDARD 14)

# Output Directories
set( CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/bin)
set( CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/lib)
set( CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_HOME_DIRECTORY}/lib)

# Directories Normal
set(lib_dir ${CMAKE_SOURCE_DIR}/../libraries/)
set(LibOTe_dir ${lib_dir}libOTe/lib/)
set(LibPSI_dir ${lib_dir}libPSI/lib/)
set(Miracl_dir ${lib_dir}libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/)
set(Wolfssl_dir /usr/local/lib/) #  WOLFSSL Normal
set(Wolfssl_dir2 /home/buchholz/lib/) # WOLFSSL Passion

# Directories Docker Full
set(lib_dir2 /lib/)
set(LibOTe_dir2 ${lib_dir2}libOTe/lib/)
set(LibPSI_dir2 ${lib_dir2}libPSI/lib/)
set(Miracl_dir2 ${lib_dir2}libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/)

# Flags
# no-pie necessary because of libOTe and libPSI
set(CMAKE_C_FLAGS "-w -Wall -g -D_REENTRANT -no-pie -fPIC") #-Xlinker -v
set(CMAKE_CXX_FLAGS  "${CMAKE_C_FLAGS}  -std=c++14")

# Includes
include_directories(${CMAKE_SOURCE_DIR}/psi_interface)
include_directories(${CMAKE_SOURCE_DIR}/ot_interface)
include_directories(${lib_dir}libPSI)
include_directories(${lib_dir}libOTe)
include_directories(${lib_dir}libOTe/cryptoTools)
include_directories(${lib_dir}libOTe/cryptoTools/thirdparty/linux/boost)
include_directories(/home/buchholz/include) # WOLFSSL Passion
include_directories(/usr/local/include) # WOLFSSL Normal

# Includes Docker Full
include_directories(${lib_dir2}libPSI)
include_directories(${lib_dir2}libOTe)
include_directories(${lib_dir2}libOTe/cryptoTools)
include_directories(${lib_dir2}libOTe/cryptoTools/thirdparty/linux/boost)

# LibOTe ---------------------------------------------------------------------
find_library(
        libOTe_LIB
        NAMES libOTe
        HINTS ${LibOTe_dir} ${LibOTe_dir2})
if(NOT libOTe_LIB)
    Message(${libOTe_LIB})
    message(FATAL_ERROR "Failed to find libOTe at " ${LibOTe_dir})
else()
    message("LibOTe at  ${libOTe_LIB}")
endif()
# ----------------------------------------------------------------------------
# LibPSI ---------------------------------------------------------------------
find_library(libPSI_LIB
        NAMES libPSI
        HINTS ${LibPSI_dir} ${LibPSI_dir2})
if(NOT libPSI_LIB)
    Message(${libPSI_LIB})
    message(FATAL_ERROR "Failed to find libPSI at " ${LibPSI_dir})
else()
    message("LibPSI at  ${libPSI_LIB}")
endif()
# ----------------------------------------------------------------------------
# CryptoTools ----------------------------------------------------------------
find_library(
        cryptoTools_LIB
        NAMES cryptoTools
        HINTS ${LibOTe_dir} ${LibOTe_dir2})
if(NOT cryptoTools_LIB)
    Message(${cryptoTools_LIB})
    message(FATAL_ERROR "Failed to find cryptoTools at " ${LibOTe_dir})
else()
    message("CryptoTools at  ${cryptoTools_LIB}")
endif()
# ----------------------------------------------------------------------------
# MIRACL ---------------------------------------------------------------------
find_library(MIRACL_LIB
        NAMES miracl
        HINTS ${Miracl_dir} ${Miracl_dir2})
if(NOT MIRACL_LIB)
    Message(${MIRACL_LIB})
    message(FATAL_ERROR "Failed to find miracl at " ${Miracl_dir})
else()
    message("Miracl at  ${MIRACL_LIB}")
endif()
# ----------------------------------------------------------------------------
# WOLFSSL --------------------------------------------------------------------
find_library(WOLFSSL_LIB wolfssl
        HINTS ${Wolfssl_dir} ${Wolfssl_dir2})
if(NOT WOLFSSL_LIB)
    Message(${WOLFSSL_LIB})
    message(FATAL_ERROR "Failed to find wolfssl at ${Wolfssl_dir} or ${Wolfssl_dir2}")
else()
    message("Wolfssl at  ${WOLFSSL_LIB}")
endif()
# ----------------------------------------------------------------------------
# PTHREAD --------------------------------------------------------------------
set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED) # pthread
# ----------------------------------------------------------------------------
# OT Targets ----------------------------------------------------------------
set(OT_TEST_DIR ${CMAKE_SOURCE_DIR}/ot_interface/Test/)
set(OT_DIR ${CMAKE_SOURCE_DIR}/ot_interface/)
# Library Files
add_library(OTInterface STATIC ${OT_DIR}OTReceiver.cpp ${OT_DIR}OTSender.cpp ${OT_DIR}util.cpp)
# Test Files
add_executable(otSend.o ${OT_TEST_DIR}mainSend.cpp ${OT_DIR}OTSender.cpp ${OT_DIR}util.cpp)
add_executable(otRecv.o ${OT_TEST_DIR}mainRecv.cpp ${OT_DIR}OTReceiver.cpp ${OT_DIR}util.cpp)
add_executable(nwSend.o ${OT_TEST_DIR}NWSend.cpp ${OT_DIR}NWSender.cpp)
add_executable(nwRecv.o ${OT_TEST_DIR}NWRecv.cpp ${OT_DIR}NWReceiver.cpp)
add_executable(fullOT.o ${OT_TEST_DIR}fullTest.cpp ${OT_DIR}OTSender.cpp ${OT_DIR}OTReceiver.cpp ${OT_DIR}util.cpp)
add_executable(min ${OT_TEST_DIR}minimalExample.cpp)

# Link libs
set(OT_LIBS ${libOTe_LIB} ${cryptoTools_LIB} ${MIRACL_LIB} ${WOLFSSL_LIB} pthread)
target_link_libraries(otSend.o ${OT_LIBS})
target_link_libraries(otRecv.o ${OT_LIBS})
target_link_libraries(nwSend.o ${OT_LIBS})
target_link_libraries(nwRecv.o ${OT_LIBS})
target_link_libraries(fullOT.o ${OT_LIBS})
target_link_libraries(min ${OT_LIBS})
# ----------------------------------------------------------------------------
# PSI Targets ----------------------------------------------------------------
set(PSI_TEST_DIR ${CMAKE_SOURCE_DIR}/psi_interface/Tests/)
set(PSI_DIR ${CMAKE_SOURCE_DIR}/psi_interface/)
# Library file
add_library(PSIInterface STATIC ${PSI_DIR}PSIReceiver.cpp ${PSI_DIR}PSISender.cpp ${PSI_DIR}util.cpp)
# Test files
add_executable(psi.out ${PSI_TEST_DIR}main.cpp ${PSI_DIR}util.cpp ${PSI_DIR}PSIReceiver.cpp ${PSI_DIR}PSISender.cpp)
add_executable(psiSend.o ${PSI_TEST_DIR}mainSend.cpp ${PSI_DIR}util.cpp ${PSI_DIR}PSISender.cpp)
add_executable(psiRecv.o ${PSI_TEST_DIR}mainRecv.cpp ${PSI_DIR}util.cpp ${PSI_DIR}PSIReceiver.cpp)
add_executable(interface_test ${CMAKE_SOURCE_DIR}/test/test_interfaces.cpp  ${OT_DIR}OTSender.cpp ${OT_DIR}OTReceiver.cpp ${OT_DIR}util.cpp ${PSI_DIR}util.cpp ${PSI_DIR}PSIReceiver.cpp ${PSI_DIR}PSISender.cpp)

# Link libs
set(PSI_LIBS ${libPSI_LIB} ${OT_LIBS})
target_link_libraries(psi.out ${PSI_LIBS})
target_link_libraries(psiSend.o ${PSI_LIBS})
target_link_libraries(psiRecv.o ${PSI_LIBS})
target_link_libraries(interface_test ${PSI_LIBS})
# ----------------------------------------------------------------------------
# Cython Targets--------------------------------------------------------------
add_custom_target(
        ot_interface ALL
        COMMAND rm -f ${CMAKE_CURRENT_SOURCE_DIR}/ot/cOTInterface.cpp
        COMMAND rm -f ${CMAKE_CURRENT_SOURCE_DIR}/ot/*.so
        COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/ot/cython_setup.py build_ext -b ${CMAKE_CURRENT_SOURCE_DIR}/ot -t ${CMAKE_CURRENT_SOURCE_DIR}/tmp
)
add_custom_target(
        psi_interface ALL
        COMMAND rm -f ${CMAKE_CURRENT_SOURCE_DIR}/psi/*.so
        COMMAND rm -f ${CMAKE_CURRENT_SOURCE_DIR}/psi/CPSIInterface.cpp
        COMMAND python3 ${CMAKE_CURRENT_SOURCE_DIR}/psi/cython_setup.py build_ext -b ${CMAKE_CURRENT_SOURCE_DIR}/psi -t ${CMAKE_CURRENT_SOURCE_DIR}/tmp
)
add_dependencies(ot_interface OTInterface)
add_dependencies(psi_interface PSIInterface)
# Add Cython Temp files to make clean
set_property(DIRECTORY APPEND PROPERTY
        ADDITIONAL_MAKE_CLEAN_FILES "${CMAKE_CURRENT_SOURCE_DIR}/tmp"
        "${CMAKE_CURRENT_SOURCE_DIR}/ot/cOTInterface.cpp"
        "${CMAKE_CURRENT_SOURCE_DIR}/psi/cPSIInterface.cpp"
        )
