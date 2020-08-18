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


cdef extern from "PSISender.h":
    cdef cppclass Sender:
        uint64_t statSecParam;
        uint64_t setSize;

        string hostName;
        uint32_t port;
        string connectionName;
        uint64_t numThreads;
        bool tls;
        string serverCert;
        string serverKey;

        # GRR18
        double epsBin;
        double binScaler;
        uint64_t bitSize;

        # DRRT18
        # uint64_t serverSetSize;
        # uint64_t numHash;
        
        Sender() except +

        # Deprecated
        # void execute(string psiScheme, vector[pair[uint64_t, uint64_t]] set, void (*callback) (unsigned char* data, uint64_t size, void* funcData), void *sendData, void* recvData)
        # void initCustomChannel(void (*callback) (unsigned char* data, uint64_t size, void* funcData), void *sendData, void* recvData);

        void execute(string psiScheme, vector[pair[uint64_t, uint64_t]] set)


cdef extern from "PSIReceiver.h":
    cdef cppclass Receiver:
        uint64_t statSecParam;
        uint64_t setSize;

        string hostName;
        uint32_t port;
        string connectionName;
        uint64_t numThreads;
        bool tls;
        string rootCA;

        # GRR18
        double epsBin;
        double binScaler;
        uint64_t bitSize;

        # DRRT18
        # uint64_t serverSetSize;
        # uint64_t numHash;
        
        Receiver() except +

        # Deprecated
        # vector[uint64_t] execute(string psiScheme, vector[pair[uint64_t,uint64_t]] set, void (*callback) (unsigned char* data, uint64_t size, void* funcData), void *sendData, void* recvData)
        # void initCustomChannel(void (*callback) (unsigned char* data, uint64_t size, void* funcData), void *sendData, void* recvData);

        vector[uint64_t] execute(string psiScheme, vector[pair[uint64_t,uint64_t]] set)
        

       

