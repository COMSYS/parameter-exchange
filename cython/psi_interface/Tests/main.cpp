/**
    Purpose: Just for testing
    @author Chris Dax (Original)
    @author Erik Buchholz (Modifications)
*/

#include "util.h"
#include "PSIReceiver.h"
#include "PSISender.h"
#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/Endpoint.h>
#include <cryptoTools/Network/IOService.h>
#include <cryptoTools/Crypto/PRNG.h>

#include <iostream>
#include <chrono>

using namespace oc;

void officialTest(){
}


int main(){
//    officialTest();
//    _debug("Done.");
    // Constants
    oc::u64 setSize = 8;
    std::string scheme = "RR17";

    std::cout << "Full PSI Test. Scheme: " << scheme << "\n";

    std::vector<oc::block> sendSet(setSize), recvSet(setSize);
    for (oc::u64 i = 0; i < setSize; i++){
        sendSet[i] = oc::toBlock(i,i);
        // Only every second Pair is a match
        recvSet[i] = oc::toBlock(i,i + i % 2);
    }

    auto commStart = std::chrono::system_clock::now();
    //PSI setup
    Receiver recv;
    Sender send;
    std::vector<oc::u64> intersection;
    recv.setSize = setSize;
    send.setSize = setSize;


    // TLS
    send.tls = false;
    send.serverCert = "../data/certs/keyserver.crt";
    send.serverKey = "../data/certs/keyserver.key";
    recv.tls = false;
    recv.rootCA = "../data/certs/rootCA.crt";

    //For unblanced only
//    recv.serverSetSize = setSize;
//    send.serverSetSize = setSize;

    //PSI excecution
    std::thread thrd([&]() {
        std::cout << "Sender Thread starting." <<std::endl;
        send.execute(scheme, sendSet);
        std::cout << "Sender Thread terminating." <<std::endl;
    });

    std::this_thread::sleep_for(std::chrono::seconds(1));
    std::cout << "Receiver Thread starting." <<std::endl;
    intersection = recv.execute(scheme, recvSet);
    std::cout << "Receiver Thread terminating." <<std::endl;
    thrd.join();

    auto commEnd = std::chrono::system_clock::now();
    std::chrono::duration<double> seconds = commEnd - commStart;

    //Print results
    std::sort(intersection.begin(), intersection.end());
    for(oc::u64 i = 0; i < intersection.size(); i++){
        std::cout << intersection.at(i) << " : " << recvSet[intersection.at(i)] << "\n";
    }
    std::cout << "Communication took " << seconds.count() << "s for set sizes: " << sendSet.size() << " - " << recvSet.size() << " with intersection of " << intersection.size() << "\n";



    return 0;
}
