# cython: language_level=3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
from libcpp.string cimport string
from libc.stdint cimport uint64_t
from libc.stdint cimport uint8_t
from libc.stdint cimport uint32_t
from libcpp.vector cimport vector
from libcpp.pair cimport pair
from libcpp cimport bool


cdef extern from "OTSender.h":
    cdef cppclass OTSender:
        uint64_t totalOTs
        uint64_t numThreads
        string hostName
        uint32_t port
        string connectionName
        string serverCert
        string serverKey

        bool maliciousSecure
        uint64_t statSecParam
        uint8_t inputBitCount
        uint64_t numChosenMsgs

        OTSender() except +
        void executeDiff(vector[vector[pair[uint64_t, uint64_t]]] sendMessages, bool tls)
        void executeSame(vector[pair[uint64_t, uint64_t]] sendMessages, bool tls)

cdef extern from "OTReceiver.h":
    cdef cppclass OTReceiver:
        uint64_t totalOTs
        uint64_t numThreads
        string hostName
        uint32_t port
        string connectionName
        string rootCA

        bool maliciousSecure
        uint64_t statSecParam
        uint8_t inputBitCount
        uint64_t numChosenMsgs

        OTReceiver() except +
        vector[pair[uint64_t, uint64_t]] execute(vector[uint64_t] choices, bool tls)



