#!/usr/bin/env python3
"""Client Pages of storage server.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import secrets

from flask import Blueprint, jsonify, request, current_app as app
from flask_httpauth import HTTPBasicAuth

from lib import helpers, config, database
from lib.base_client import UserType
from lib.base_server import verify_token, gen_token, client_pw
from lib.database import db
from lib.storage_server_backend import StorageServer
from lib.user_database import get_user
from storage_server.connector import get_storageserver_backend, execute_psi, \
    status_overview, kill_task, task_status, TaskType
from storage_server.storage_database import PSIAccess, BloomAccess

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


def _track_bloom_access(user_type: str, username: str) -> BloomAccess:
    """
    Track an access to the Bloom API.
    :param user_type: Client or Owner
    :param username: Name of user
    :return: The created DB Object
    """
    u = get_user(user_type, username)
    if user_type == UserType.CLIENT:
        t = BloomAccess(
            client=u
        )
    else:  # pragma no cover
        raise ValueError("Bad user type.")
    db.session.add(t)
    db.session.commit()
    return t


@bp.route('/bloom')
@client_auth.login_required
def client_get_bloom() -> str:
    """
    Return a base64 encoding of the bloom filter encoding the storage
    server's record set.
    :return: Dict containing base64 encoded bloom filter
    """
    try:
        _track_bloom_access(UserType.CLIENT, client_auth.username())
        b = get_storageserver_backend().get_bloom_filter(
                        ).decode()
    except ValueError as e:
        return jsonify(
            {
                "success": False,
                "msg": str(e)
            })
    return jsonify(
        {
            "success": True,
            "bloom": b
        })


@bp.route('/retrieve_record', methods=['POST'])
@client_auth.login_required
def retrieve_record() -> str:
    """
    Retrieve record for the authenticated user.
    Requires JSON as POST data:
    {
        'hash':  Base64(Hash) [str]
    }
    :return: Dict containing ist of records matching the hash or error msg
            'records':
            [
                ['Base64(HASH)', 'json.dumps(CIPHERTEXT-1)'],
                ['Base64(HASH)', 'json.dumps(CIPHERTEXT-2)']
            ]
    """
    try:
        if request.json is None or 'hash' not in request.json:
            raise ValueError("Missing POST value 'hash'.")
        h = request.json['hash']
        r = StorageServer.get_record(h, client_auth.username())
    except ValueError as e:
        return jsonify({'success': False,
                        'msg': str(e)})
    return jsonify({'success': True,
                    'records': r})


@bp.route('/batch_retrieve_records', methods=['POST'])
@client_auth.login_required
def batch_retrieve_records() -> str:
    """
    Retrieve multiple records for the authenticated user.
    Requires JSON as POST data:
    {
        'hashes': [
                    Base64(Hash-1) [str],
                    Base64(Hash-2) [str],
                    ...
                  ]
    }
    :return: jsonified dict containing records on success and an error
             message otherwise. On success:
             'records':
             [
                ('Base64(HASH-1)', 'json.dumps(CIPHERTEXT-1)'),
                ('Base64(HASH-1)', 'json.dumps(CIPHERTEXT-2)'),
                ('Base64(HASH-2)', 'json.dumps(CIPHERTEXT-3)')
            ]
    """
    try:
        if request.json is None:
            raise KeyError("Missing POST value 'hashes'.")
        hash_list = request.json['hashes']
        r = StorageServer.batch_get_records(hash_list, client_auth.username())
    except KeyError:
        return jsonify({'success': False,
                        'msg': "Missing POST value 'hashes'."})
    return jsonify({'success': True,
                    'records': r})


def _track_PSI_access(user_type: str, username: str) -> PSIAccess:
    """
    Track an access to the PSI API.
    :param user_type: Client or Owner
    :param username: Name of user
    :return: The created DB Object
    """
    u = get_user(user_type, username)
    if user_type == UserType.CLIENT:
        t = PSIAccess(
            client=u
        )
    else:  # pragma no cover
        raise ValueError("Bad user type.")
    db.session.add(t)
    db.session.commit()
    return t


@bp.route('/psi')
@client_auth.login_required
def psi():
    """
    Start a PSI Server and return connection information.
    :return: Dict containing PSI Server access information.
    {
        'success': bool,
        'port': int,
        'host': str,
        'tls': bool,
        'setSize': int,
        'msg': str (On failure only)
    }
    """
    # Get free port
    port = secrets.randbelow(65536 - 1024) + 1024
    while not helpers.port_free(port):
        port = secrets.randbelow(65536 - 1024) + 1024  # pragma no cover
    if not app.config['RANDOMIZE_PORTS']:  # pragma no cover
        if helpers.port_free(config.PSI_PORT):
            port = config.PSI_PORT
        else:  # pragma no cover
            app.logger.warning(f"Port {config.PSI_PORT} already in use!"
                               f"Using {port} instead.")
    app.logger.info(f"Starting PSI Sending instance on port {port}.")
    _track_PSI_access(UserType.CLIENT, client_auth.username())
    task = execute_psi.delay(port)
    database.add_task(client_auth.username(),
                                         UserType.CLIENT,
                                         task.id, TaskType.PSI)
    app.logger.debug(f"PSI Server Thread started on port {port}.")
    return jsonify({
        'success': True,
        'port': port,
        'host': app.config['PSI_HOST'],
        'tls': app.config['PSI_TLS'],
        'setSize': config.PSI_SETSIZE
    })


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
    :param task_type: Type of celery task
    :param task_id: ID of celery task
    :return: None
    """
    return jsonify(task_status(task_type, task_id))


@bp.route('/<task_type>/kill/<task_id>')
@client_pw.login_required
def killtask(task_type: str, task_id: str):
    """Kill specified task.
    :param task_type: Type of celery task
    :param task_id: ID of celery task
    :return: None"""
    return jsonify(kill_task(task_type, task_id))
