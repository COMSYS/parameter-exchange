FROM ubuntu:18.04

LABEL maintainer="Erik Buchholz <erik.buchholz@rwth-aachen.de>"

# Install packages
RUN apt-get -yqq update
RUN apt-get -yqq install python3-pip python3-dev
RUN apt-get -yqq install wget git g++ cmake vim tmux htop
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
COPY wolfssl /lib/wolfssl
WORKDIR /lib/wolfssl/
RUN ./autogen.sh
RUN ./configure --enable-opensslextra --enable-debug CFLAGS=-DKEEP_PEER_CERT
RUN make -j
RUN make install
RUN ldconfig

# Add boost to path
ENV PATH="/master/libraries/libOTe/cryptoTools/thirdparty/linux/boost/boost:${PATH}"

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
