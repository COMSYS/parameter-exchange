#!/usr/bin/env python3
"""
Copyright (c) 2020.
Author: Chris Dax
E-mail: dax@comsys.rwth-aachen.de
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import os
import sys
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

# os.path.dirname moves on directory up
cur_dir = os.path.dirname(os.path.abspath(__file__))
cython_dir = os.path.dirname(cur_dir)
repo_base_dir = os.path.dirname(cython_dir)

lib_dirs = [
    f"{cython_dir}/lib",
    f"{repo_base_dir}/libraries/libPSI/lib",
    f"{repo_base_dir}/libraries/libOTe/lib",
    f"{repo_base_dir}/libraries/libOTe/cryptoTools/thirdparty/linux"
    "/miracl/miracl/source/"
]

inc_dirs = [
    cur_dir,
    f"{cython_dir}/psi_interface",
    f"{repo_base_dir}/libraries/libOTe/cryptoTools",
    f"{repo_base_dir}/libraries/libOTe/cryptoTools/thirdparty/linux/boost",
    f"{repo_base_dir}/libraries/libPSI",
    f"{repo_base_dir}/libraries/libOTe"
]

home = os.path.expanduser("~")
wolfssl_filename = "libwolfssl.so"

if sys.platform == "darwin":
    # MAC OS
    # os.environ["CC"] = "g++-9"
    wolfssl_filename = "libwolfssl.dylib"
    inc_dirs.append("/usr/local/include/")

wolfssl_path = home + "/lib/" + wolfssl_filename

if os.path.exists(wolfssl_path):
    # WOLFSSL was installed into home instead of /usr/local/
    # Done on passion for example
    lib_dirs.append(home + "/lib/")
    inc_dirs.append(home + "/include/")

RunMain_extension = Extension(
    name="cPSIInterface",
    sources=[f"{cur_dir}/cPSIInterface.pyx"],
    libraries=[
        "PSIInterface", "libPSI", "libOTe", "cryptoTools", "miracl", "wolfssl"
    ],
    library_dirs=lib_dirs,
    include_dirs=inc_dirs,
    language="c++",
    extra_compile_args=["-w", "-fPIC", "-pthread", "-std=c++14"]
    # extra_link_args = []
)
setup(
    name="cPSIInterface",
    ext_modules=cythonize([RunMain_extension])
)
