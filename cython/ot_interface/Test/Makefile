VERSION = 1.0
CC      = /usr/bin/g++
CFLAGS  = -w -Wall -g -D_REENTRANT -DVERSION=\"$(VERSION)\"
HOST=$(shell hostname)
ROOT_DIR=../../../
INCLUDES := -I../ -I$(ROOT_DIR)libraries/libOTe
INCLUDES += -I$(ROOT_DIR)libraries/libOTe/cryptoTools
INCLUDES += -I$(ROOT_DIR)libraries/libOTe/cryptoTools/thirdparty/linux/boost
LDFLAGS := -pthread -L$(ROOT_DIR)libraries/libOTe/lib/
LDFLAGS += -L$(ROOT_DIR)libraries/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/
LDFLAGS += -llibOTe -lcryptoTools -lmiracl -lwolfssl

NC=\033[0m
YEL=\033[0;33m
RED=\033[0;31m
BLU=\033[0;34m

.PHONY: all clean

all: pre-build mainSend.o mainRecv.o nwSend.o nwRecv.o

pre-build:
	@echo "\e[0;31mDeprecated! Use cmake-generated Makefile in parent directory instead!\e[0m"
	@echo "Running on host: \e[1m$(HOST)\e[0m"
	@echo "Home Directory: \e[1m$(HOME)\e[0m"
# Adds include directories of libwolfssl because it is installed in home instead of globally
ifeq ($(HOST), passion)
INCLUDES += -I$(HOME)/include
LDFLAGS += -L$(HOME)/lib
endif

mainSend.o: mainSend.cpp ../OTSender.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o mainSend.o mainSend.cpp ../OTSender.cpp $(LDFLAGS)
mainRecv.o: mainRecv.cpp ../OTReceiver.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o mainRecv.o mainRecv.cpp ../OTReceiver.cpp $(LDFLAGS)
nwSend.o: NWSend.cpp ../NWSender.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o nwSend.o NWSend.cpp ../NWSender.cpp $(LDFLAGS)
nwRecv.o: NWRecv.cpp ../NWReceiver.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o nwRecv.o NWRecv.cpp ../NWReceiver.cpp $(LDFLAGS)
clean: 
	rm -f *.o
cleanNW:
	rm -f nw*.o
