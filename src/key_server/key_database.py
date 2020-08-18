#!/usr/bin/env python3
"""Database Models for key server only.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
from datetime import datetime

from lib.database import db
# noinspection PyUnresolvedReferences
from lib.user_database import Client, Owner
# Need to be imported for the foreign key to work


class KeyRetrieval(db.Model):
    """
    SQLAlchemy class representing one key retrieval operation on the
    key server only
    """
    __tablename__ = 'key_retrievals'

    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"))
    client = db.relationship("Client",
                             uselist=False,
                             foreign_keys=[client_id])
    provider_id = db.Column(db.Integer,
                            db.ForeignKey("owner.id"))
    provider = db.relationship("Owner",
                               uselist=False,
                               foreign_keys=[provider_id])
    retrieved_keys = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime,
                          default=datetime.now(),
                          nullable=False)


class HashKeyRetrieval(db.Model):
    """
        SQLAlchemy class storing all hash key retrieval operations.
    """
    __tablename__ = 'hash_key_retrievals'

    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"))
    client = db.relationship("Client",
                             uselist=False,
                             foreign_keys=[client_id])
    provider_id = db.Column(db.Integer,
                            db.ForeignKey("owner.id"))
    provider = db.relationship("Owner",
                               uselist=False,
                               foreign_keys=[provider_id])
    timestamp = db.Column(db.DateTime,
                          default=datetime.now(),
                          nullable=False)
