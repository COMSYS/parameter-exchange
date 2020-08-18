#include "PSISender.h"

#include "cryptoTools/Crypto/PRNG.h"
#include "cryptoTools/Common/Defines.h"

#include "libPSI/MPSI/Rr17/Rr17a/Rr17aMPsiSender.h"
#include "libPSI/MPSI/Rr17/Rr17b/Rr17bMPsiSender.h"

#include "libPSI/MPSI/Rr16/AknBfMPsiSender.h"

#include "libPSI/MPSI/Grr18/Grr18MPsiSender.h"
#include "libPSI/MPSI/Grr18/Grr18Common.h"

#include "libPSI/PSI/KkrtPsiSender.h"

#include "libPSI/PSI/DrrnPsiServer.h"

#include "libOTe/NChooseOne/Kkrt/KkrtNcoOtReceiver.h"
#include "libOTe/NChooseOne/Kkrt/KkrtNcoOtSender.h"

#include "libOTe/NChooseOne/Oos/OosNcoOtReceiver.h"
#include "libOTe/NChooseOne/Oos/OosNcoOtSender.h"
#include "libOTe/NChooseOne/RR17/Rr17NcoOtReceiver.h"
#include "libOTe/NChooseOne/RR17/Rr17NcoOtSender.h"

#include "libOTe/TwoChooseOne/KosOtExtReceiver.h"
#include "libOTe/TwoChooseOne/KosOtExtSender.h"

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/IOService.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/Session.h>
#include <cryptoTools/Common/Log.h>


#include <chrono>
#include <thread>

Sender::Sender(){
}

void Sender::execute(std::string psiScheme, std::vector<std::pair<oc::u64, oc::u64>> inputSet){
    execute(stringToPSIScheme(psiScheme), inputSet);
}

void Sender::execute(std::string psiScheme, std::vector<oc::block> inputSet){
    execute(stringToPSIScheme(psiScheme), inputSet);
}

void Sender::execute(PSIScheme psiScheme, std::vector<std::pair<oc::u64, oc::u64>> inputSet){
    std::vector<oc::block> set(setSize);
    for(oc::u64 i = 0; i < setSize; i++){
        set[i] = oc::toBlock(inputSet[i].first, inputSet[i].second);
    }
    execute(psiScheme, set);
}

void Sender::execute(PSIScheme psiScheme, std::vector<oc::block> inputSet){   
    //Check if all important configs are set (setSize)
    if(setSize == 0){
        std::cout << "No valid set size was provided" << "\n";
    } 

    if (psiScheme == Drrt18){
        // Special channels necessary
        executeDrrt18(inputSet);
        return;
    }

    oc::IOService ios(0);
    oc::Session  ep0;
    _debug("Sender: Started IO service.");

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
        _debug("Sender: Using TLS.");
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
        _debug("Sender: No TLS.");
        ep0.start(ios, hostName, port, oc::SessionMode::Server, connectionName);
    }

    std::vector<oc::Channel> chls(numThreads);
    

    for(oc::u64 i = 0; i < numThreads; i++){
        chls[i] = ep0.addChannel("channel_" + std::to_string(i));
    }
    
    _debug("Sender: Channels created.");
    _debug("Sender: Start Execution:");
    
    switch(psiScheme){
        case Grr18: throw std::logic_error("Not implemented due to an error in the library.");//executeGrr18(inputSet, chls); break;
        case Rr17: executeRr17(inputSet, chls); break;
        case Rr16: executeRr16(inputSet, chls); break;
        case Dkt10: throw std::logic_error("Not implemented yet."); //executeDkt10(inputSet, chls); break;
        case Kkrt16: executeKkrt16(inputSet, chls); break;
    }
    _debug("Sender: Completed Execution.");
    
    for (oc::u64 i = 0; i < numThreads; i++)
    {
        chls[i].close();
    }
    
    ep0.stop();
    ios.stop();
    
}

// Different PSI schemes -------------------------------------------------------

void Sender::executeGrr18(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Sender: Using scheme GRR18.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::OosNcoOtReceiver otRecv;
    oc::OosNcoOtSender   otSend;

    oc::Grr18MPsiSender send;
    oc::mGrr18PrintWarning = false;
    send.mEpsBins = epsBin;

    
    send.init(setSize, statSecParam, chls, otSend, otRecv, prng.get<oc::block>(), binScaler,  bitSize);
    _debug("Sender: Init succeeded.");
    send.sendInput(set, chls);
    _debug("Sender: Matching succeeded.");
}

void Sender::executeRr17(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Sender: Using scheme RR17.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::Rr17NcoOtReceiver otRecv;
    oc::Rr17NcoOtSender   otSend;

    oc::Rr17aMPsiSender send;
    
    send.init(setSize, statSecParam, chls, otSend, otRecv, prng.get<oc::block>());
    _debug("Sender: Init succeeded.");
    send.sendInput(set, chls);
    _debug("Sender: Matching succeeded.");
}

void Sender::executeRr16(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Sender: Using scheme RR16.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::KosOtExtReceiver otRecv;
    oc::KosOtExtSender   otSend;

    oc::AknBfMPsiSender send;
    
    send.init(setSize, statSecParam, otSend, chls, prng.get<oc::block>());
    send.sendInput(set, chls);
}

void Sender::executeKkrt16(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Sender: Using scheme KKRT16.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::KkrtNcoOtSender otSend;

    oc::KkrtPsiSender send;
    
    send.init(setSize, setSize, statSecParam, chls, otSend, prng.get<oc::block>()); //TODO:investigate double setSize
    send.sendInput(set, chls);
}

 void Sender::executeDrrt18(std::vector<oc::block> set){
     _debug("Sender: Using scheme DRRT18.");
     throw std::logic_error("Not implemented yet.");
 }
