#!/usr/bin/env python3
"""Application factory for keyserver app.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import os

from celery import Celery
from flask import Flask

from lib import config, database
from lib.key_server_backend import KeyServer
from lib.logging import configure_root_loger

# Configure logging
# configure_root_loger(config.LOGLEVEL)
celery_app = Celery(__name__, broker=config.KEY_CELERY_BROKER_URL)


def create_app(test_config=None, logging_level=config.LOGLEVEL,
               data_dir=config.DATA_DIR) -> Flask:
    """Factory function for flask app. Return a configured flask app object."""

    # Configure App
    app = Flask(__name__, instance_relative_config=True)
    redis_port = config.KEY_REDIS_PORT
    if test_config is not None and 'DATA_DIR' in test_config:
        data_dir = test_config['DATA_DIR']
    log_dir = data_dir + 'logs/'
    app.config.from_mapping(
        REDIS_PORT=redis_port,
        CELERY_BROKER_URL=config.KEY_CELERY_BROKER_URL,
        CELERY_RESULT_BACKEND=config.KEY_CELERY_BROKER_URL,
        HASHKEY_LEN=config.HASHKEY_LEN,
        KEY_RANDOMIZE_PORTS=config.RANDOMIZE_PORTS,
        OT_HOST=config.OT_HOST,
        OT_TLS=config.OT_TLS,
        DATA_DIR=data_dir,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{data_dir}/{config.KEYSERVER_DB}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is not None:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    # Update Logging with new values
    configure_root_loger(logging_level, log_dir + config.KEY_LOGFILE)

    # Update Celery
    celery_app.conf.update(app.config)

    # Update SQL Alchemy
    import key_server.key_database
    # noinspection PyUnresolvedReferences
    import lib.user_database
    # Needs to be imported so that table is created, too
    database.db.init_app(app)
    with app.app_context():
        database.db.create_all()

    # Include pages
    from key_server import main
    app.register_blueprint(main.bp)

    from key_server import client
    app.register_blueprint(client.bp)

    from key_server import provider
    app.register_blueprint(provider.bp)

    # Generate keys
    KeyServer(app.config['DATA_DIR'])

    if config.EVAL:
        print("************************************************************")
        print("Starting in Eval Mode!")
        print("************************************************************")

    return app
