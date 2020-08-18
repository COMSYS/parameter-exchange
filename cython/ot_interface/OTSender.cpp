#include "OTSender.h"
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

#include <thread>
#include <iostream>
     
OTSender::OTSender(){}

void OTSender::executeDiff(std::vector<std::vector<std::pair<oc::u64, oc::u64>>> sendMessages, bool tls){

    if(inputBitCount > 76 && maliciousSecure){
        throw std::logic_error("OOS16 allows max. 76Bit inputs.");
    }

    oc::u64 numOTs = totalOTs / numThreads;

    oc::IOService ios(0);
    oc::Session  ep0;
    if (tls){
        struct stat buffer;
        if (stat (serverCert.c_str(), &buffer) != 0){
        ::std::cerr << "Server certificate file does not exist: '"<< serverCert << "'." << ::std::endl;
        exit(-1);
        }
        if (stat (serverKey.c_str(), &buffer) != 0){
        ::std::cerr << "Server key file does not exist: '"<< serverKey << "'." << ::std::endl;
        exit(-1);
        }
        oc::TLSContext ctx;
        oc::error_code e;
        ctx.init(oc::TLSContext::Mode::Server, e);
        if(e){
            ::std::cerr << "TLS initialization failed: " << e << ::std::endl;
            exit(-1);
        }
        ctx.loadKeyPairFile(serverCert, serverKey, e);
        if(e){
            ::std::cerr << "Loading TLS key files failed: " << e << ::std::endl;
            exit(-1);
        }
        ep0.start(ios, hostName, port, oc::SessionMode::Server, ctx, connectionName);
    }else{
        ep0.start(ios, hostName, port, oc::SessionMode::Server, connectionName);
    }
    
    std::vector<oc::Channel> chls(numThreads);
    for (int i = 0; i < numThreads; ++i)
        chls[i] = ep0.addChannel();
    
    oc::Matrix<oc::block> temp(numOTs, numChosenMsgs);
    for(int i = 0; i < numOTs; i++){
        for(int j = 0; j < numChosenMsgs; j++){
            temp(i,j) = oc::toBlock(sendMessages[i][j].first, sendMessages[i][j].second);
        }
    }

    if(maliciousSecure)
        _execute<oc::OosNcoOtSender>(temp, chls);
    else
        _execute<oc::KkrtNcoOtSender>(temp, chls);
    
    for (int i = 0; i < numThreads; i++){
        chls[i].close();
    }
    ep0.stop();
    ios.stop();

    
}

void OTSender::executeSame(std::vector<std::pair<oc::u64, oc::u64>> sendMessages, bool tls){
    oc::u64 numOTs = totalOTs / numThreads;

    if(inputBitCount > 76 && maliciousSecure){
        throw std::logic_error("OOS16 allows max. 76Bit inputs.");
    }

    oc::IOService ios(0);
    oc::Session  ep0;
    if (tls){
        struct stat buffer;
        if (stat (serverCert.c_str(), &buffer) != 0){
            ::std::cout << "Server certificate file does not exist: '"<< serverCert << "'." << ::std::endl;
            exit(-1);
        }
        if (stat (serverKey.c_str(), &buffer) != 0){
            ::std::cout << "Server key file does not exist: '"<< serverKey << "'." << ::std::endl;
            exit(-1);
        }
        oc::TLSContext ctx;
        oc::error_code e;
        ctx.init(oc::TLSContext::Mode::Server, e);
        if(e){
            ::std::cout << "TLS initialization failed: " << e << ::std::endl;
            exit(-1);
        }
        ctx.loadKeyPairFile(serverCert, serverKey, e);
        if(e){
            ::std::cout << "Loading TLS key files failed: " << e << ::std::endl;
            exit(-1);
        }
        ep0.start(ios, hostName, port, oc::SessionMode::Server, ctx, connectionName);
    }else{
        ep0.start(ios, hostName, port, oc::SessionMode::Server, connectionName);
    }
    
    
    std::vector<oc::Channel> chls(numThreads);
    for (int i = 0; i < numThreads; ++i)
        chls[i] = ep0.addChannel();

    std::vector<oc::block> temp(numChosenMsgs);
    for(int j = 0; j < numChosenMsgs; j++){
        temp[j] = oc::toBlock(sendMessages[j].first, sendMessages[j].second);
    }
    _debugs("Preparation done.");
    if(maliciousSecure)
        _execute<oc::OosNcoOtSender>(temp, chls);
    else
        _execute<oc::KkrtNcoOtSender>(temp, chls);
    _debugs("_execute done. Cleaning up.");
    for (int i = 0; i < numThreads; i++){
        chls[i].close();
    }
    ep0.stop();
    ios.stop();
}

template<typename NcoOtSender>
void fixedGenBaseOTsIKNP(NcoOtSender &sender, oc::PRNG &prng, oc::Channel &chl){
    // The library function NcoOtSender::genBaseOts is broken, hence we need
    // this fix. This uses IKNP --> Not malicious secure.
    _debugs("Using IKNP for base OTs.");
    if(sender.isMalicious()){
        throw std::logic_error("IKNP base OT cannot be used for malicious secure OTs.");
    }
    auto count = sender.getBaseOTCount();
    std::vector<oc::block> msgs(count);
    oc::BitVector bv(count);
    bv.randomize(prng);
    oc::IknpOtExtReceiver recver;
    recver.genBaseOts(prng, chl);
    recver.receive(bv, msgs, prng,  chl);
    sender.setBaseOts(msgs, bv, chl);
    _debugs("FixedGenBaseOTsIKNP done.");
}

template<typename NcoOtSender>
void fixedGenBaseOTsKOS(NcoOtSender &sender, oc::PRNG &prng, oc::Channel &chl){
    // The library function NcoOtSender::genBaseOts is broken, hence we need
    // this fix. This uses KOS --> malicious secure.
    _debugs("Using KOS for base OTs.");
    auto count = sender.getBaseOTCount();
    std::vector<oc::block> msgs(count);
    oc::BitVector bv(count);
    bv.randomize(prng);
    oc::KosOtExtReceiver recver;
    recver.genBaseOts(prng, chl);
    recver.receive(bv, msgs, prng, chl);
    sender.setBaseOts(msgs, bv, chl);
    _debugs("FixedGenBaseOTsKOS done.");
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

template<typename NcoOtSender>
void OTSender::_execute(oc::Matrix<oc::block> sendMessages, std::vector<oc::Channel> &chls){

    //::std::cout << "Using: " << typeid(NcoOtSender).name() << ::std::endl;
    std::vector<NcoOtSender> senders(numThreads);

    senders[0].configure(maliciousSecure, statSecParam, inputBitCount);
    oc::PRNG prng(oc::sysRandomSeed());
    _debugs("Generate Base OTs.");
    senders[0].genBaseOts(prng, chls[0]);
    //fixedGenBaseOTs<NcoOtSender>(senders[0], prng, chls[0]);
    _debugs("Base OTs done.");

    for (int i = 1; i < numThreads; ++i)
        senders[i] = senders[0].splitBase();
        
    auto sendRoutine = [&](int k){
        auto& chl = chls[k];
        oc::PRNG prng(oc::sysRandomSeed());
        _debugs("Start sending.");
        senders[k].sendChosen(sendMessages, prng, chl);
        _debugs("Done sending.");
    };

    std::vector<std::thread> thds(numThreads);
    for (int k = 0; k < numThreads; ++k)
        thds[k] = std::thread(sendRoutine, k);

    for (int k = 0; k < numThreads; ++k)
        thds[k].join();
}

template<typename NcoOtSender>
void OTSender::_execute(std::vector<oc::block> sendMessages, std::vector<oc::Channel> &chls){
    // This is a custom implementation of osuCrypto::NcoOtExtSender::sendChosen
    // that reduces overhead due to the use of the same vector for each sending.
    // Same result as translating the vector to a matrix and calling above
    // execute, but more performant.

    //::std::cout << "Using: " << typeid(NcoOtSender).name() << ::std::endl;

    std::vector<NcoOtSender> senders(numThreads);
    
    senders[0].configure(maliciousSecure, statSecParam, inputBitCount);
    oc::PRNG prng(oc::sysRandomSeed());
    _debugs("Generate Base OTs.");
    senders[0].genBaseOts(prng, chls[0]);
    //fixedGenBaseOTs<NcoOtSender>(senders[0], prng, chls[0]);
    _debugs("Base OTs done.");

    for (int i = 1; i < numThreads; ++i)
        senders[i] = senders[0].splitBase();
        
    auto sendRoutine = [&](int k){
        _debugs("Start sending.");
        auto& chl = chls[k];
        oc::PRNG prng(oc::sysRandomSeed());

        auto numMsgsPerOT = numChosenMsgs;

        if (senders[k].hasBaseOts() == false)
            throw std::runtime_error("call configure(...) and genBaseOts(...) first.");
        
        senders[k].init(totalOTs, prng, chl);
        _debugs("Init done.");
        senders[k].recvCorrection(chl);
        _debugs("Received corrections.");

        if (senders[k].isMalicious()){
            senders[k].check(chl, prng.get<oc::block>());
            _debugs("Checked.");
        }


        std::array<oc::u64, 2> choice{0,0};
        oc::u64& j = choice[0];

        oc::Matrix<oc::block> temp(totalOTs, numMsgsPerOT);
        for (oc::u64 i = 0; i < totalOTs; ++i)
        {
            for (j = 0; j < numMsgsPerOT; ++j)
            {
                senders[k].encode(i, choice.data(), &temp(i, j));
                temp(i, j) = temp(i, j) ^ sendMessages[j];
            }
        }
        _debugs("Encoded.");
        chl.asyncSend(std::move(temp));
        _debugs("Done sending.");
    };

    std::vector<std::thread> thds(numThreads);
    for (int k = 0; k < numThreads; ++k)
        thds[k] = std::thread(sendRoutine, k);

    for (int k = 0; k < numThreads; ++k)
        thds[k].join();
    _debugs("Leaving _execute.");
}
