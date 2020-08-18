#include "OTReceiver.h"
#define ENABLE_WOLFSSL

#include "util.h"

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/IOService.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/Session.h>
#include <cryptoTools/Common/Log.h>

#include <libOTe/NChooseOne/NcoOtExt.h>

#include <libOTe/NChooseOne/Oos/OosNcoOtReceiver.h>
#include <libOTe/NChooseOne/Oos/OosNcoOtSender.h>

#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtSender.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtReceiver.h>

// For BaseOTs
#include <libOTe/TwoChooseOne/IknpOtExtReceiver.h>
#include <libOTe/TwoChooseOne/IknpOtExtSender.h>
#include "libOTe/TwoChooseOne/KosOtExtSender.h"
#include "libOTe/TwoChooseOne/KosOtExtReceiver.h"

#include <iostream>
#include <thread>


OTReceiver::OTReceiver(){}

std::vector<std::pair<oc::u64, oc::u64>> OTReceiver::execute(std::vector< oc::u64> choices, bool tls){

    if(inputBitCount > 76 && maliciousSecure){
        throw std::logic_error("OOS16 allows max. 76Bit inputs.");
    }

    oc::u64 numOTs = totalOTs / numThreads;

    oc::IOService ios(0);
    oc::Session  ep0;
    if (tls){
        struct stat buffer;
        if (stat (rootCA.c_str(), &buffer) != 0){
            ::std::cerr << "Root CA file does not exist: '"<< rootCA << "'." << ::std::endl;
            exit(-1);
        }
        oc::TLSContext ctx;
        oc::error_code e;
        ctx.init(oc::TLSContext::Mode::Client, e);
        if(e){
            ::std::cerr << "TLS initialization failed: " << e << ::std::endl;
            exit(-1);
        }
        ctx.loadCertFile(rootCA, e);
        if(e){
            ::std::cerr << "Loading TLS root certificate failed: " << e << ::std::endl;
            exit(-1);
        }
        ep0.start(ios, hostName, port, oc::SessionMode::Client, ctx, connectionName);
    }else{
        ep0.start(ios, hostName, port, oc::SessionMode::Client, connectionName);
    }

    std::vector<oc::Channel> chls(numThreads);
    for (int i = 0; i < numThreads; ++i)
        chls[i] = ep0.addChannel();
    _debugr("Prepatation done.");
    std::vector<oc::block> blockRes;
    if(maliciousSecure)
        blockRes = _execute<oc::OosNcoOtReceiver>(choices, chls);
    else
        blockRes = _execute<oc::KkrtNcoOtReceiver>(choices, chls);
    _debugr("_execute done. Cleaning up.");
    for (int i = 0; i < numThreads; i++){
        chls[i].close();
    }
    ep0.stop();
    ios.stop();
    
    std::vector<std::pair<oc::u64, oc::u64>> res (totalOTs);
    for(int i = 0; i < res.size(); i++){
        res[i] = std::make_pair((oc::u64)blockRes[i][1], (oc::u64)blockRes[i][0]);
    }
    
    return res;
}

template<typename  NcoOtReceiver>
void fixedGenBaseOTsIKNP(NcoOtReceiver &recv, oc::PRNG &prng, oc::Channel &chl){
    // The library function NcoOtReceiver::genBaseOts is broken, hence we need
    // this fix. This uses IKNP --> Not malicious secure.
    _debugr("Using IKNP for base OTs.");
    if(recv.isMalicious()){
        throw std::logic_error("IKNP base OT cannot be used for malicious secure OTs.");
    }
    auto count = recv.getBaseOTCount();
    std::vector<std::array<oc::block, 2>> msgs(count);
    oc::IknpOtExtSender sender;
    sender.genBaseOts(prng, chl);
    sender.send(msgs, prng, chl);
    recv.setBaseOts(msgs, prng, chl);
}

template<typename  NcoOtReceiver>
void fixedGenBaseOTsKOS(NcoOtReceiver &recv, oc::PRNG &prng, oc::Channel &chl){
    // The library function NcoOtReceiver::genBaseOts is broken, hence we need
    // this fix. This uses KOS --> malicious secure.
    _debugs("Using KOS for base OTs.");
    auto count = recv.getBaseOTCount();
    std::vector<std::array<oc::block, 2>> msgs(count);
    oc::KosOtExtSender sender;
    sender.genBaseOts(prng, chl);
    sender.send(msgs, prng, chl);
    recv.setBaseOts(msgs, prng, chl);
}

template<typename  NcoOtReceiver>
void fixedGenBaseOTs(NcoOtReceiver &recv, oc::PRNG &prng, oc::Channel &chl){
    // The library function NcoOtReceiver::genBaseOts is broken, hence we need
    // this fix.
    if(recv.isMalicious()){
        fixedGenBaseOTsKOS<NcoOtReceiver>(recv, prng, chl);
    }else{
        fixedGenBaseOTsIKNP<NcoOtReceiver>(recv, prng, chl);
    }
}

template<typename  NcoOtReceiver>
std::vector<oc::block> OTReceiver::_execute(std::vector<oc::u64> choices, std::vector<oc::Channel> &chls){
    
    oc::u64 numOTs = totalOTs / numThreads;
    std::vector<NcoOtReceiver> recvers(numThreads);
    // ::std::cout << "Using: " << typeid(NcoOtReceiver).name() << ::std::endl;
    
    recvers[0].configure(maliciousSecure, statSecParam, inputBitCount);

    oc::PRNG prng(oc::sysRandomSeed());
    _debugr("Generate Base OTs.");
    recvers[0].genBaseOts(prng, chls[0]);
    //fixedGenBaseOTs<NcoOtReceiver>(recvers[0], prng, chls[0]);
    _debugr("Base OTs done.");

    for (int i = 1; i < numThreads; ++i)
        recvers[i] = recvers[0].splitBase();
        
    std::vector<oc::block>recvMsgs(numOTs); //threading?

    auto recvRoutine = [&](int k){
        _debugr("Start receiving...");
        auto& chl = chls[k];
        oc::PRNG prng(oc::sysRandomSeed());
        recvers[k].receiveChosen(numChosenMsgs, recvMsgs, choices, prng, chl);
        _debugr("Receiving done.");
    };

    std::vector<std::thread> thds(numThreads);

    for (int k = 0; k < numThreads; ++k)
        thds[k] = std::thread(recvRoutine, k);

    for (int k = 0; k < numThreads; ++k)
        thds[k].join();

    return recvMsgs;
}


