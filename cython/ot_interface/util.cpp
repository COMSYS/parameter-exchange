//
// Created by Erik Buchholz on 25.02.20.
//
#include "util.h"

void _debugs(std::string msg){
#if DEBUG
    ::std::cout << "Sender: " << msg << ::std::endl;
#endif
}
void _debugr(std::string msg){
#if DEBUG
    ::std::cout << "Receiver: " << msg << ::std::endl;
#endif
}