#distutils: language = c++
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""

from libcpp.string cimport string
from libcpp cimport bool
from libc.stdint cimport uint8_t
from libcpp.vector cimport vector
from libcpp.pair cimport pair

from cOTInterface cimport OTReceiver

cdef class PyOTReceiver:
    cdef OTReceiver c_recv

    def execute(self, choices, tls):
        if self.maliciousSecure and self.inputBitCount > 76:
            raise RuntimeError(
                "Malicious Secure OTs only allow an inputBitCount <= 76!")
        res = self.c_recv.execute(choices, tls)
        resMerge = []
        for val in res:
            high = val.first
            low = val.second
            resMerge.append((high << 64) + (low % 2**64))
        return resMerge

    @property
    def totalOTs(self):
        return self.c_recv.totalOTs

    @totalOTs.setter
    def totalOTs(self, totalOTs):
        self.c_recv.totalOTs = totalOTs

    @property
    def numThreads(self):
        return self.c_recv.numThreads

    @numThreads.setter
    def numThreads(self, numThreads):
        self.c_recv.numThreads = numThreads

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

    @property
    def maliciousSecure(self):
        return self.c_recv.maliciousSecure

    @maliciousSecure.setter
    def maliciousSecure(self, maliciousSecure):
        self.c_recv.maliciousSecure = maliciousSecure

    @property
    def statSecParam(self):
        return self.c_recv.statSecParam

    @statSecParam.setter
    def statSecParam(self, statSecParam):
        self.c_recv.statSecParam = statSecParam

    @property
    def inputBitCount(self):
        return self.c_recv.inputBitCount

    @inputBitCount.setter
    def inputBitCount(self, inputBitCount):
        self.c_recv.inputBitCount = inputBitCount

    @property
    def numChosenMsgs(self):
        return self.c_recv.numChosenMsgs

    @numChosenMsgs.setter
    def numChosenMsgs(self, numChosenMsgs):
        self.c_recv.numChosenMsgs = numChosenMsgs


from cOTInterface cimport OTSender

cdef class PyOTSender:
    cdef OTSender c_send

    def executeDiff(self, sendMessages, tls):
        if self.maliciousSecure and self.inputBitCount > 76:
            raise RuntimeError(
                "Malicious Secure OTs only allow an inputBitCount <= 76!")
        sendMessagesWithPairs = []
        for msgVct in sendMessages:
            sendMessagesWithPairsVect = []
            for msg in msgVct:
                sendMessagesWithPairsVect.append([msg>>64, msg % (2**64)])
            sendMessagesWithPairs.append(sendMessagesWithPairsVect)
        self.c_send.executeDiff(sendMessagesWithPairs, tls)

    def executeSame(self, sendMessages, tls):
        if self.maliciousSecure and self.inputBitCount > 76:
            raise RuntimeError(
                "Malicious Secure OTs only allow an inputBitCount <= 76!")
        sendMessagesWithPairsVect = []
        for msg in sendMessages:
            sendMessagesWithPairsVect.append([msg>>64, msg % (2**64)])
        self.c_send.executeSame(sendMessagesWithPairsVect, tls)

    @property
    def totalOTs(self):
        return self.c_send.totalOTs

    @totalOTs.setter
    def totalOTs(self, totalOTs):
        self.c_send.totalOTs = totalOTs

    @property
    def numThreads(self):
        return self.c_send.numThreads

    @numThreads.setter
    def numThreads(self, numThreads):
        self.c_send.numThreads = numThreads

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

    @property
    def maliciousSecure(self):
        return self.c_send.maliciousSecure

    @maliciousSecure.setter
    def maliciousSecure(self, maliciousSecure):
        self.c_send.maliciousSecure = maliciousSecure

    @property
    def statSecParam(self):
        return self.c_send.statSecParam

    @statSecParam.setter
    def statSecParam(self, statSecParam):
        self.c_send.statSecParam = statSecParam

    @property
    def inputBitCount(self):
        return self.c_send.inputBitCount

    @inputBitCount.setter
    def inputBitCount(self, inputBitCount):
        self.c_send.inputBitCount = inputBitCount

    @property
    def numChosenMsgs(self):
        return self.c_send.numChosenMsgs

    @numChosenMsgs.setter
    def numChosenMsgs(self, numChosenMsgs):
        self.c_send.numChosenMsgs = numChosenMsgs
