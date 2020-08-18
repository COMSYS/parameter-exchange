#!/usr/bin/env python3
"""Blueprint for main pages.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import os
from typing import Any

from flask import (Blueprint, render_template, g, current_app,
                   send_from_directory)

from lib.base_server import is_redis_online

log: logging.Logger = logging.getLogger(__name__)


bp = Blueprint('main', __name__)


@bp.route('/favicon.ico')
def favicon() -> Any:
    """Return key server favicon."""
    return send_from_directory(os.path.join(current_app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft'
                                                       '.icon')


def is_celery_online() -> bool:
    """Return True if celery is reachable, False otherwise."""
    from key_server import celery_app
    s = celery_app.control.inspect().ping()
    if s is None:
        return False
    else:
        return True


@bp.route('/')
def main() -> str:
    """State whether server is running including redis and celery."""
    g.redis_online = is_redis_online(current_app.config['REDIS_PORT'])
    g.celery_online = is_celery_online()
    return render_template('index.html')


@bp.route('/celery')
def celery_status() -> str:
    """Return True if celery is started correctly and false otherwise."""
    return str(is_celery_online())
