FROM ubuntu:18.04

LABEL maintainer="Erik Buchholz <erik.buchholz@rwth-aachen.de>"

# Install packages
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev bash
RUN apt-get -yqq install wget git g++ cmake vim tmux htop sed
RUN apt-get -yqq install redis libssl-dev dh-autoreconf colordiff

# Pip Installs
COPY requirements.txt /tmp/
RUN pip3 install --requirement /tmp/requirements.txt

# Bash & Vim Colors
COPY bashrc /root/.bashrc
COPY vimrc /root/.vimrc

# Timezone
RUN echo "Europe/Berlin" > /etc/timezone
RUN ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime
RUN apt-get install -y tzdata
RUN dpkg-reconfigure -f noninteractive tzdata

# Wolfssl
RUN mkdir -p /lib/
RUN git clone --recursive https://github.com/wolfSSL/wolfssl.git  /lib/wolfssl
WORKDIR /lib/wolfssl/
RUN ./autogen.sh
RUN ./configure --enable-opensslextra --enable-debug CFLAGS=-DKEEP_PEER_CERT
RUN make -j
RUN make install
RUN ldconfig

# Add boost to path
ENV PATH="/master/libraries/libOTe/cryptoTools/thirdparty/linux/boost/boost:${PATH}"

# Clone repos
RUN git clone --recursive https://github.com/osu-crypto/libOTe.git /lib/libOTe
WORKDIR /lib/libOTe
RUN git checkout 0d9a2afb
RUN git clone --recursive https://github.com/osu-crypto/libPSI.git /lib/libPSI
WORKDIR /lib/libPSI
RUN git checkout 6082b131

# Install pre-requesites BOOST and MIRCAL
WORKDIR /lib/libOTe/cryptoTools/thirdparty/linux
RUN bash all.get
WORKDIR /lib/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/
RUN sed -i -- 's|g++|g++ -fPIC|g' linux64
RUN bash linux64

# Install libraries
WORKDIR /lib
COPY build_libraries_within_docker.sh /lib/build_libraries.sh
RUN ./build_libraries.sh

# Expose ports
EXPOSE 80/tcp
EXPOSE 443/tcp
EXPOSE 5000/tcp
EXPOSE 5001/tcp

# Mount Point for MA Code
VOLUME ["/master"]

# Start directory
WORKDIR /master/src

ENTRYPOINT ["bash"]
