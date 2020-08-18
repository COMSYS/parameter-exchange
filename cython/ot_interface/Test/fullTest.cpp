//
// Created by Erik Buchholz on 26.02.20.
//
#define DEBUG 1
#include "OTReceiver.h"
#include "OTSender.h"

#include <string.h>
#include <stdio.h>

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/IOService.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/Session.h>
#include <cryptoTools/Common/Log.h>
#include <cryptoTools/Crypto/PRNG.h>

#include <libOTe/TwoChooseOne/IknpOtExtReceiver.h>
#include <libOTe/TwoChooseOne/IknpOtExtSender.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtReceiver.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtSender.h>
#include <libOTe/NChooseOne/Oos/OosNcoOtReceiver.h>
#include <libOTe/NChooseOne/Oos/OosNcoOtSender.h>
#include "libOTe/TwoChooseOne/KosOtExtSender.h"
#include "libOTe/TwoChooseOne/KosOtExtReceiver.h"

#define LINE "------------------------------------------------------"
#define SERVERCERT "certs/keyserver.crt"
#define SERVERKEY "certs/keyserver.key"
#define ROOTCA "certs/rootCA.crt"
#define TOTALOTS 10
#define SETSIZE 2<<10

void dr(::std::string msg){
    ::std::cout << "Receiver: " << msg << ::std::endl;
}

void ds(::std::string msg){
    ::std::cout << "Sender: " << msg << ::std::endl;
}

using namespace osuCrypto;

void kkrt(){
    ::std::cout << "Testing KKRT." << LINE << ::std::endl;
    // Channel Setup------------------------------------------------------------
    PRNG prng(sysRandomSeed());
    IOService ios(0);
    Channel senderChl = Session(ios, "127.0.0.1:1213", SessionMode::Server).addChannel();
    Channel recverChl = Session(ios, "127.0.0.1:1213", SessionMode::Client).addChannel();

    // Generate random values---------------------------------------------------
    std::vector<block> sendMsgs(SETSIZE);
    // Same for all OTs
    for (int i = 0; i < SETSIZE; ++i) {
        sendMsgs[i] = toBlock(i);
    }
    // Random choices
    std::vector<u64> choices(TOTALOTS);
    for (int i = 0; i < TOTALOTS; ++i) {
        choices[i] = i % SETSIZE;
    }
    // Receiver Code -----------------------------------------------------------
    auto recverThread = std::thread([&]() {
        PRNG prng(sysRandomSeed());
        KkrtNcoOtReceiver recv;
        recv.configure(false, 40, 128);
        dr("Configure done.");
        // Self Implementation of genBaseOTs because lib broken
        // recv.genBaseOts(prng, recverChl);
        auto count = recv.getBaseOTCount();
        std::vector<std::array<block, 2>> msgs(count);
        IknpOtExtSender sender;
        sender.genBaseOts(prng, recverChl);
        sender.send(msgs, prng, recverChl);
        recv.setBaseOts(msgs, prng, recverChl);
        dr("genBaseOts done.");

        // Receive the messages
        std::vector<block> messages(TOTALOTS);
        recv.receiveChosen(SETSIZE, messages, choices, prng, recverChl);

        dr("Result: ");
        for (int i = 0; i < TOTALOTS; ++i) {
            //std::cout << i << ": " << messages[i] << std::endl;
        }
        dr("Finished");
    });
    //--------------------------------------------------------------------------


    KkrtNcoOtSender sender;
    sender.configure(false, 40, 128);
    ds("Configure done.");
    // Self Implementation of genBaseOTs because lib broken
    // sender.genBaseOts(prng, senderChl);
    auto count = sender.getBaseOTCount();
    std::vector<block> msgs(count);
    BitVector bv(count);
    bv.randomize(prng);
    IknpOtExtReceiver recver;
    recver.genBaseOts(prng, senderChl);
    recver.receive(bv, msgs, prng,  senderChl);
    sender.setBaseOts(msgs, bv, senderChl);
    ds("genBaseOts done.");

    // Create Matrix
    Matrix<block> tmp(TOTALOTS, SETSIZE);
    for(int i = 0; i < TOTALOTS; i++){
        for(int j = 0; j < SETSIZE; j++){
            tmp(i,j) = sendMsgs[j];
        }
    }
    // Send the messages.
    sender.sendChosen(tmp, prng, senderChl);

    ds("Finished");
    recverThread.join();
}

void oos(){
    ::std::cout << "Testing OOS16." << LINE  << ::std::endl;
    // Generate random values---------------------------------------------------
    std::vector<block> sendMsgs(SETSIZE);
    // Same for all OTs
    for (int i = 0; i < SETSIZE; ++i) {
        sendMsgs[i] = toBlock(i);
    }
    // Random choices
    std::vector<u64> choices(TOTALOTS);
    for (int i = 0; i < TOTALOTS; ++i) {
        choices[i] = i % (SETSIZE);
    }
    // Sender Code -----------------------------------------------------------
    auto senderThread = std::thread([&]() {
        IOService ios(0);
        PRNG prng(sysRandomSeed());
        Channel senderChl = Session(ios, "127.0.0.1:1212", SessionMode::Server).addChannel();
        OosNcoOtSender sender;
        sender.configure(true, 40, 76);
        ds("Configure done.");
        // Self Implementation of genBaseOTs because lib broken
        sender.genBaseOts(prng, senderChl);
//        auto count = sender.getBaseOTCount();
//        std::vector<block> msgs(count);
//        BitVector bv(count);
//        bv.randomize(prng);
//        KosOtExtReceiver recver;
//        recver.genBaseOts(prng, senderChl);
//        recver.receive(bv, msgs, prng,  senderChl);
//        sender.setBaseOts(msgs, bv, senderChl);
        ds("genBaseOts done.");

        // Create Matrix
        Matrix<block> tmp(TOTALOTS, SETSIZE);
        for(int i = 0; i < TOTALOTS; i++){
            for(int j = 0; j < SETSIZE; j++){
                tmp(i,j) = sendMsgs[j];
            }
        }
        // Send the messages.
        sender.sendChosen(tmp, prng, senderChl);
        ds("Finished");
    });
    //--------------------------------------------------------------------------
    PRNG prng(sysRandomSeed());
    IOService ios(0);
    Channel recverChl = Session(ios, "127.0.0.1:1212", SessionMode::Client).addChannel();
    OosNcoOtReceiver recv;
    recv.configure(true, 40, 76);
    dr("Configure done.");
    // Self Implementation of genBaseOTs because lib broken
    recv.genBaseOts(prng, recverChl);
//    auto count = recv.getBaseOTCount();
//    std::vector<std::array<block, 2>> msgs(count);
//    KosOtExtSender sender;
//    sender.genBaseOts(prng, recverChl);
//    sender.send(msgs, prng, recverChl);
//    recv.setBaseOts(msgs, prng, recverChl);
    dr("genBaseOts done.");

    // Receive the messages
    std::vector<block> messages(TOTALOTS);
    recv.receiveChosen(SETSIZE, messages, choices, prng, recverChl);

    dr("Result: ");
    for (int i = 0; i < TOTALOTS; ++i) {
        std::cout << i << ": " << messages[i][0] << ", " << messages[i][1] << std::endl;
    }
    dr("Finished");

    senderThread.join();
}

void executeOT(bool tls, bool oos){
    std::string type;
    if(oos){
        type = "OOS16";
    }else{
        type = "KKRT";
    }
    ::std::cout << "Testing " << type << LINE << "\n";
    OTReceiver receiver;
    receiver.totalOTs = TOTALOTS;
    receiver.numChosenMsgs = SETSIZE;
    receiver.rootCA = ROOTCA;
    receiver.maliciousSecure = oos; // False implies KKRT

    std::vector<oc::u64> choices(receiver.totalOTs);
    for (oc::u64 i = 0; i < TOTALOTS; ++i)
        choices[i] = i % TOTALOTS;

    if (oos){
        receiver.inputBitCount = 76; //OOS16 only supports up to 76 Bit
    }

    std::vector<std::pair<oc::u64, oc::u64>>recvMsgs(receiver.totalOTs);

    std::thread send_thrd([&]() {
        OTSender sender;
        sender.maliciousSecure = oos; // False implies KKRT
        sender.totalOTs = TOTALOTS;
        sender.numChosenMsgs = SETSIZE;
        sender.serverCert = SERVERCERT;
        sender.serverKey = SERVERKEY;
        std::vector <std::pair<oc::u64, oc::u64>> sendMessages(
                sender.numChosenMsgs);
        for (int j = 0; j < SETSIZE; j++) {
            sendMessages[j] = std::make_pair(0, j);
        }
        if (oos) {
            sender.inputBitCount = 76; //OOS16 only supports up to 76 Bit
        }
        sender.executeSame(sendMessages, tls);
    });

    recvMsgs = receiver.execute(choices, tls);
    send_thrd.join();

    //Check
    for (int j = 0; j < TOTALOTS; j++) {
        dr(
                "j: " + std::to_string(j) + ", First: " +
                std::to_string(recvMsgs[j].first) + ", Second: " +
                std::to_string(recvMsgs[j].second)
        );
    }
}

int main(){
    kkrt();
    oos();
    executeOT(false, false);
    return 0;
}