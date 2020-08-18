#Compile
make -j mainRecv.o mainSend.o

#Execute both (sender in background)
./mainSend.o & ./mainRecv.o
