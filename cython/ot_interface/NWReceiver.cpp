#include "NWReceiver.h"
#define ENABLE_WOLFSSL

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/IOService.h>

using namespace osuCrypto;

void receive(){
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
    cA.waitForConnection();
    cB.waitForConnection();
    ::std::cout << "Client: Connection established." << ::std::endl;
    ::std::string destA;
    ::std::string destB;
    cA.recv(destA);
    cB.recv(destB);
    ::std::cout << "Client received on Channel A: " << destA << ::std::endl;
    ::std::cout << "Client received on Channel B: " << destB << ::std::endl;
    // Clean-Up
    cA.close();
    cB.close();
    clientA.stop();
    clientB.stop();
    ios.stop();
}   

void receiveOwnSocket(){
    int n = 0;
    IOService ios(n); //IO Service with as many threads as cores
    ::std::string serverIP = "127.0.0.1";
    u32 serverPort = 1213;
    ::std::string conNameA = "con1"; //Name of the connection, multiple connections can be multiplexed on same port
    ::std::string conNameB = "con2";
    Endpoint clientA(ios,serverIP,serverPort,EpMode::Client,conNameA);
    Session clientB(ios,serverIP,serverPort,EpMode::Client,conNameB);
    Channel ownSockA = clientA.addChannel();
    Channel ownSockB = clientB.addChannel();
    ownSockA.waitForConnection();
    ownSockB.waitForConnection();
    ::std::cout << "Client: Connection to own sockets established." << ::std::endl;
    
    typedef Channel MySocket;
    Channel cA(ios, new SocketAdapter<MySocket>(ownSockA)) ; // Create OC channel from own channel
    Channel cB(ios, new SocketAdapter<MySocket>(ownSockB));
    cA.waitForConnection();
    cB.waitForConnection();
    ::std::cout << "Client: Connection to high level established." << ::std::endl;
    ::std::string destA;
    ::std::string destB;
    cA.recv(destA);
    ::std::cout << "Client received on Channel A: " << destA << ::std::endl;
    cB.recv(destB);
    ::std::cout << "Client received on Channel B: " << destB << ::std::endl;

    // Clean-Up
    cA.close();
    cB.close();
    ::std::cout << "Client: High Level sockets closed." << ::std::endl;
    ownSockA.close();
    ownSockB.close();
    ::std::cout << "Client: Own Sockets closed." << ::std::endl;
    clientA.stop();
    clientB.stop();
    ios.stop();
} 

void receiveViaTLS(){

    TLSContext ctx;
    error_code e;
    ctx.init(TLSContext::Mode::Client, e);
    if(e){
        ::std::cout << "TLS initialization failed: " << e << ::std::endl;
        exit(-1);
    }
    ctx.loadCertFile("../../data/certs/rootCA.crt", e);
    if(e){
        ::std::cout << "Loading TLS root certificate failed: " << e << ::std::endl;
        exit(-1);
    }

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
    cA.waitForConnection();
    cB.waitForConnection();
    ::std::cout << "Client: Connection established." << ::std::endl;
    ::std::string destA;
    ::std::string destB;
    cA.recv(destA);
    cB.recv(destB);
    ::std::cout << "Client received on Channel A: " << destA << ::std::endl;
    ::std::cout << "Client received on Channel B: " << destB << ::std::endl;
    // Clean-Up
    cA.close();
    cB.close();
    clientA.stop();
    clientB.stop();
    ios.stop();
}
