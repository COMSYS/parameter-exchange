/*
    Purpose: Test cryptoTools Network connections

    Copyright (c) 2020.
    @author: Erik Buchholz
    @maintainer: Erik Buchholz
    @email: buchholz@comsys.rwth-aachen.de
*/
#pragma once
#define ENABLE_WOLFSSL

void receive();
void receiveOwnSocket();
void receiveViaTLS();