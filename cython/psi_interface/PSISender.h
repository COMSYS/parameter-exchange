/*
    Purpose: to used by the party which should not receive the intersection

    Copyright (c) 2020.
    @author: Chris Dax
    @email: dax@comsys.rwth-aachen.de
    @maintainer: Erik Buchholz
    @email: buchholz@comsys.rwth-aachen.de
*/
#pragma once
#ifndef _PSIVariants_PSISender_h_included
#define _PSIVariants_PSISender_h_included

#include "util.h"
#include <cryptoTools/Network/Channel.h>
#include <cryptoTools/Network/IOService.h>

class Sender {
    public:
    oc::u64 statSecParam = 40;
    oc::u64 setSize = 0;

    // Connection Settings -----------------------------------------------------
    std::string hostName = "127.0.0.1";
    oc::u32 port = 1213;
    std::string connectionName = "StandardConnection";
    oc::u64 numThreads = 1;
    bool tls = true;
    std::string serverCert = "";
    std::string serverKey = "";
    // -------------------------------------------------------------------------
    // Only for GRR18: ---------------------------------------------------------
    double epsBin = 0.1;
    double binScaler = 12;
    oc::u64 bitSize = -1;
    // -------------------------------------------------------------------------
    // Only for DRRT18: --------------------------------------------------------
    // oc::u64 serverSetSize = 0;
    // oc::u64 numHash = 3;
    // -------------------------------------------------------------------------
    
    Sender();
   
    //Multiple verions of execute, string and pair facilitate python exposure
    void execute(std::string psiScheme, std::vector<std::pair<oc::u64, oc::u64>> inputSet);
    void execute(std::string psiScheme, std::vector<oc::block> inputSet);
    void execute(PSIScheme psiScheme, std::vector<std::pair<oc::u64, oc::u64>> inputSet);
    void execute(PSIScheme psiScheme, std::vector<oc::block> inputSet);
    
    private:   
    //All the different protocols implemented in libPSI, accessed via parameter in execute
    void executeGrr18(std::vector<oc::block> set, std::vector<oc::Channel> &chls);
    void executeRr17(std::vector<oc::block> set, std::vector<oc::Channel> &chls);
    void executeRr16(std::vector<oc::block> set, std::vector<oc::Channel> &chls);
    // void executeDkt10(std::vector<oc::block> set, std::vector<oc::Channel> &chls); // Needs relic
    void executeKkrt16(std::vector<oc::block> set, std::vector<oc::Channel> &chls);
    void executeDrrt18(std::vector<oc::block> set);
};







#endif
