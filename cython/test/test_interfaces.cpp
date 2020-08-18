/*
    Test OT and PSI interfaces.

    Copyright (c) 2020.
    @author: Erik Buchholz
    @maintainer: Erik Buchholz
    @email: buchholz@comsys.rwth-aachen.de
*/

#define CATCH_CONFIG_MAIN
#define ENABLE_WOLFSSL
#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/IOService.h>
#include <libOTe/TwoChooseOne/IknpOtExtReceiver.h>
#include <libOTe/TwoChooseOne/IknpOtExtSender.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtReceiver.h>
#include <libOTe/NChooseOne/Kkrt/KkrtNcoOtSender.h>
#include "catch.hpp"
#include "OTReceiver.h"
#include "OTSender.h"
#include "util.h"
#include "PSIReceiver.h"
#include "PSISender.h"

using namespace osuCrypto;

#define SERVERCERT "certs/keyserver.crt"
#define SERVERKEY "certs/keyserver.key"
#define ROOTCA "certs/rootCA.crt"
#define TOTALOTS 10
#define SETSIZE 2<<10
#define DEBUG 0

TEST_CASE( "Network Connections are tested without TLS", "[Simple NW]" ) {
    int n = 0;
    IOService ios(n); //IO Service with as many threads as cores
    ::std::string serverIP = "127.0.0.1";
    u32 serverPort = 1213;
    ::std::string conNameA = "con1"; //Name of the connection, multiple connections can be multiplexed on same port
    ::std::string conNameB = "con2";
    Endpoint clientA(ios,serverIP,serverPort,EpMode::Client,conNameA);
    Session clientB(ios,serverIP,serverPort,EpMode::Client,conNameB);
    Channel cA = clientA.addChannel();
    Channel cB = clientB.addChannel();

    //Sender Thread
    std::thread send_thrd([&]() {
        int n = 0;
        IOService ios(n); //IO Service with as many threads as cores
        ::std::string serverIP = "127.0.0.1";
        u32 serverPort = 1213;
        ::std::string conNameA = "con1"; //Name of the connection, multiple connections can be multiplexed on same port
        ::std::string conNameB = "con2";
        Session serverA(ios,serverIP,serverPort,EpMode::Server,conNameA); //Session and Endpoint are the same thing!
        Endpoint serverB(ios,serverIP,serverPort,EpMode::Server,conNameB);
        Channel cA = serverA.addChannel();
        Channel cB = serverB.addChannel();
        cA.waitForConnection();
        cB.waitForConnection();
        cA.send("A");
        cB.send("B");
        // Clean-Up
        cA.close();
        cB.close();
        serverA.stop();
        serverB.stop();
        ios.stop();
    });
    //std::this_thread::sleep_for(std::chrono::seconds(1));
    // Execute receiver
    cA.waitForConnection();
    cB.waitForConnection();
    ::std::string destA;
    ::std::string destB;
    cA.recv(destA);
    cB.recv(destB);
    // Close Thread
    send_thrd.join();

    // Clean-Up
    cA.close();
    cB.close();
    clientA.stop();
    clientB.stop();
    ios.stop();

    // Check results
    REQUIRE(destA.compare("A"));
    REQUIRE(destB.compare("B"));
}

TEST_CASE( "Network Connections are tested with TLS", "[TLS NW]" ) {
    struct stat buffer;
    if (stat ("certs/rootCA.crt", &buffer) != 0){
        WARN("Tests have to be started from cython with valid 'certs' subdirectory.");
        REQUIRE(false);
    }

    TLSContext ctx;
    error_code e;
    ctx.init(TLSContext::Mode::Client, e);
    REQUIRE_FALSE(e);
    ctx.loadCertFile(ROOTCA, e);
    REQUIRE_FALSE(e);

    int n = 0;
    IOService ios(n); //IO Service with as many threads as cores
    ::std::string serverIP = "127.0.0.1";
    u32 serverPort = 1213;
    ::std::string conNameA = "con1"; //Name of the connection, multiple connections can be multiplexed on same port
    ::std::string conNameB = "con2";
    Endpoint clientA(ios,serverIP,serverPort,EpMode::Client,ctx, conNameA);
    Session clientB(ios,serverIP,serverPort,EpMode::Client,ctx, conNameB);
    Channel cA = clientA.addChannel();
    Channel cB = clientB.addChannel();

    // Sender Thread
    std::thread send_thrd([&]() {
        TLSContext ctx;
        error_code e;
        ctx.init(TLSContext::Mode::Server, e);
        REQUIRE_FALSE(e);
        ctx.loadKeyPairFile(SERVERCERT, SERVERKEY, e);
        REQUIRE_FALSE(e);
        int n = 0;
        IOService ios(n); //IO Service with as many threads as cores
        ::std::string serverIP = "127.0.0.1";
        u32 serverPort = 1213;
        ::std::string conNameA = "con1"; //Name of the connection, multiple connections can be multiplexed on same port
        ::std::string conNameB = "con2";
        Session serverA(ios,serverIP,serverPort,EpMode::Server,ctx, conNameA); //Session and Endpoint are the same thing!
        Endpoint serverB(ios,serverIP,serverPort,EpMode::Server,ctx, conNameB);
        Channel cA = serverA.addChannel();
        Channel cB = serverB.addChannel();
        cA.waitForConnection();
        cB.waitForConnection();
        cA.send("A");
        cB.send("B");
        // Clean-Up
        cA.close();
        cB.close();
        serverA.stop();
        serverB.stop();
        ios.stop();
    });
    //std::this_thread::sleep_for(std::chrono::seconds(1));

    // Execute receiver
    cA.waitForConnection();
    cB.waitForConnection();
    ::std::string destA;
    ::std::string destB;
    cA.recv(destA);
    cB.recv(destB);
    send_thrd.join();

    // Clean-Up
    cA.close();
    cB.close();
    clientA.stop();
    clientB.stop();
    ios.stop();

    // Check results
    REQUIRE(destA.compare("A"));
    REQUIRE(destB.compare("B"));
}

void executeOT(bool tls, bool oos){
    if(tls){
        struct stat buffer;
        if (stat ("certs/rootCA.crt", &buffer) != 0){
            WARN("Tests have to be started from cython with valid 'certs' subdirectory.");
            REQUIRE(false);
        }
    }
    OTReceiver receiver;
    receiver.totalOTs = TOTALOTS;
    receiver.numChosenMsgs = SETSIZE;
    receiver.rootCA = ROOTCA;
    receiver.maliciousSecure = oos; // False implies KKRT

    std::vector<oc::u64> choices(receiver.totalOTs);
    for (oc::u64 i = 0; i < TOTALOTS; ++i)
        choices[i] = i % TOTALOTS;

    if (oos){
        INFO("This should throw a logic error because of bad inputBitlength.");
//        REQUIRE_THROWS_AS(receiver.execute(choices, tls), std::logic_error);
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
            INFO("This should throw a logic error because of bad inputBitlength.");
//            REQUIRE_THROWS_AS(sender.executeSame(sendMessages, tls),
//                              std::logic_error);
            sender.inputBitCount = 76; //OOS16 only supports up to 76 Bit
        }
        sender.executeSame(sendMessages, tls);
    });

    recvMsgs = receiver.execute(choices, tls);
    send_thrd.join();

    //Check
    for (int j = 0; j < TOTALOTS; j++) {
        INFO(
                "j: " + std::to_string(j) + ", First: " +
                std::to_string(recvMsgs[j].first) + ", Second: " +
                std::to_string(recvMsgs[j].second)
                );
        REQUIRE(recvMsgs[j].first == 0);
        REQUIRE(recvMsgs[j].second == j);
    }
}

TEST_CASE( "OT Interface with KKRT & without TLS", "[KKRT INT]" ) {
    executeOT(false, false);
}

TEST_CASE( "OT Interface with KKRT & TLS", "[KKRT INT TLS]" ) {
    executeOT(true, false);
}

TEST_CASE( "OT Interface with OOS16 & without TLS", "[OOS16]" ) {
    executeOT(false, true);
}

TEST_CASE( "OT Interface with OOS16 & TLS", "[OOS16 TLS]" ) {
    executeOT(true, true);
}

void executePSI(std::string scheme, bool tls){
    if (tls){
        struct stat buffer;
        if (stat ("certs/rootCA.crt", &buffer) != 0){
            WARN("Tests have to be started from cython with valid 'certs' subdirectory.");
            REQUIRE(false);
        }
    }
    oc::u64 setSize = 8;

    std::vector<oc::block> sendSet(setSize), recvSet(setSize);

    for (oc::u64 i = 0; i < setSize; i++){
        sendSet[i] = oc::toBlock(i,i);
        // Only every second Pair is a match
        recvSet[i] = oc::toBlock(i,i + i % 2);
    }

    //PSI setup
    Receiver recv;
    Sender send;
    std::vector<oc::u64> intersection;
    recv.setSize = setSize;
    send.setSize = setSize;

    // TLS
    send.tls = tls;
    send.serverCert = SERVERCERT;
    send.serverKey = SERVERKEY;
    recv.tls = tls;
    recv.rootCA = ROOTCA;

    //PSI excecution
    std::thread thrd([&]() {
        send.execute(scheme, sendSet);
    });

    //std::this_thread::sleep_for(std::chrono::seconds(1));
    intersection = recv.execute(scheme, recvSet);
    thrd.join();

    //Check
    for(oc::u64 i = 0; i < setSize; i++) {
        if (i % 2 == 0) {
            // Match
            REQUIRE(std::count(intersection.begin(), intersection.end(), i));
        } else {
            // No Match
            REQUIRE_FALSE(
                    std::count(intersection.begin(), intersection.end(), i));

        }
    }
}

TEST_CASE( "KKRT16 PSI without TLS", "[KKRT16]" ) {
    executePSI("KKRT16", false);
}

TEST_CASE( "KKRT16 PSI with TLS", "[KKRT16 TLS]" ) {
    executePSI("KKRT16", true);
}

TEST_CASE( "RR16 PSI without TLS", "[RR16]" ) {
    executePSI("RR16", false);
}

TEST_CASE( "RR16 PSI with TLS", "[RR16 TLS]" ) {
    executePSI("RR16", true);
}

TEST_CASE( "RR17 PSI without TLS", "[RR17]" ) {
    executePSI("RR17", false);
}

TEST_CASE( "RR17 PSI with TLS", "[RR17 TLS]" ) {
    executePSI("RR17", true);
}

//TEST_CASE( "GRR18 PSI without TLS", "[GRR18]" ) {
//    executePSI("GRR18", false);
//}
//
//TEST_CASE( "GRR18 PSI with TLS", "[GRR18 TLS]" ) {
//    executePSI("GRR18", true);
//}

// Not implemented because of bug in library
//TEST_CASE( "DRRT18 PSI without TLS", "[DRRT18]" ) {
//    executePSI("DRRT18", false);
//}
//
//TEST_CASE( "DRRT18 PSI with TLS", "[DRRT18 TLS]" ) {
//    executePSI("DRRT18", true);
//}

TEST_CASE("IKNP 1oo2 OT", "[IKNP]"){
    // The number of OTs.
    int totalOTs = 100;
    // Set size
    int setSize = 2;

    PRNG prng(sysRandomSeed());
    IOService ios(0);
    Channel senderChl = Session(ios, "localhost:1212", SessionMode::Server).addChannel();
    Channel recverChl = Session(ios, "localhost:1212", SessionMode::Client).addChannel();



    // Generate random values
    std::vector<std::array<block, 2>> sendMsgs(totalOTs);
    for (int i = 0; i < totalOTs; ++i) {
        sendMsgs[i] = { toBlock(i), toBlock(2 * i)};
    }
    // Random choices
    BitVector choices(totalOTs);
    for (int i = 0; i < totalOTs; ++i) {
        choices[i] = i % 2;
    }

    // The code to be run by the OT receiver.
    auto recverThread = std::thread([&]() {
        PRNG prng(sysRandomSeed());
        IknpOtExtReceiver recver;
        recver.genBaseOts(prng, recverChl);

        // Receive the messages
        std::vector<block> messages(totalOTs);
        recver.receiveChosen(choices, messages, prng, recverChl);

        for (int i = 0; i < totalOTs; ++i) {
            //std::cout << i << ": " << messages[i] << std::endl;
            INFO(std::to_string(i) + ": " + std::to_string(messages[i][0])+ std::to_string(messages[i][1]));
            REQUIRE(sendMsgs[i][choices[i]][0] == messages[i][0]);
            REQUIRE(sendMsgs[i][choices[i]][1] == messages[i][1]);
        }
    });


    IknpOtExtSender sender;
    sender.genBaseOts(prng, senderChl);

    // Send the messages.
    sender.sendChosen(sendMsgs, prng, senderChl);
    recverThread.join();
}

void dr(::std::string msg){
#if DEBUG
    ::std::cout << "Receiver: " << msg << ::std::endl;
#endif
}

void ds(::std::string msg){
#if DEBUG
    ::std::cout << "Sender: " << msg << ::std::endl;
#endif
}

TEST_CASE("KKRT 1oon OT", "[KKRT]"){
    // Constants----------------------------------------------------------------
    // The number of OTs.
    int totalOTs = 100;
    // Set size (# elements to choose from per OT)
    u64 setSize = 2 << 10;

    // Channel Setup------------------------------------------------------------
    PRNG prng(sysRandomSeed());
    IOService ios(0);
    Channel senderChl = Session(ios, "localhost:1212", SessionMode::Server).addChannel();
    Channel recverChl = Session(ios, "localhost:1212", SessionMode::Client).addChannel();

    // Generate random values---------------------------------------------------
    std::vector<block> sendMsgs(setSize);
    // Same for all OTs
    for (int i = 0; i < setSize; ++i) {
        sendMsgs[i] = toBlock(i);
    }
    // Random choices
    std::vector<u64> choices(totalOTs);
    for (int i = 0; i < totalOTs; ++i) {
        choices[i] = i % setSize;
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
        recv.init(totalOTs, prng, recverChl);
        dr("Init done.");

        // Receive the messages
        std::vector<block> messages(totalOTs);
        recv.receiveChosen(setSize, messages, choices, prng, recverChl);

        dr("Result: ");
        for (int i = 0; i < totalOTs; ++i) {
            INFO(std::to_string(i) + ": " + std::to_string(messages[i][0])+ std::to_string(messages[i][1]));
            REQUIRE(sendMsgs[i % setSize][0] == messages[i][0]);
            REQUIRE(sendMsgs[i % setSize][1] == messages[i][1]);
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
    sender.init(totalOTs, prng, senderChl);
    ds("Init done.");

    // Create Matrix
    Matrix<block> tmp(totalOTs, setSize);
    for(int i = 0; i < totalOTs; i++){
        for(int j = 0; j < setSize; j++){
            tmp(i,j) = sendMsgs[j];
        }
    }
    // Send the messages.
    sender.sendChosen(tmp, prng, senderChl);


    ds("Finished");
    recverThread.join();

}