#!/usr/bin/env python3
"""Client Pages of key server.

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
from lib.base_server import verify_token, client_pw, gen_token

log: logging.Logger = logging.getLogger(__name__)


bp = Blueprint('/client', __name__, url_prefix='/client')
client_auth = HTTPBasicAuth()


@client_auth.verify_password
def client_verify_token(user: str, token: str) -> bool:
    """
    Verify whether the token is valid for this client.
    :param user: Username of client.
    :param token: Token to verify.
    :return: True if token is valid for user, false otherwise.
    """
    return verify_token(UserType.CLIENT, user, token)


@bp.route('/gen_token')
@client_pw.login_required
def client_gen_token() -> str:
    """
    Generate a new token for the logged-in user.
    :return: A JSON containing an error message on failure or the token on
    success.
    """
    return gen_token(UserType.CLIENT, client_pw.username())


@bp.route('/hash_key')
@client_auth.login_required
def client_get_hash_key() -> str:
    """
    Return the hash key for the logged-in user.
    :return: JSON containing the hash key or an error message.
    """
    return jsonify(get_hash_key(UserType.CLIENT, client_auth.username()))


@bp.route('/key_retrieval')
@client_auth.login_required
def client_retrieve_keys() -> str:
    """Start an OT Server for encryption key retrieval.

    :return: Connection information for OT server.
    """
    return jsonify(retrieve_keys(UserType.CLIENT, client_auth.username()))


@bp.route('/status')
@client_pw.login_required
def status():
    """
    Display status of all background tasks of this user.
    :return: Page containing background task status.
    """
    return status_overview(UserType.CLIENT)


@bp.route('/<task_type>/status/<task_id>')
@client_pw.login_required
def taskstatus(task_type: str, task_id: str):
    """
    Return status of the defined background celery task.
    """
    return jsonify(task_status(task_type, task_id))


@bp.route('/<task_type>/kill/<task_id>')
@client_pw.login_required
def killtask(task_type: str, task_id: str):
    """Kill specified task."""
    return jsonify(kill_task(task_type, task_id))
