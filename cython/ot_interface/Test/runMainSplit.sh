#Compile
make -j

#Execute both (sender in background)
./mainSend.o & ./mainRecv.o
