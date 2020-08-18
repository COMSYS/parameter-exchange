#define DEBUG_WOLFSSL
#include "NWSender.h"
#include <iostream>
#include <wolfssl/wolfcrypt/logging.h>

int main(){
    // wolfSSL_Debugging_ON();
    std::cout << "Sender startet!\n";
    std::cout << "Test Simple Send.---------------------------------------------\n";
    send();
    std::cout << "Simple Send completed.----------------------------------------\n";
    std::cout << "Test own socket sending.--------------------------------------\n";
    sendOwnSocket();
    std::cout << "Test own socket completed.------------------------------------\n";
    std::cout << "TLS Socket Test.----------------------------------------------\n";
    sendViaTLS();
    std::cout << "TLS Socket Test completed.------------------------------------\n";
    std::cout << "Sender terminating! \n";
    return 0;
}