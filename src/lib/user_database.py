#!/usr/bin/env python3
"""User management for access control.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import secrets
import sqlite3
from abc import abstractmethod
from typing import List, Callable

import sqlalchemy
from werkzeug.security import generate_password_hash, check_password_hash

from lib.base_client import UserType
from lib.database import db

log: logging.Logger = logging.getLogger(__name__)


class Token(db.Model):
    """Represents one token"""

    __tablename__ = "tokens"

    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    value = db.Column(db.Text, nullable=False)
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"))
    provider_id = db.Column(db.Integer,
                            db.ForeignKey("owner.id"))


class User:
    """Abstract base class for users."""

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)

    @property
    @abstractmethod
    def tokens(self):  # pragma no cover
        """List of tokens of user"""
        pass

    # Was needed for shared table
    # type = db.Column(db.String(20), nullable=False)
    # __mapper_args__ = {
    #     'polymorphic_on': type,
    #     'polymorphic_identity': 'User'
    # }


class Client(User, db.Model):
    """Client-type end-users."""

    tokens = db.relationship("Token",
                             uselist=True,
                             backref='client',
                             lazy=False)
    # __mapper_args__ = {
    #     'polymorphic_identity': UserType.CLIENT
    # }


class Owner(User, db.Model):
    """Data Providers."""

    tokens = db.relationship("Token",
                             uselist=True,
                             backref='provider',
                             lazy=False)
    # __mapper_args__ = {
    #     'polymorphic_identity': UserType.OWNER
    # }


def verify_password(user_type: str, user_id: str, pwd: str) -> bool:
    """Return whether the password is correct for the user with the
    given user_id. Raises Value error if user does not exist."""
    UserCls = get_user_type(user_type)
    u: User = UserCls.query.filter_by(username=user_id).first()
    if u is None:
        raise ValueError(f"No {user_type} with ID '{user_id}' exists.")
    return check_password_hash(u.password, pwd)


def verify_token(user_type: str, user_id: str, token: str):
    """Return whether the token is correct for the user with the
    given user_id.
    Furthermore, remove token hash from DB because tokens can only be
    used once.
    """
    UserCls = get_user_type(user_type)
    u: User = UserCls.query.filter_by(username=user_id).first()
    if u is None:
        raise ValueError(f"No {user_type} with ID '{user_id}' exists.")
    tokens = u.tokens
    if len(u.tokens) == 0:
        msg = f"No token for user '{user_id}' exists."
        raise ValueError(msg)
    for t in tokens:
        if check_password_hash(t.value, token):
            logging.debug("Token correct.")
            # Remove token from DB
            db.session.delete(t)
            db.session.commit()
            return True
    return False


def _generate_token() -> str:
    """Generate a random token and return it along the corresponding
    SHA3 Hash."""
    token = secrets.token_urlsafe(64)
    return token


def generate_token(user_type: str, user_id: str):
    """Generate and return a new token for the user with the given
    ID. """
    UserCls = get_user_type(user_type)
    token = _generate_token()
    u: User = UserCls.query.filter_by(username=user_id).first()
    if u is None:
        raise ValueError(f"Could not generate token: No user '{user_id}' "
                         f"exists.")
    token_val = generate_password_hash(token, salt_length=32)
    t = Token(value=token_val)
    db.session.add(t)
    u.tokens.append(t)
    db.session.commit()
    log.info(f"Generated new token for '{user_id}'.")
    return token


def update_password(user_type: str, user_id: str, old_pwd: str, new_pwd: str):
    """Update the password if the credentials are correct."""
    UserCls = get_user_type(user_type)
    if not verify_password(user_type, user_id, old_pwd):
        msg = f"Password change for user '{user_id}' failed because old " \
              f'password is wrong.'
        raise ValueError(msg)
    if len(new_pwd) < 8:
        msg = "Password needs to have at least 8 characters!"
        raise ValueError(msg)
    pwd_hash = generate_password_hash(new_pwd, salt_length=32)
    u: UserCls = UserCls.query.filter_by(username=user_id).first()
    u.password = pwd_hash
    db.session.commit()
    log.info(f"Successfully updated password for '{user_id}'.")


def get_all_users(user_type: str) -> List[str]:
    """Return a list containing all user IDs"""
    UserCls = get_user_type(user_type)
    users = UserCls.query.all()
    return [u.username for u in users]


def add_user(user_type: str, user_id: str, password: str):
    """Add a new client, generate a token for API access and return
    it.
    """
    UserCls: Callable = get_user_type(user_type)
    if len(password) < 8:
        msg = "Password needs to have at least 8 characters!"
        raise ValueError(msg)
    pwd_hash = generate_password_hash(password, salt_length=32)
    token = generate_password_hash(_generate_token(), salt_length=32)
    # noinspection PyUnresolvedReferences
    try:
        u = UserCls(username=user_id, password=pwd_hash)
        t = Token(value=token)
        u.tokens.append(t)
        db.session.add(t)
        db.session.add(u)
        db.session.commit()
    except (sqlalchemy.orm.exc.FlushError,
            sqlalchemy.exc.InvalidRequestError,
            sqlalchemy.exc.IntegrityError,
            sqlite3.IntegrityError):
        db.session.rollback()
        msg = f"{user_type.capitalize()} ID '{user_id}' already in use!"
        raise ValueError(msg)
    log.info(f"Successfully stored '{user_id}' in DB.")
    return token


def get_user_type(user_type: str) -> [User]:
    """
    Return the class corresponding to the given user_type
    :param user_type: Type of user
    :return: Class representing that user user_type.
    """
    if user_type == UserType.CLIENT:
        return Client
    elif user_type == UserType.OWNER:
        return Owner
    else:
        raise TypeError(f"No such User Type exists: {user_type}")


def get_user(user_type: str, username: str) -> [Client, Owner]:
    """
    Return the user with the given username
    :param user_type: Client or Owner
    :param username: username to check
    :return: The user object
    """
    UserCls = get_user_type(user_type)
    c = UserCls.query.filter_by(username=username).first()
    if c is None:
        raise ValueError(
            f"{user_type.capitalize()} '{username}'does not exist!")
    return c
