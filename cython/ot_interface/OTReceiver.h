/*
    Purpose: to used by the party which should receive the OTs
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

#ifndef _OTVariants_OTReceiver_h_included
#define _OTVariants_OTReceiver_h_included

class OTReceiver {
    public:
    oc::u64 totalOTs = 2 << 10;
    oc::u64 numThreads = 1;
    std::string hostName = "127.0.0.1";
    oc::u32 port = 1213;
    std::string connectionName = "";
    std::string rootCA = "";
    
    bool maliciousSecure = false;
    oc::u64 statSecParam = 40;
    oc::u8 inputBitCount = 128; // the kkrt protocol default to 128 but oos can only do 76.
    oc::u64 numChosenMsgs = 2<<20; //Denotes N in one OT
    
    OTReceiver();
    std::vector<std::pair<oc::u64, oc::u64>> execute(std::vector< oc::u64> choices, bool tls=false);
    private:
    std::vector<oc::Channel> channels;
    template<typename  NcoOtReceiver>
    std::vector<oc::block> _execute(std::vector<oc::u64> choices, std::vector<oc::Channel> &chls);
    
    
};

#endif
