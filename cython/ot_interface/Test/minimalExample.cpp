//
// Created by Erik Buchholz on 27.02.20.
//
#include <string.h>
#include <stdio.h>
#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/IOService.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/Session.h>
#include <cryptoTools/Common/Log.h>
#include <cryptoTools/Crypto/PRNG.h>
#include <libOTe/NChooseOne/Oos/OosNcoOtReceiver.h>
#include <libOTe/NChooseOne/Oos/OosNcoOtSender.h>

#define LINE "------------------------------------------------------"
#define TOTALOTS 10
#define SETSIZE 2<<10

using namespace osuCrypto;

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
    // Sender Code -------------------------------------------------------------
    auto senderThread = std::thread([&]() {
        IOService ios(0);
        PRNG prng(sysRandomSeed());
        Channel senderChl = Session(ios, "127.0.0.1:1212", SessionMode::Server).addChannel();
        OosNcoOtSender sender;
        sender.configure(true, 40, 76);
        ::std::cout << "Sender: Configure done.\n";
        sender.genBaseOts(prng, senderChl);
        ::std::cout << "Sender: genBaseOts done.\n";

        // Create Matrix
        Matrix<block> tmp(TOTALOTS, SETSIZE);
        for(int i = 0; i < TOTALOTS; i++){
            for(int j = 0; j < SETSIZE; j++){
                tmp(i,j) = sendMsgs[j];
            }
        }
        // Send the messages.
        sender.sendChosen(tmp, prng, senderChl);
        ::std::cout << "Sender: Finished\n";
    });
    //--------------------------------------------------------------------------
    PRNG prng(sysRandomSeed());
    IOService ios(0);
    Channel recverChl = Session(ios, "127.0.0.1:1212", SessionMode::Client).addChannel();
    OosNcoOtReceiver recv;
    recv.configure(true, 40, 76);
    ::std::cout << "Receiver: " << "Configure done.\n";
    recv.genBaseOts(prng, recverChl);
    ::std::cout << "Receiver: " << "genBaseOts done.\n";

    // Receive the messages
    std::vector<block> messages(TOTALOTS);
    recv.receiveChosen(SETSIZE, messages, choices, prng, recverChl);

    ::std::cout << "Receiver: " << "Result: \n";
    for (int i = 0; i < TOTALOTS; ++i) {
        std::cout << i << ": " << messages[i] << std::endl;
    }
    senderThread.join();
}

int main(){
    oos();
    return 0;
}
