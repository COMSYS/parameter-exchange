/*
    Purpose: Provide some helper functionality

    Copyright (c) 2020.
    @author: Chris Dax
    @email: dax@comsys.rwth-aachen.de
    @maintainer: Erik Buchholz
    @email: buchholz@comsys.rwth-aachen.de
*/
#pragma once
#ifndef _PSIVariants_util_h_included
#define _PSIVariants_util_h_included

#include "cryptoTools/Network/Channel.h"
#include <stdint.h>


enum PSIScheme {Grr18, Rr17, Rr16, Dkt10, Kkrt16, Drrt18}; //Dkt10 on hold until relic acquired, DRRT18 not implemented
// Working: RR16, KKRT16
        

std::string psiSchemeToString(PSIScheme psiScheme);
PSIScheme stringToPSIScheme(std::string schemeString);
void _debug(std::string msg);


#endif
