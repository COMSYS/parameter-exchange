VERSION = 1.0
CC      = /usr/bin/g++
CFLAGS  = -w -Wall -g -D_REENTRANT -DVERSION=\"$(VERSION)\" -Xlinker -v
HOST=$(shell hostname)
ROOT_DIR=../../../
INCLUDES := -I../ -I$(ROOT_DIR)libraries/libOTe
INCLUDES += -I$(ROOT_DIR)libraries/libPSI -I$(ROOT_DIR)libraries/libOTe/cryptoTools
INCLUDES += -I$(ROOT_DIR)libraries/libOTe/cryptoTools/thirdparty/linux/boost
LDFLAGS := -L$(ROOT_DIR)libraries/libOTe/lib/
LDFLAGS += -L$(ROOT_DIR)libraries/libPSI/lib/
LDFLAGS += -L$(ROOT_DIR)libraries/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/
LDFLAGS += -llibPSI -llibOTe -lcryptoTools -lmiracl -lwolfssl -pthread

NC=\033[0m
YEL=\033[0;33m
RED=\033[0;31m
BLU=\033[0;34m
BLA=\033[0;30m

.PHONY: all clean

all: pre-build mainSend.o mainRecv.o main.out

pre-build:
	@echo "\e[0;31mDeprecated! Use cmake-generated Makefile in parent directory instead!\e[0m"
	@echo "Running on host: $(BLU)$(HOST)$(NC)"
	@echo "Home Directory: $(BLU)$(HOME)$(NC)"
# Adds include directories of libwolfssl because it is installed in home instead of globally
ifeq ($(HOST), passion)
INCLUDES += -I$(HOME)/include
LDFLAGS += -L$(HOME)/lib
endif

mainSend.o: mainSend.cpp ../PSISender.cpp ../util.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o mainSend.o \
		mainSend.cpp ../PSISender.cpp ../util.cpp $(LDFLAGS)

mainRecv.o: mainRecv.cpp ../PSIReceiver.cpp ../util.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o mainRecv.o \
		mainRecv.cpp ../PSIReceiver.cpp ../util.cpp $(LDFLAGS)
	
main.out: main.cpp ../util.cpp ../PSIReceiver.cpp ../PSISender.cpp
	@echo "$(YEL)Building $@ $(NC)"
	$(CC) $(CFLAGS) $(INCLUDES) -o main.out \
		main.cpp ../util.cpp ../PSIReceiver.cpp ../PSISender.cpp $(LDFLAGS)

clean: 
	rm -f *.o *.out
