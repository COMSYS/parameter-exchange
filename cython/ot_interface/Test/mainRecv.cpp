#include "OTReceiver.h"
#include <iostream>
#include <chrono>

int main(){
    std::cout << "mainRecv \n";
    OTReceiver receiver;
    receiver.totalOTs = 10;
    receiver.numChosenMsgs = 2<<20;
    receiver.rootCA = "../../data/certs/rootCA.crt";

    
    std::vector<oc::u64> choices(receiver.totalOTs); 
    for (oc::u64 i = 0; i < receiver.totalOTs; ++i)
        choices[i] = i%receiver.numChosenMsgs;
        
    std::vector<std::pair<oc::u64, oc::u64>>recvMsgs(receiver.totalOTs);
    std::cout << "recv calling execute without TLS------------------------------\n";
    auto commStart = std::chrono::system_clock::now(); 
    recvMsgs = receiver.execute(choices);
    auto commEnd = std::chrono::system_clock::now();  
    for(auto msg : recvMsgs){
        std::cout << oc::toBlock(msg.first,msg.second) << "\n";
    }
    std::chrono::duration<double> seconds = commEnd - commStart;
    std::cout << "Communication took " << seconds.count() << "s for " << receiver.totalOTs << " OTs, with N of " << receiver.numChosenMsgs << "\n";
    std::cout << "recv calling execute with TLS---------------------------------\n";
    commStart = std::chrono::system_clock::now(); 
    recvMsgs = receiver.execute(choices, true);
    commEnd = std::chrono::system_clock::now();  
    for(auto msg : recvMsgs){
        std::cout << oc::toBlock(msg.first,msg.second) << "\n";
    }
    seconds = commEnd - commStart;
    std::cout << "Communication took " << seconds.count() << "s for " << receiver.totalOTs << " OTs, with N of " << receiver.numChosenMsgs << "\n";
    
    return 0;
}
