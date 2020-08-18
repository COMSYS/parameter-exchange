#include "PSIReceiver.h"

#include "cryptoTools/Crypto/PRNG.h"
#include "cryptoTools/Common/Defines.h"

#include "libPSI/MPSI/Rr17/Rr17a/Rr17aMPsiReceiver.h"
#include "libPSI/MPSI/Rr17/Rr17b/Rr17bMPsiReceiver.h"

#include "libPSI/MPSI/Rr16/AknBfMPsiReceiver.h"

#include "libPSI/MPSI/Grr18/Grr18MPsiReceiver.h"
#include "libPSI/MPSI/Grr18/Grr18Common.h"

#include "libPSI/PSI/KkrtPsiReceiver.h"

#include "libPSI/PSI/DrrnPsiClient.h"

#include "cryptoTools/Common/Defines.h"

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

Receiver::Receiver(){
}

std::vector<oc::u64> Receiver::execute(std::string psiScheme, std::vector<std::pair<oc::u64, oc::u64>> inputSet){
    return execute(stringToPSIScheme(psiScheme), inputSet);
}

std::vector<oc::u64> Receiver::execute(std::string psiScheme, std::vector<oc::block> inputSet){
    return execute(stringToPSIScheme(psiScheme), inputSet);
}

std::vector<oc::u64> Receiver::execute(PSIScheme psiScheme, std::vector<std::pair<oc::u64, oc::u64>> inputSet){
    std::vector<oc::block> set(setSize);
    for(oc::u64 i = 0; i < setSize; i++){
        set[i] = oc::toBlock(inputSet[i].first, inputSet[i].second);
    }
    
    return execute(psiScheme, set);
}

std::vector<oc::u64> Receiver::execute(PSIScheme psiScheme, std::vector<oc::block> inputSet){
    //Check if all important configs are setSize
    if(setSize == 0){
        std::cout << "No valid set size was provided" << "\n";
    }

    if (psiScheme == Drrt18){
        // Special channels necessary
        return executeDrrt18(inputSet);
    }

    oc::IOService ios(0);
    oc::Session  ep0;
    if (tls){
        struct stat buffer;
        if (stat (rootCA.c_str(), &buffer) != 0){
            ::std::cout << "Root CA file does not exist: '"<< rootCA << "'." << ::std::endl;
            exit(-1);
        }
        _debug("Receiver: Starting TLS.");
        oc::TLSContext ctx;
        oc::error_code e;
        ctx.init(oc::TLSContext::Mode::Client, e);
        if(e){
            ::std::cout << "TLS initialization failed: " << e << ::std::endl;
            exit(-1);
        }
        ctx.loadCertFile(rootCA, e);
        if(e){
            ::std::cout << "Loading TLS root certificate failed: " << e << ::std::endl;
            exit(-1);
        }
        ep0.start(ios, hostName, port, oc::SessionMode::Client, ctx, connectionName);
    }else{
        _debug("Receiver: Starting without TLS");
        ep0.start(ios, hostName, port, oc::SessionMode::Client, connectionName);
    }

    std::vector<oc::Channel> chls(numThreads);

    for(oc::u64 i = 0; i < numThreads; i++){
        chls[i] = ep0.addChannel("channel_" + std::to_string(i));
    }

    _debug("Receiver: Channels created.");
    _debug("Receiver: Start Execution:");
    
    std::vector<oc::u64> res;
    switch(psiScheme){
        case Grr18: throw std::logic_error("Not implemented due to an error in the library.");//res = executeGrr18(inputSet, chls); break;
        case Rr17: res = executeRr17(inputSet, chls); break;
        case Rr16: res = executeRr16(inputSet, chls); break;
        case Dkt10: throw std::logic_error("Not implemented yet.");//res = executeDkt10(inputSet, chls); break;
        case Kkrt16: res = executeKkrt16(inputSet, chls); break;
        default: throw std::logic_error("Unknown PSI scheme chosen.");
    }
    _debug("Receiver: Completed Execution.");
    
    for (oc::u64 i = 0; i < numThreads; i++)
    {
        chls[i].close();
    }
    ep0.stop();
    ios.stop();

    return res;
}

// Different PSI schemes -------------------------------------------------------

std::vector<oc::u64> Receiver::executeGrr18(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Receiver: Using scheme GRR18.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::OosNcoOtReceiver otRecv;
    oc::OosNcoOtSender   otSend;

    oc::Grr18MPsiReceiver recv;
    oc::mGrr18PrintWarning = false;
    recv.mEpsBins = epsBin;

    
    recv.init(setSize, statSecParam, chls, otRecv, otSend,
              prng.get<oc::block>(), binScaler,  bitSize);
    _debug("Receiver: Init succeeded.");
    recv.sendInput(set, chls);
    _debug("Receiver: Matching succeeded.");
    return recv.mIntersection;
}

std::vector<oc::u64> Receiver::executeRr17(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Receiver: Using scheme RR17.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::Rr17NcoOtReceiver otRecv;
    oc::Rr17NcoOtSender   otSend;

    oc::Rr17aMPsiReceiver recv;

    recv.init(setSize, statSecParam, chls, otRecv, otSend,
              prng.get<oc::block>());
    _debug("Receiver: Init succeeded.");
    recv.sendInput(set, chls);
    _debug("Receiver: Matching succeeded.");
    return recv.mIntersection;
}

std::vector<oc::u64> Receiver::executeRr16(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Receiver: Using scheme RR16.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::KosOtExtReceiver otRecv;
    oc::KosOtExtSender   otSend;

    oc::AknBfMPsiReceiver recv;
    
    recv.init(setSize, statSecParam, otRecv, chls,
              prng.get<oc::block>());
    recv.sendInput(set, chls);
    return recv.mIntersection;
}

std::vector<oc::u64> Receiver::executeKkrt16(std::vector<oc::block> set, std::vector<oc::Channel> &chls){
    _debug("Receiver: Using scheme KKRT16.");
    oc::PRNG prng(_mm_set_epi32(4253465, 3434565, 234435, 23987045));
    oc::KkrtNcoOtReceiver otRecv;

    oc::KkrtPsiReceiver recv;
    
    recv.init(setSize, setSize, statSecParam, chls, otRecv,
              prng.get<oc::block>());
    recv.sendInput(set, chls);
    return recv.mIntersection;
}

 std::vector<oc::u64> Receiver::executeDrrt18(std::vector<oc::block> set){
     _debug("Receiver: Using scheme DRRT18.");
     throw std::logic_error("Not implemented yet.");
 }
