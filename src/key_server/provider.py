#!/usr/bin/env python3
"""Provider Pages of key server.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging

from flask import (Blueprint, jsonify)
from flask_httpauth import HTTPBasicAuth

from key_server.connector import get_hash_key, retrieve_keys, \
    kill_task, task_status, status_overview
from lib.base_client import UserType
from lib.base_server import verify_token, provider_pw, gen_token

log: logging.Logger = logging.getLogger(__name__)

bp = Blueprint('/provider', __name__, url_prefix='/provider')
provider_auth = HTTPBasicAuth()


@provider_auth.verify_password
def provider_verify_token(user: str, token: str) -> bool:
    """
    Verify whether the token is valid for this data provider.
    :param user: Username of data provider.
    :param token: Token to verify.
    :return: True if token is valid for user, false otherwise.
    """
    return verify_token(UserType.OWNER, user, token)


@bp.route('/gen_token')
@provider_pw.login_required
def provider_gen_token() -> str:
    """
    Generate a new token for the logged-in user.
    :return: A JSON containing an error message on failure or the token on
    success.
    """
    return gen_token(UserType.OWNER, provider_pw.username())


@bp.route('/hash_key')
@provider_auth.login_required
def provider_get_hash_key() -> str:
    """
    Return the hash key for the logged-in user.
    :return: JSON containing the hash key or an error message.
    """
    return jsonify(get_hash_key(UserType.OWNER, provider_auth.username()))


@bp.route('/key_retrieval')
@provider_auth.login_required
def provider_retrieve_keys() -> str:
    """Start an OT Server for encryption key retrieval.

    :return: Connection information for OT server.
    """
    log.debug("Provider key_retrieval accessed.")
    return jsonify(retrieve_keys(UserType.OWNER, provider_auth.username()))


@bp.route('/status')
@provider_pw.login_required
def status():
    """
    Display status of all background tasks of this user.
    :return: Page containing background task status.
    """
    return status_overview("provider")


@bp.route('/<task_type>/status/<task_id>')
@provider_pw.login_required
def taskstatus(task_type: str, task_id: str):
    """
    Return status of the defined background celery task.
    """
    return jsonify(task_status(task_type, task_id))


@bp.route('/<task_type>/kill/<task_id>')
@provider_pw.login_required
def killtask(task_type: str, task_id: str):
    """Kill specified task."""
    return jsonify(kill_task(task_type, task_id))
