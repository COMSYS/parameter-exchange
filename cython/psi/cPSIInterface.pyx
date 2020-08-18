#distutils: language = c++
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""

from libcpp.string cimport string
from libc.stdint cimport uint64_t
from libcpp.vector cimport vector
from libcpp.pair cimport pair
    
    
from cPSIInterface cimport Receiver

cdef class PyPSIReceiver:
    cdef Receiver c_recv
        
    def execute(self, psiScheme, recvSet):
        recvSetWithPairs = []
        if(len(recvSet) > 0 and not type(recvSet[0]) == list):
            for item in recvSet:
                recvSetWithPairs.append([item>>64, item % (2**64)])
        else:
            recvSetWithPairs = recvSet
                
        if(type(psiScheme) is str):
            psiScheme = psiScheme.encode('utf-8')
        return self.c_recv.execute(psiScheme, recvSetWithPairs)

    @property
    def statSecParam(self):
        return self.c_recv.statSecParam

    @statSecParam.setter
    def statSecParam(self, statSecParam):
        self.c_recv.statSecParam = statSecParam

    @property
    def setSize(self):
        return self.c_recv.setSize

    @setSize.setter
    def setSize(self, setSize):
        self.c_recv.setSize = setSize

    @property
    def hostName(self):
        if(type(self.c_recv.hostName) is str):
            return self.c_recv.hostName
        else:    
            return self.c_recv.hostName.decode() 
    
    @hostName.setter
    def hostName(self, hostName):
        if(type(hostName) is str):
            hostName = hostName.encode('utf-8')
        self.c_recv.hostName = hostName

    @property
    def port(self):
        return self.c_recv.port

    @port.setter
    def port(self, port):
        self.c_recv.port = port

    @property
    def connectionName(self):
        if(type(self.c_recv.connectionName) is str):
            return self.c_recv.connectionName
        else:
            return self.c_recv.connectionName.decode()

    @connectionName.setter
    def connectionName(self, connectionName):
        if(type(connectionName) is str):
            connectionName = connectionName.encode('utf-8')
        self.c_recv.connectionName = connectionName

    @property
    def numThreads(self):
        return self.c_recv.numThreads
        
    @numThreads.setter
    def numThreads(self, numThreads):
        self.c_recv.numThreads = numThreads

    @property
    def tls(self):
        return self.c_recv.tls

    @tls.setter
    def tls(self, tls):
        self.c_recv.tls = tls

    @property
    def rootCA(self):
        if(type(self.c_recv.rootCA) is str):
            return self.c_recv.rootCA
        else:
            return self.c_recv.rootCA.decode()

    @rootCA.setter
    def rootCA(self, rootCA):
        if(type(rootCA) is str):
            rootCA = rootCA.encode('utf-8')
        self.c_recv.rootCA = rootCA

    # GRR18 -------------------------------------------------------------------
    @property
    def epsBin(self):
        return self.c_recv.epsBin

    @epsBin.setter
    def epsBin(self, epsBin):
        self.c_recv.epsBin = epsBin

    @property
    def binScaler(self):
        return self.c_recv.binScaler
    
    @binScaler.setter
    def binScaler(self, binScaler):
        self.c_recv.binScaler = binScaler

    @property
    def bitSize(self):
        return self.c_recv.bitSize
        
    @bitSize.setter
    def bitSize(self, bitSize):        
        self.c_recv.bitSize = bitSize

    # DRRT18 -------------------------------------------------------------------
    # @property
    # def serverSetSize(self):
    #     return self.c_recv.serverSetSize
    #
    # @serverSetSize.setter
    # def serverSetSize(self, serverSetSize):
    #     self.c_recv.serverSetSize = serverSetSize
    #
    # @property
    # def numHash(self):
    #     return self.c_recv.numHash
    #
    # @numHash.setter
    # def numHash(self, numHash):
    #     self.c_recv.numHash = numHash

        
from cPSIInterface cimport Sender

cdef class PyPSISender:
    cdef Sender c_send

    def execute(self, psiScheme, sendSet):
        sendSetWithPairs = []
        if(len(sendSet) > 0 and not type(sendSet[0]) == list):
            for item in sendSet:
                sendSetWithPairs.append([item>>64, item % (2**64)])
        else:
            sendSetWithPairs = sendSet
        
        if(type(psiScheme) is str):
            psiScheme = psiScheme.encode('utf-8')
        self.c_send.execute(psiScheme, sendSetWithPairs)
        
    @property
    def statSecParam(self):
        return self.c_recv.statSecParam

    @statSecParam.setter
    def statSecParam(self, statSecParam):
        self.c_send.statSecParam = statSecParam

    @property
    def setSize(self):
        return self.c_send.setSize

    @setSize.setter
    def setSize(self, setSize):
        self.c_send.setSize = setSize

    @property
    def hostName(self):
        if(type(self.c_send.hostName) is str):
            return self.c_send.hostName
        else:
            return self.c_send.hostName.decode()

    @hostName.setter
    def hostName(self, hostName):
        if(type(hostName) is str):
            hostName = hostName.encode('utf-8')
        self.c_send.hostName = hostName

    @property
    def port(self):
        return self.c_send.port

    @port.setter
    def port(self, port):
        self.c_send.port = port

    @property
    def connectionName(self):
        if(type(self.c_send.connectionName) is str):
            return self.c_send.connectionName
        else:
            return self.c_send.connectionName.decode()

    @connectionName.setter
    def connectionName(self, connectionName):
        if(type(connectionName) is str):
            connectionName = connectionName.encode('utf-8')
        self.c_send.connectionName = connectionName

    @property
    def numThreads(self):
        return self.c_send.numThreads

    @numThreads.setter
    def numThreads(self, numThreads):
        self.c_send.numThreads = numThreads

    @property
    def tls(self):
        return self.c_send.tls

    @tls.setter
    def tls(self, tls):
        self.c_send.tls = tls

    @property
    def serverCert(self):
        if(type(self.c_send.serverCert) is str):
            return self.c_send.serverCert
        else:
            return self.c_send.serverCert.decode()

    @serverCert.setter
    def serverCert(self, serverCert):
        if(type(serverCert) is str):
            serverCert = serverCert.encode('utf-8')
        self.c_send.serverCert = serverCert

    @property
    def serverKey(self):
        if(type(self.c_send.serverKey) is str):
            return self.c_send.serverKey
        else:
            return self.c_send.serverKey.decode()

    @serverKey.setter
    def serverKey(self, serverKey):
        if(type(serverKey) is str):
            serverKey = serverKey.encode('utf-8')
        self.c_send.serverKey = serverKey

    # GRR18 -------------------------------------------------------------------
    @property
    def epsBin(self):
        return self.c_send.epsBin

    @epsBin.setter
    def epsBin(self, epsBin):
        self.c_send.epsBin = epsBin

    @property
    def binScaler(self):
        return self.c_send.binScaler

    @binScaler.setter
    def binScaler(self, binScaler):
        self.c_send.binScaler = binScaler

    @property
    def bitSize(self):
        return self.c_send.bitSize

    @bitSize.setter
    def bitSize(self, bitSize):
        self.c_send.bitSize = bitSize

    # DRRT18 -------------------------------------------------------------------
    # @property
    # def serverSetSize(self):
    #     return self.c_send.serverSetSize
    #
    # @serverSetSize.setter
    # def serverSetSize(self, serverSetSize):
    #     self.c_send.serverSetSize = serverSetSize
    #
    # @property
    # def numHash(self):
    #     return self.c_send.numHash
    #
    # @numHash.setter
    # def numHash(self, numHash):
    #     self.c_send.numHash = numHash
