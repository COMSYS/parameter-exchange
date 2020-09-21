# Privacy-Preserving Production Process Parameter Exchange

## About

This repository contains our fully-tested prototype of BPE & PPE, our implementations that offer Privacy-Preserving Production Process Parameter Exchanges (in industrial settings).

> Nowadays, collaborations between industrial companies always go hand in hand with trust issues, i.e., exchanging valuable production data entails the risk of improper use of potentially sensitive information. Therefore, companies hesitate to offer their production data, e.g., process parameters that would allow other companies to establish new production lines faster, against a quid pro quo. Nevertheless, the expected benefits of industrial collaboration, data exchanges, and the utilization of external knowledge are significant.
>
> In this paper, we propose BPE, our platform allowing industrial companies to exchange production process parameters privacy-preservingly using Bloom filters and oblivious transfers. We demonstrate the applicability of our platform based on two distinct real-world use cases: injection molding and machine tools. We show that BPE is both scalable and deployable for different needs. Thereby, we reward data-providing companies with payments while preserving their valuable data and reducing the risks of data leakage.

## Publication

* Jan Pennekamp, Erik Buchholz, Yannik Lockner, Markus Dahlmanns, Tiandong Xi, Marcel Fey, Christian Brecher, Christian Hopmann, and Klaus Wehrle: *Privacy-Preserving Production Process Parameter Exchange*. In Proceedings of the 36th Annual Computer Security Applications Conference (ACSAC '20), ACM, 2020.

If you use any portion of our work, please cite our publication.

```
@inproceedings{pennekamp2020parameterexchange,
    author = {Pennekamp, Jan and Buchholz, Erik and Lockner, Yannik and Dahlmanns, Markus and Xi, Tiandong and Fey, Marcel and Brecher, Christian and Hopmann, Christian and Wehrle, Klaus},
    title = {{Privacy-Preserving Production Process Parameter Exchange}},
    booktitle = {Proceedings of the 36th Annual Computer Security Applications Conference (ACSAC '20)},
    year = {2020},
    month = {12},
    publisher = {ACM},
}
```

## License

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <http://www.gnu.org/licenses/>.

If you are planning to integrate parts of our work into a commercial product and do not want to disclose your source code, please contact us for other licensing options via email at pennekamp (at) comsys (dot) rwth-aachen (dot) de

## Acknowledgments

This work is funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Germany's Excellence Strategy – EXC-2023 Internet of Production – 390621612.

---

# Artifacts

## Introduction

We provide three ways to set up the environment that is required to run the code and evaluation scripts.

1. **Direct setup** on a server running Linux or macOS
2. **Partial Docker Container:** A Docker container that uses the libraries as submodules (allows for faster building and does not require to compile the libraries every time the container is created)
3. **Full Docker Container:** A Docker container realizing the entire setup, including the compilation of all libraries

The setup has been tested on macOS Catalina, Ubuntu 18.04, and Docker.
We do not guarantee that this setup works for any other operating system.

After the setup, we describe how to execute the platform and the evaluation scripts.

Further information about the evaluation can be found in `Eval.md` and information about the datasets in `Datasets.md`.

## 1. Direct Setup

1. Checkout Repository with `git clone --recursive git@github.com:COMSYS/parameter-exchange.git` to also clone the
submodules/libraries (This project requires [libOTe](https://github.com/osu-crypto/libOTe), [libPSI](https://github.com/osu-crypto/libPSI), [cryptoTools](https://github.com/ladnir/cryptoTools) and
[Wolfssl](https://www.wolfssl.com/))
2. cd into `docker/`
3. Run `sudo ./server-pre-setup.sh` (This file contains the commands that are otherwise executed by the Dockerfile)

    **Note:** You can run this script **without sudo**. However, then wolfssl
     is locally installed into your `$HOME` and you have to make sure that
     all necessary packages are installed:

     `python3-pip python3-dev wget git g++ cmake vim tmux htop redis libssl-dev dh-autoreconf colordiff`

4. Execute `./setup.sh`.

## 2. Partial Docker Container

The setup is called *partial* Docker container because the script `setup.sh` has to be executed manually within the container.
This procedure has the advantage that the libraries only need to be compiled once and the binaries can be reused by multiple containers.
The compilation takes a while such that this approach should be preferred if the docker container needs to be rebuilt frequently, for instance, due to the usage of certain IDEs.

1. Install Docker on your host
2. Checkout Repository with `git clone --recursive` to also clone the
submodules/libraries (This project requires [libOTe](https://github.com/osu-crypto/libOTe), [libPSI](https://github.com/osu-crypto/libPSI), [cryptoTools](https://github.com/ladnir/cryptoTools) and
[Wolfssl](https://www.wolfssl.com/))
3. cd into `docker/`
4. Execute `create_container.sh` (This will also create the required image
via Dockerfile) [You can change the container and image name in this file, default is *(erikb/)ma*]

    **Note:** Building the container might fail at the pip install command.
    This issue is caused by problems with the internet connection. Just try to create
    the container again, the build process will resume at the previous point.

5. You can start the container via `docker start ma` and attach via
`docker attach ma`. If you want to open a new bash, use: `docker exec -it ma bash`.

6. Execute `cd /master/docker` within the container.
7. Execute `./setup.sh` within the container.

   	 **Note:** The setup just needs to be executed once after cloning the repo
   	 (or after making any update to the libOTe, libPSI, or wolfssl libraries).
   	 It takes **very long** and does not need to be executed in case only the
   	 docker container has to be rebuilt due to whatever reason. For instance,
   	 you can once build the docker container manually and perform the setup, and
   	 then create another docker container (with another name) for your IDE
   	 without the need to execute the setup again. This approach is particularly
   	 useful if your IDE builds the container itself.

   	 **Note:** You can adapt the variable `NUM_THREADS` in `setup.sh` to
   	 accelerate the setup procedure. (Too high values might yield an internal compiler error, see below under *Known Issues*.)

8. Now, you should be able to use the container to execute the scripts.

## 3. Full Docker Container

This Docker container includes the steps that are performed by `setup.sh` in the previous setup, such that no manual steps have to be performed.
However, the creation of this container takes a lot longer because the compilation of libOTe and libPSI introduces significant overhead.
Therefore, this container should only be used if it is not frequently rebuilt.

1. Install Docker on your host
2. Checkout Repository with `git clone --recursive` to also clone the
submodules/libraries (This project requires [libOTe](https://github.com/osu-crypto/libOTe), [libPSI](https://github.com/osu-crypto/libPSI), [cryptoTools](https://github.com/ladnir/cryptoTools) and
[Wolfssl](https://www.wolfssl.com/))
3. cd into `dockerFull/`
4. Execute `create_container.sh` [You can change the container and image name in this file, default is *(erikb/)pppe_full* for *Privacy-Preserving Parameter Exchange*]
5. You can start the container via `docker start pppe_full` and attach via
`docker attach pppe_full`. If you want to open a new bash, use: `docker exec -it pppe_full bash`.
6. The Cython code has still to be compiled because the directory is only accessible after the first start of the container. See *Modifications* below for a manual on how to do this.

## Library Versions:

- LibOTe: Commit `0d9a2afba26cd5a0359268292bc7902448c3ef6d`

        git submodule add https://github.com/osu-crypto/libOTe.git libraries/libOTe
        cd libraries/libOTe
        git checkout 0d9a2afba26cd5a0359268292bc7902448c3ef6d

- LibPSI: Commit `6082b1310ef0ee9004d10bea24f96e4c615f6eeb`

        git submodule add https://github.com/osu-crypto/libPSI.git libraries/libPSI
        cd libraries/libPSI
        git checkout 6082b1310ef0ee9004d10bea24f96e4c615f6eeb

- CryptoTools: Commit `572763dc3feda7e73ea04e88e3f9ae63e6c10f05`

        cd libraries/libOTe/
        git submodule init cryptoTools
        cd cryptoTools
        git submodule update
        git checkout 572763dc3feda7e73ea04e88e3f9ae63e6c10f05 # for manual setup only

- Wolfssl Commit `d1397656ef4be39829fafd90bbc07e7aa447d600`

        git submodule add https://github.com/wolfSSL/wolfssl.git docker/wolfssl
        cd docker/wolfssl
        git checkout d1397656ef4be39829fafd90bbc07e7aa447d600

## System Requirements

We do not require any specific hardware or software apart from the needs introduced by our utilized libraries (i.e., a current Linux or MacOS system).
In general, our design is detached from the specific hardware and can be configured accordingly, for example, to require less memory (e.g., by reducing the number of OTs).
For our measurements, we noticed a maximum memory consumption of 42 GiB, however, most evaluations required significantly less.
In a real-world deployment, the different entities would run on different devices and, thus, require less memory on a single machine.

## Library Adaptions

*All those changes are done by the setup script, so do not worry about it
, in case you build everything as described above.*

To be able to use the libraries with Cython, we have to make some changes. Mainly, we have to create position-independent code by using the gcc option `-fPIC` and we have to add the correct Wolfssl paths to the linker.

0. **_WOLFSSL_**
Wolfssl needs to be configured before compilation with some flags.
If you do not have root rights on the machine, add `--prefix=$HOME` to `./configure`.
Then, you need to modify the wolfssl path for libOTe and libPSI. See below.

		cd *YOUR_WOLFSSL_DIRECTORY*
		./autogen.sh
		./configure --enable-opensslextra --enable-debug CFLAGS=-DKEEP_PEER_CERT
		make -j
		make install



1. **_MIRACL_**
We need to add `-fPIC` to each line in
`libraries/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/linux64`.
Move to the directory and use the following command:

        # Add - fPIC to generate position-independent code
        sed -i -- 's|g++|g++ -fPIC|g' linux64

2. **_LibOTe_**
The libOTe and wolfssl libraries are usable as is. However, there is a bug in the `cryptoTools` submodule used by libOTe. Therefore, we need to checkout a newer commit before compilation:

		cd "libraries/libOTe/cryptoTools"
		git checkout -f
		git pull origin master
		git checkout -f 572763dc3feda7e73ea04e88e3f9ae63e6c10f05

3. **_libPSI_**
We need to add `-fPIC` to the libPSI compilation as well.

		cd libraries/libPSI
		# Add - fPIC to generate position-independent code
		echo 'set(CMAKE_CXX_FLAGS "-fPIC ${CMAKE_CXX_FLAGS}")' >> libPSI/CMakeLists.txt

4. **_Wolfssl -  Optional_**
In case you installed wolfssl to another location than `/usr/local`, you need to adapt the include and linker paths accordingly. In case you installed WOLFSSL into `$HOME` by using `./configure --prefix=$HOME` you have to do the following adaptions:
For macOS, you have to replace `libwolfssl.so` by `libwolfssl.dylib` in the following.

	1. libOTe

			cd libraries/libOTe
			# WOLFSSL has been installed into your home directory. Hence, we have to adapt the paths.
	    	sed -i -- "s|WolfSSL_DIR \"/usr/local/\"|WolfSSL_DIR \"$HOME/\"|g" cryptoTools/cryptoTools/CMakeLists.txt
	    	sed -i -- 's|find_library(WOLFSSL_LIB NAMES wolfssl  HINTS "${WolfSSL_DIR}")|set\(WOLFSSL_LIB "\${WolfSSL_DIR}lib/libwolfssl.so"\)|g' cryptoTools/cryptoTools/CMakeLists.txt
	    	LD_LIBRARY_PATH="${HOME}/lib:${LD_LIBRARY_PATH}"
	    	export LD_LIBRARY_PATH

	2. libPSI

			# Wolfssl installed into $HOME
			cd libraries/libPSI
			sed -i -- "s|WolfSSL_DIR \"/usr/local/\"|WolfSSL_DIR \"$HOME/\"|g" CMakeLists.txt
			sed -i -- "s|find_library(WOLFSSL_LIB NAMES wolfssl  HINTS \"\${WolfSSL_DIR}\")|set\(WOLFSSL_LIB \"\${WolfSSL_DIR}lib/${WOLFSSL_FILENAME}\"\)|g" libPSI/CMakeLists.txt

## Known Issues

### Autoreconf: command not found

This error indicates that the respective tool is not installed.
Please make sure to install it and run the setup again.

	brew install automake # MacOS
	apt install autoconf # Linux

### Linking Error for libOTe Code

If you get a linker error, you might need to rebuild miracl.

    cd libraries/libOTe/cryptoTools/thirdparty/linux
    rm -rf miracl
    bash miracl.get
    cd /master/libraries/libOTe/cryptoTools/thirdparty/linux/miracl/miracl/source/
    # Add - fPIC to generate position-independent code
    sed -i -- 's|g++|g++ -fPIC|g' linux64
    bash linux64

### Internal Compiler error building libraries

This error occurs sometimes if make uses too many threads. Set `$NUM_THREADS` (line 6) in `libraries/build_libraries.sh` to a small value, e.g., 3.

## Testing

After a successful setup, the platform can be executed.

### Unittests

		cd src/
		python3 -m unittest

### Test Cython Implementation

These tests are automatically executed at the end of the setup.

		cd cython
		cmake .
		make -j
		./bin/interface_test -d yes

## Modifications

**src/Python:**
Modifications of the Python code in `src/` do not require re-compilation. Just check that the unit tests are still running successfully.

**Cython:**
After any modification of the libraries or the Cython code, the Cython shared library has to be re-compiled.

	cd cython
	cmake .
	make -j

**Libraries:**
After modification of the libraries (e.g., updates), they have to be re-compiled, as well as the Cython library (see above).

	cd libraries/
	./build_libraries.sh
	./test_all_libs.sh
	cd ../cython
	cmake .
	make -j

## Configuration

All global configurations are stored in `src/lib/config.py`.

## Directory Structure

- TLS certificates and DH parameters are stored in `data/certs`.
- Logs are contained in `data/logs`


## Usage

All scripts have to be started from within `src/`.

### Create Users

1. Create users:

	We provide a separate script for the registration of both clients and data providers.
	See the scripts' help for usage information:

		python3 owner_db_cli.py --help
		python3 client_db_cli.py --help

	**Example:**

		python3 owner_db_cli.py --add USERNAME PASSWORD
		python3 client_db_cli.py --add USERNAME PASSWORD

	**Both servers have to restarted after modification of the user databases!**

### Starting Server

#### Start via Script

The first variant to start the server instances is using the script `allStart.sh`. This script creates a tmux session *Server* that contains Redis and both key and storage server along with the corresponding celery instances.

#### Start  Manually

1. Start Redis for both key and storage server:

		redis-server --port 6379
		redis-server --port 6380

2. Start the key server's celery workers:

		celery worker -A key_server.celery.celery_app --loglevel=info

3. Start the key server:

		./startKeyServer.sh

4. Start the storage server's celery workers:

		celery worker -A storage_server.celery.celery_app --loglevel=info

5. Start the storage server:

		./startStorageServer.sh

The web interface of the key server is reachable at `https://localhost:5000/` and the one of the storage server at `https://localhost:5001/`.
Additional information on the web interface is listed in `WebInterface.md`.
However, it is mostly designed to give an overview and to ease testing.

### Data Provider Application
*Servers must be running*

**Usage:**

			python3 data_provider.py --help

**Examples:**

1. Upload single record:

			python3 data_provider.py USERNAME PASSWORD --add '[1,2,3,4,5]'

2. Upload records from file (each line must contain a single records, refer to `data/wzl_data.txt` for an example).

			python3 data_provider.py USERNAME PASSWORD -f FILEPATH


### Client Application
*Servers must be running*

**Usage:**

			python3 client.py --help

**Examples:**

1. Request matches for target Vector [1,2,3,4,5]:

		python3 client.py USERNAME PASSWORD -r '[1,2,3,4,5]'

2. Use PPE design variant for retrieval:

		python3 client.py USERNAME PASSWORD -r '[1,2,3,4,5]' --psi



## Evaluation

An overview of all performed evaluations is provided in `Eval.md`.
The datasets are explained in `Datasets.md`.

**All evaluation scripts need to be started from `src/` with the command `python3 -m eval.NAME OPTIONS`.
The server instances DO NOT need to be running, if needed, they are started automatically.**

All eval scripts provide a user manual with the command line option `--help`.

		python3 -m eval.script --help

All evals are written to `eval/`. Accordingly, all filenames are relative to this base directory.

### Bloom Filter Eval

		python3 -m eval.bloom_eval OPTIONS -o FILENAME -r REPETITIONS

**Options:**

- `--capacity (-c) CONSTANT or MIN MAX STEP`: Capacities to consider. Either one value (constant) or three values (min, max, stepsize).
- `--insert (-i) CONSTANT or MIN MAX STEP`: Number of elements to insert. Either one value (constant) or three values (min, max, stepsize).
- `--query (-q) CONSTANT or MIN MAX STEP`: Number of elements to query. Either one value (constant) or three values (min, max, stepsize).
- `--error (-e) CONSTANT or MIN MAX STEP`: FP rates. Either one value (constant) or three values (min, max, stepsize).
- `--fill`: Fill each Bloom filter to max capacity, i.e., ignore insert values.

**Examples:**

		ID 1: python3 -m eval.bloom_eval -q 100000000 --error 0.00000000000000000001 -c 0 1000000000 100000000 -o butthead_bloom_cap -r 10 --fill

		ID 2: python3 -m eval.bloom_eval -q 100000000 -c 100000000 -o butthead_bloom_fp -r 10 --fill

### OT Eval

		python3 -m eval.ot_eval OPTIONS -o FILENAME -r REPETITIONS

**Options:**

- `--tls (-t) {0,1}`: Activate (1) or Deactivate (0) TLS.
- `--setsize (-s) CONSTANT or MIN MAX STEP`: OT set size. Either one value (constant) or three values (min, max, stepsize).
- `--numOTs (-n) CONSTANT or MIN MAX STEP`: Number of OT extensions to perform. Either one value (constant) or three values (min, max, stepsize).
- `--malicious (-m)`: Use OOS16 instead of KKRT16.
- `--latency (-l) CONSTANT or MIN MAX STEP`: Latency to add. Only on Linux. Either one value (constant) or three values (min, max, stepsize).
- `--bandwidth (-b)`: Limit bandwidth to 6Mbit/s, 50Mbit/s, and 100Mbit/s? Only on Linux.
- `--baseline`: Transmit 76Bit instead of 128Bit.
- `--statsecparam CONSTANT or MIN MAX STEP`: Statistical Security Parameter. Either one value (constant) or three values (min, max, stepsize).

**Examples:**

		ID 1: python3 -m eval.ot_eval --tls 0 --numOTs 10 -o butthead_setsize -r 10

		ID 5: python3 -m eval.ot_eval --tls 0 --numOTs 20 100 20 --setsize 1048576 --latency 0 300 50 -o butthead_latency -r 10

### PSI Eval

		python3 -m eval.psi_eval OPTIONS -o FILENAME -r REPETITIONS

**Options:**

- `--tls (-t) {0,1}`: Activate (1) or Deactivate (0) TLS.
- `--setsize (-s) CONSTANT or MIN MAX STEP`: PSI set size. Either one value (constant) or three values (min, max, stepsize).
- `--malicious (-m)`: Use RR16 instead of KKRT16.
- `--rr17`: Use RR17 instead of KKRT16. Broken for set sizes > 1000.
- `--latency (-l) CONSTANT or MIN MAX STEP`: Latency to add. Only on Linux. Either one value (constant) or three values (min, max, stepsize).
- `--bandwidth (-b)`: Limit bandwidth to 6Mbit/s, 50Mbit/s, and 100Mbit/s? Only on Linux.
- `--statsecparam CONSTANT or MIN MAX STEP`: Statistical Security Parameter. Either one value (constant) or three values (min, max, stepsize).

**Examples:**

	ID 1: python3 -m eval.psi_eval --tls 0 -o butthead_psi_setsize -r 10

	ID 5: python3 -m eval.psi_eval --tls 0 --setsize 2000000 10000000 2000000 --latency 0 300 50 -o butthead_psi_latency -r 10

### Metric Eval

		python3 -m eval.metric_eval OPTIONS -o FILENAME -r REPETITIONS

**Options:**

- `--id1` - `--id12`: Perform Eval with corresponding ID.

**Examples:**

		ID X: python3 -m eval.metric_eval -idX -o metric_idX -r 10

### Client Eval

		python3 -m eval.client OPTIONS -o FILENAME -r REPETITIONS

**Options:**

- `--metric (-m) METRIC`: Name of similarity metric to use.
- `--num (-n) NUMBER or MIN MAX STEP`: Number of matches to produce. Either one value (number) or three values (min, max, stepsize).
- `--psi (-p)`: Also evaluate PPE design variant.
- `--random`: Use random data.
- `--ikv`: Use IKV data.
- `--wzl1`: Use WZL Data and metric MT-Material.
- `--wzl2`: Use WZL Data and metric MT-Diameter.

**Examples:**

	ID 1: python3 -m eval.client --random -n 0 1000 100 -m relOffset-0.3 --psi -o butthead_psi_vs_bloom -r 10
	ID 2: python3 -m eval.client --random -n 0 1000 100 -m relOffset-0.5 -o butthead_client_bloom -r 10
	ID 3: python3 -m eval.client --ikv -m relOffset-2 --psi -o butthead_client_ikv1 -r 10
	ID 4: python3 -m eval.client --ikv -m relOffset-2.5 -o butthead_client_ikv2 -r 10
	ID 5: python3 -m eval.client --ikv -m relOffset-3 -o butthead_client_ikv3 -r 10
	ID 6: python3 -m eval.client -m wzl1 --wzl1 --psi -o butthead_client_wzl1 -r 10
	ID 7: python3 -m eval.client -m wzl2 --wzl2 --psi -o butthead_client_wzl2 -r 10

### Data Provider Eval

		python3 -m eval.data_provider OPTIONS -o FILENAME -r REPETITIONS

**Options:**

- `--uploads`: Eval ID 1.
- `--rec_len`: Eval ID 2.
- `--ikv1`: Eval ID 3a.
- `--ikv2`: Eval ID 3b.
- `--wzl`: Eval ID 4.

**Examples:**

		ID 1: python3 -m eval.data_provider --uploads -o butthead_provider_uploads -r 10
		ID 2: python3 -m eval.data_provider --rec_len -o butthead_provider_record_length -r 10
		ID 3a: python3 -m eval.data_provider --ikv1 -o butthead_provider_ikv -r 10
		ID 3b: python3 -m eval.data_provider --ikv2 -o butthead_provider_ikv2 -r 10
		ID 4: python3 -m eval.data_provider --wzl -o butthead_provider_wzl -r 10