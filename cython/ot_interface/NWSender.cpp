#include "NWSender.h"
#define ENABLE_WOLFSSL

#include <cryptoTools/Common/Defines.h>
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/IOService.h>

using namespace osuCrypto;

void send(){
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
    ::std::cout << "Server: Connection established." << ::std::endl;
    cA.send("Nachricht A");
    cB.send("Nachricht B");
    // Clean-Up
    cA.close();
    cB.close();
    serverA.stop();
    serverB.stop();
    ios.stop();
}

void sendOwnSocket(){


    int n = 0;
    IOService ios(n); //IO Service with as many threads as cores
    ::std::string serverIP = "127.0.0.1";
    u32 serverPort = 1213;
    ::std::string conNameA = "con1"; //Name of the connection, multiple connections can be multiplexed on same port
    ::std::string conNameB = "con2";
    Session serverA(ios,serverIP,serverPort,EpMode::Server,conNameA); //Session and Endpoint are the same thing!
    Endpoint serverB(ios,serverIP,serverPort,EpMode::Server,conNameB);
    Channel ownSockA = serverA.addChannel();
    Channel ownSockB = serverB.addChannel();
    ownSockA.waitForConnection();
    ownSockB.waitForConnection();
    ::std::cout << "Server: Connectionto own sockets established." << ::std::endl;

    typedef Channel MySocket;
    Channel cA(ios, new SocketAdapter<MySocket>(ownSockA)) ; // Create OC channel from own channel
    Channel cB(ios, new SocketAdapter<MySocket>(ownSockB));
    cA.waitForConnection();
    cB.waitForConnection();
    ::std::cout << "Server: Connectionto high level sockets established." << ::std::endl;
    cA.send("Nachricht A");
    ::std::cout << "Server sent msg A." << ::std::endl;
    cB.send("Nachricht B");
    ::std::cout << "Server sent msg B." << ::std::endl;
    // Clean-Up
    cA.close();
    cB.close();
    ::std::cout << "Server: High Level sockets closed." << ::std::endl;
    ownSockA.close();
    ownSockB.close();
    ::std::cout << "Server: Own sockets closed." << ::std::endl;
    serverA.stop();
    serverB.stop();
    ios.stop();

    //cleanup_openssl();
}

void sendViaTLS(){

    TLSContext ctx;
    error_code e;
    ctx.init(TLSContext::Mode::Server, e);
    if(e){
        ::std::cout << "TLS initialization failed: " << e << ::std::endl;
        exit(-1);
    }
    ctx.loadKeyPairFile("../../data/certs/keyserver.cert", "../../data/certs/keyserver.key", e);
    if(e){
        ::std::cout << "Loading TLS key files failed: " << e << ::std::endl;
        exit(-1);
    }

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
    ::std::cout << "Server: Connection established." << ::std::endl;
    cA.send("Nachricht A");
    cB.send("Nachricht B");
    // Clean-Up
    cA.close();
    cB.close();
    serverA.stop();
    serverB.stop();
    ios.stop();
}
