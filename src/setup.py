#!/usr/bin/env python3
"""Setup requirements.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
from setuptools import setup, find_packages
from lib import config

with open(config.WORKING_DIR + "README.md", "r") as f:
    readme = f.read()

with open(config.WORKING_DIR + "docker/requirements.txt", "r") as f:
    requirements = f.read()

setup(
    name="Privacy-Preserving Exchange of Process Parameters",
    version="1.0.0",
    maintainer="Erik Buchholz",
    maintainer_email="erik.buchholz@rwth-aachen.de",
    description="Implementation of the Erik's master thesis.",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requirements,
    extras_require={"test": ["coverage"]},
    test_suite="test"
)
