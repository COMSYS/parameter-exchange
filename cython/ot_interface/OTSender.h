/*
    Purpose: to used by the party which should send the OTs
    Copyright (c) 2020.
    @author: Chris Dax
    @email: dax@comsys.rwth-aachen.de
    @maintainer: Erik Buchholz
    @email: buchholz@comsys.rwth-aachen.de
*/
#pragma once
#define ENABLE_WOLFSSL
#include <string>
#include <vector>
#include "cryptoTools/Network/Channel.h"
#include <stdint.h>

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/IOService.h>
#include <cryptoTools/Network/Session.h>
#include <cryptoTools/Common/Log.h>

#include "libOTe/NChooseOne/Oos/OosNcoOtReceiver.h"
#include "libOTe/NChooseOne/Oos/OosNcoOtSender.h"

#ifndef _OTVariants_OTSender_h_included
#define _OTVariants_OTSender_h_included

class OTSender {
    public:
    oc::u64 totalOTs = 2 << 10;
    oc::u64 numThreads = 1;
    std::string hostName = "127.0.0.1";
    oc::u32 port = 1213;
    std::string connectionName = "";
    std::string serverCert = "";
    std::string serverKey = "";
    
    bool maliciousSecure = false;
    oc::u64 statSecParam = 40;
    oc::u8 inputBitCount = 128; // the kkrt protocol default to 128 but oos can only do 76.
    oc::u64 numChosenMsgs = 2<<20; //Denotes N in one OT
    
     
    OTSender();
    void executeDiff(std::vector<std::vector<std::pair<oc::u64, oc::u64>>> sendMessages, bool tls=false);
    void executeSame(std::vector<std::pair<oc::u64, oc::u64>> sendMessages, bool tls=false);

    private:
    template<typename NcoOtSender>
    void _execute(oc::Matrix<oc::block> sendMessages, std::vector<oc::Channel> &chls);
    template<typename NcoOtSender>
    void _execute(std::vector<oc::block> sendMessages, std::vector<oc::Channel> &chls);
};

#endif
