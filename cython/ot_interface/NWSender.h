/*
    Purpose: Test cryptoTools Network connections

    Copyright (c) 2020.
    @author: Erik Buchholz
    @maintainer: Erik Buchholz
    @email: buchholz@comsys.rwth-aachen.de
*/
#pragma once
#define ENABLE_WOLFSSL

void send();
void sendOwnSocket();
void sendViaTLS();