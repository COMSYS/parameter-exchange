#!/usr/bin/env bash

#Compile
make -j

#Execute both (sender in background)
./nwSend.o & ./nwRecv.o
