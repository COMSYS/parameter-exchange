#!/usr/bin/env python3
"""Provider Pages of storage server.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging

from flask import Blueprint, request, jsonify
from flask_httpauth import HTTPBasicAuth

from lib.base_client import UserType
from lib.base_server import verify_token, gen_token, provider_pw
from storage_server.connector import (_batch_store_records,
                                      get_storageserver_backend,
                                      status_overview, task_status, kill_task)

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


@bp.route('/store_record', methods=['POST'])
@provider_auth.login_required
def store_record() -> None:
    """
    Store a record into the database.
    Requires request JSON as HTTP POST data:
    {
        'hash': Base64(Hash)[str]
        'ciphertext': json.dumps(ciphertext)[str]
        'owner': 'ownername'[str]
    }
    :return: None
    """
    try:
        if request.json is None:
            raise ValueError("Empty POST JSON.")
        try:
            hash_val: str = request.json['hash']
            ciphertext: str = request.json['ciphertext']
            owner: str = request.json['owner']
        except KeyError:
            raise ValueError("Require 'hash', 'ciphertext' and 'owner'.")
        if owner != provider_auth.username():
            raise ValueError("Owner in JSON not authenticated owner.")
    except ValueError as e:
        return jsonify({
            'success': False,
            'msg': f"Invalid POST data: {str(e)}"
        })

    log.info(f"Store record: {hash_val} - {ciphertext} of {owner}")
    try:
        get_storageserver_backend().store_record(hash_val, ciphertext, owner)
    except Exception as e:
        log.exception(f"Failed to store record: {str(e)}")
        return jsonify({
            'success': False,
            'msg': str(e)
        })
    return jsonify({
        'success': True,
        'msg': None
    })


@bp.route('/batch_store_records', methods=['POST'])
@provider_auth.login_required
def batch_store_records() -> None:
    """
    Store many records into the database.
    Requires a JSON as HTTP POST data:
    [
        [Base64(Hash-1)[str], json.dumps(ciphertext-1)[str], 'owner'[str]],
        [Base64(Hash-2)[str], json.dumps(ciphertext-2)[str], 'owner'[str]],
        [Base64(Hash-2)[str], json.dumps(ciphertext-3)[str], 'owner'[str]],
    ]
    :return: None
    """
    log.info(f"Batch Store Records")
    record_list = request.json
    owner = provider_auth.username()

    try:
        if request.json is None:
            raise ValueError("Missing POST values.")
        if not isinstance(record_list, list):
            raise ValueError(f"batch_store_records received non list"
                             f": {record_list}")
        for item in record_list:
            if not len(item) == 3 or not isinstance(item, list):
                raise ValueError(f"Record list contained bad item: {item}")
            for i in item:
                if not isinstance(i, str):
                    raise ValueError(f"Record list contained bad item: {item}")
            # Verify that owner is correct
            if item[2] != owner:
                raise ValueError(
                    f"Different owner in record than authenticated owner!")
    except ValueError as e:
        log.warning(str(e))
        return jsonify({
            'success': False,
            'msg': str(e)
        })
    _batch_store_records(record_list, owner)
    return jsonify({
        'success': True,
        'msg': None
    })


@bp.route('/status')
@provider_pw.login_required
def status():
    """
    Display status of all background tasks of this user.
    :return: Page containing background task status.
    """
    return status_overview(UserType.OWNER)


@bp.route('/<task_type>/status/<task_id>')
@provider_pw.login_required
def taskstatus(task_type: str, task_id: str):
    """
    Return status of the defined background celery task.
    :param task_type: Type of celery task
    :param task_id: ID of celery task
    :return: None
    """
    return jsonify(task_status(task_type, task_id))


@bp.route('/<task_type>/kill/<task_id>')
@provider_pw.login_required
def killtask(task_type: str, task_id: str):
    """Kill specified task.
    :param task_type: Type of celery task
    :param task_id: ID of celery task
    :return: None"""
    return jsonify(kill_task(task_type, task_id))
