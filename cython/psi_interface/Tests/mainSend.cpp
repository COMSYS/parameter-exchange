/**
    Purpose: Just for testing
    @author Chris Dax (Original)
    @author Erik Buchholz (Modifications)
*/

#include "PSISender.h"

#include <iostream>


int main(){
    std::cout << "Testing PSI Sender." << "\n";
    
    // Constants
    oc::u64 setSize = 100;
    std::string scheme = "KKRT16";
    
    //Create Test Values
    std::vector<std::pair<oc::u64, oc::u64>> sendSet(setSize);
    for (oc::u64 i = 0; i < setSize; ++i)
    {
	    sendSet[i] = std::make_pair(i,i);
    }

    //PSI setup
    Sender send;    
    send.setSize = setSize;
    send.serverCert = "../../data/certs/keyserver.crt";
    send.serverKey = "../../data/certs/keyserver.key";

    //PSI excecution
    send.execute(scheme, sendSet);
    
    return 0;
}