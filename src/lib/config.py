#!/usr/bin/env python3
"""This module contains central configurations.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import math
import multiprocessing
import os

# GENERAL----------------------------------------------------------------------
DEBUG = True
PSI_MODE = False
EVAL = True
PARALLEL = True
MAX_PROCS = int(math.ceil(multiprocessing.cpu_count() / 2))
# Celery can only process as many tasks as CPUs.
# -----------------------------------------------------------------------------
# DIRECTORY STRUCTURE----------------------------------------------------------
# os.path.dirname moves on directory up
_cur_dir = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))
WORKING_DIR = os.path.abspath(_cur_dir) + '/'
DATA_DIR = WORKING_DIR + 'data/'
EVAL_DIR = WORKING_DIR + 'eval/'
LOG_DIR = DATA_DIR + 'logs/'
EVAL_RESULT_DIR = WORKING_DIR + 'results_eval/'
# -----------------------------------------------------------------------------
# TLS--------------------------------------------------------------------------
TLS_CERT_DIR = DATA_DIR + "certs/"
TLS_ROOT_CA = TLS_CERT_DIR + "rootCA.crt"
# -----------------------------------------------------------------------------
# EVAL SETTINGS----------------------------------------------------------------
if EVAL:
    DATA_DIR += 'eval/'
    os.makedirs(DATA_DIR, exist_ok=True)
TEMP_DIR = DATA_DIR + 'tmp/'
os.makedirs(TEMP_DIR, exist_ok=True)
RAM_INTERVAL = 0.5  # s
# -----------------------------------------------------------------------------
# LOGGING----------------------------------------------------------------------
LOGLEVEL = logging.DEBUG
# -----------------------------------------------------------------------------
# KEY SERVER SETTINGS----------------------------------------------------------
KEYSERVER_HOSTNAME = "localhost"
KEY_API_PORT = 5000
KEY_TLS_CERT = TLS_CERT_DIR + "keyserver.crt"
KEY_TLS_KEY = TLS_CERT_DIR + "keyserver.key"
RANDOMIZE_PORTS = True
KEY_LOGNAME = "key_server"
KEY_LOGFILE = "key_server.log"
KEY_HASHKEY_PATH = "hash_key.pyc"
KEY_ENCKEY_PATH = "encryption_keys.pyc"
KEY_REDIS_PORT = 6379
KEY_CELERY_BROKER_URL = f'redis://localhost:{KEY_REDIS_PORT}/0'
KEYSERVER_DB = "keyserver.db"
# -----------------------------------------------------------------------------
# STORAGE SERVER SETTINGS------------------------------------------------------
STORAGESERVER_HOSTNAME = "localhost"
STORAGE_API_PORT = 5001
STORAGE_TLS_CERT = TLS_CERT_DIR + "storageserver.crt"
STORAGE_TLS_KEY = TLS_CERT_DIR + "storageserver.key"
STORAGE_LOGFILE = "storage_server.log"
STORAGE_DB = "storage.db"
STORAGE_REDIS_PORT = 6380
BLOOM_FILE = 'storage.bloom'
if EVAL:  # pragma no cover
    BLOOM_CAPACITY = 10 ** 8
    BLOOM_ERROR_RATE = 10 ** -20
else:  # pragma no cover
    BLOOM_CAPACITY = 10 ** 5
    BLOOM_ERROR_RATE = 10 ** -8
STORAGE_CELERY_BROKER_URL = f'redis://localhost:{STORAGE_REDIS_PORT}/0'
# -----------------------------------------------------------------------------
# OT Parameters ---------------------------------------------------------------
OT_SETSIZE = 2**20
# equals PyOTSender/PyOTReceiver.numChosenMsgs
OT_THREADS = 1
OT_STATSECPARAM = 40
OT_MAL_SECURE = False
OT_INPUT_BIT_COUNT = 128
OT_PORT = 1213
OT_HOST = "127.0.0.1"
OT_TLS = False
OT_MAX_NUM = 10  # Maximal number of simultaneous OTs
# -----------------------------------------------------------------------------
# PSI Parameters ---------------------------------------------------------------
PSI_SCHEME = "KKRT16"
PSI_SETSIZE = 2**20
PSI_THREADS = 1
PSI_STATSECPARAM = 40
PSI_MAL_SECURE = False
PSI_INPUT_BIT_COUNT = 128
PSI_PORT = 1214
PSI_HOST = "127.0.0.1"
PSI_TLS = False
# -----------------------------------------------------------------------------
# KEY SETTINGS-----------------------------------------------------------------
HASHKEY_LEN = 128
ENCKEY_LEN = 128
# -----------------------------------------------------------------------------
# HASH SETTINGS----------------------------------------------------------------
PSI_INDEX_LEN = 127  # Bit (127 so that we can use the remainder for dummies)
PSI_DUMMY_START_SERVER = 2 ** 127
PSI_DUMMY_START_CLIENT = 2 ** 127 + PSI_SETSIZE
OT_INDEX_LEN = 20  # in Bit
# -----------------------------------------------------------------------------
# DISCRETIZATION SETTINGS------------------------------------------------------
RECORD_ID_LENGTH = 10
# RECORD_ROUNDING = 3
RECORD_LENGTH = 100
ROUNDING_VEC = [3 for _ in range(RECORD_ID_LENGTH)]
# -----------------------------------------------------------------------------
