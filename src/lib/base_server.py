#!/usr/bin/env python3
"""This file contains base server functionalities shared by both server
components.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging

import flask.wrappers
import redis
from flask import jsonify, current_app as app
from flask_httpauth import HTTPBasicAuth

from lib.base_client import UserType
import lib.user_database as db

log: logging.Logger = logging.getLogger(__name__)


def is_redis_online(port: int) -> bool:
    """Return true if redis is online."""
    rs = redis.Redis("localhost", port)
    try:
        rs.ping()
        return True  # pragma no cover
    except redis.ConnectionError:
        log.info("Redis offline.")
        return False


def verify_token(user_type: str, user: str, token: str) -> bool:
    """Verify if the get_token is correct for the given user and return the
    username if so or raise an error otherwise."""
    if 'LOGIN_DISABLED' in app.config and app.config['LOGIN_DISABLED']:
        return True
    try:
        if not db.verify_token(user_type, user, token):
            return False
    except ValueError as e:
        log.warning(str(e))
        return False
    return True


client_pw = HTTPBasicAuth()
provider_pw = HTTPBasicAuth()


@client_pw.verify_password
def verify_client_pw(user: str, pw: str) -> bool:
    """
    Verify that the credentials match those in the database.
    :param user: Username
    :param pw: Password
    :return: Authentication result.
    """
    if 'LOGIN_DISABLED' in app.config and app.config['LOGIN_DISABLED']:
        return True
    try:
        return db.verify_password(UserType.CLIENT, user, pw)
    except ValueError:
        return False


@provider_pw.verify_password
def verify_provider_pw(user: str, pw: str) -> bool:
    """
    Verify that the credentials match those in the database.
    :param user: Username
    :param pw: Password
    :return: Authentication result.
    """
    if 'LOGIN_DISABLED' in app.config and app.config['LOGIN_DISABLED']:
        return True
    try:
        return db.verify_password(UserType.OWNER, user, pw)
    except ValueError:
        return False


def gen_token(user_type: str, user: str) -> flask.wrappers.Response:
    """
    Generate and return a token for the given User.
    :param user_type: UserType.CLIENT or UserType.OWNER
    :param user: Username
    :return: A Jsonify response that can directly be returned
    """
    log.debug('Token requested.')
    try:
        resp = jsonify(
            {'success': True,
             'token': db.generate_token(user_type, user)
             })
    except ValueError as e:
        log.warning("gen_token: " + str(e))
        resp = jsonify(
            {
                'success': False,
                'msg': str(e)
            }
        )
    return resp
