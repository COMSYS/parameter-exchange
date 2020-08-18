#define DEBUG_WOLFSSL
#include "NWReceiver.h"
#include <iostream>
#include <wolfssl/wolfcrypt/logging.h>

int main(){
    // wolfSSL_Debugging_ON();
    std::cout << "Receiver started!\n";
    std::cout << "Test Simple Receive.------------------------------------------\n";
    receive();
    std::cout << "Simple Receive completed.-------------------------------------\n";
    std::cout << "Test own socket receving.-------------------------------------\n";
    receiveOwnSocket();
    std::cout << "Own Socket receiving completed.-------------------------------\n";
    std::cout << "TLS Socket Test.----------------------------------------------\n";
    receiveViaTLS();
    std::cout << "TLS Socket Test completed.------------------------------------\n";
    std::cout << "Receiver terminating! \n";
    return 0;
}