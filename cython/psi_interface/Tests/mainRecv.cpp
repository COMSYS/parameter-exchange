/**
    Purpose: Just for testing
    @author Chris Dax (Original)
    @author Erik Buchholz (Modifications)
*/

#include "PSIReceiver.h"
#include "cryptoTools/Common/Defines.h"

#include <iostream>


int main(){
    std::cout << "Testing PSI Receiver." << "\n";
    
    // Constants
    oc::u64 setSize = 100;
    std::string scheme = "KKRT16";
    
    //Create Test Values
    std::vector<oc::block> recvSet(setSize);
    for (oc::u64 i = 0; i < setSize; ++i)
    {
        recvSet[i] = oc::toBlock(i, i + i % 2);
        // Only every second Pair is a match
    }
    
    //PSI setup
    Receiver recv;
    recv.setSize = setSize;
    recv.rootCA = "../../data/certs/rootCA.crt";
    
    //PSI excecution
    std::vector<oc::u64> intersection;
    intersection = recv.execute(scheme, recvSet);
    
    //Print results
    std::cout << "Total Matches: " << intersection.size() << std::endl;
    std::sort(intersection.begin(), intersection.end());
    for(oc::u64 i = 0; i < intersection.size(); i++){
    	std::cout << intersection.at(i) << " : " << recvSet[intersection.at(i)] << "\n";
    }
    std::cout << "\n";
    
    return 0;
}