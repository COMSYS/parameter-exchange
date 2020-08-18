#include "OTSender.h"
#include <iostream>
#include <wolfssl/wolfcrypt/logging.h>

int main(){
    std::cout << "mainSend \n";
    OTSender sender;
    sender.totalOTs = 10;
    sender.numChosenMsgs = 2<<20;
    sender.serverCert = "../../data/certs/keyserver.crt";
    sender.serverKey = "../../data/certs/keyserver.key";

    //std::vector<std::vector<std::pair<oc::u64, oc::u64>>> sendMessages(sender.totalOTs, std::vector<std::pair<oc::u64, oc::u64>>(sender.numChosenMsgs));
    /*for(int i = 0; i < sender.totalOTs; i++){
        for(int j = 0; j < sender.numChosenMsgs; j++){
            sendMessages[i][j] = std::make_pair(i+j,i+j + 42);
        }
    }*/

    std::vector<std::pair<oc::u64, oc::u64>> sendMessages(sender.numChosenMsgs);
    for(int j = 0; j < sender.numChosenMsgs; j++){
        sendMessages[j] = std::make_pair(j,j + 42);
    }

    std::cout << "send calling execute without TLS------------------------------\n";
    sender.executeSame(sendMessages, false);
    std::cout << "send calling execute with TLS---------------------------------\n";
    sender.executeSame(sendMessages, true);
    return 0;
}
