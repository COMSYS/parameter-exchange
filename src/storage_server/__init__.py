#!/usr/bin/env python3
"""Application factory for storageserver app.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import os

from celery import Celery
from flask import Flask

from lib import config, database
from lib.logging import configure_root_loger

# Configure logging
# configure_root_loger(config.LOGLEVEL)
celery_app = Celery(__name__, broker=config.STORAGE_CELERY_BROKER_URL)


def create_app(test_config=None, logging_level=config.LOGLEVEL,
               data_dir=config.DATA_DIR) -> Flask:
    """Factory function for flask app. Return a configured flask app object."""

    app = Flask(__name__, instance_relative_config=True)
    redis_port = config.STORAGE_REDIS_PORT
    if test_config is not None and 'DATA_DIR' in test_config:
        data_dir = test_config['DATA_DIR']
    log_dir = data_dir + 'logs/'
    app.config.from_mapping(
        SECRET_KEY='dev',  # TODO: Exchange
        REDIS_PORT=redis_port,
        CELERY_BROKER_URL=config.STORAGE_CELERY_BROKER_URL,
        CELERY_RESULT_BACKEND=config.STORAGE_CELERY_BROKER_URL,
        DATA_DIR=data_dir,
        PSI_HOST=config.PSI_HOST,
        PSI_TLS=config.PSI_TLS,
        RANDOMIZE_PORTS=config.RANDOMIZE_PORTS,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{data_dir}/{config.STORAGE_DB}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is not None:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # Update Logging with new values
    configure_root_loger(logging_level, log_dir + config.STORAGE_LOGFILE)

    # Update celery
    celery_app.conf.update(app.config)

    # Update SQL Alchemy
    import storage_server.storage_database
    # noinspection PyUnresolvedReferences
    import lib.user_database
    # Needs to be imported so that table is created, too
    database.db.init_app(app)
    # For bloom filter
    from storage_server.connector import get_storageserver_backend
    with app.app_context():
        database.db.create_all()
        # Initialize Bloom Filter
        get_storageserver_backend()._initialize_bloom_filter()
    # Include pages
    from storage_server import main
    app.register_blueprint(main.bp)

    from storage_server import client
    app.register_blueprint(client.bp)

    from storage_server import provider
    app.register_blueprint(provider.bp)

    if config.EVAL:
        print("************************************************************")
        print("Starting in Eval Mode!")
        print("************************************************************")

    return app
