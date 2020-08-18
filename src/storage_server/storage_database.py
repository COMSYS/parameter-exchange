#!/usr/bin/env python3
"""Database Models for storage server only.

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


class StoredRecord(db.Model):
    """
    SQLAlchemy class representing one record
    """
    hash = db.Column(db.Text, nullable=False, primary_key=True)
    ciphertext = db.Column(db.Text, nullable=False, primary_key=True)
    owner = db.Column(db.Text, nullable=False, primary_key=True)


class RecordRetrieval(db.Model):
    """
    SQLAlchemy class representing one data retrieval operation on the
    storage server only
    """
    __tablename__ = 'record_retrieval_accesses'

    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"),
                          nullable=False)
    client = db.relationship("Client",
                             uselist=False,
                             foreign_keys=[client_id])
    enc_keys_by_hash = db.Column(db.Integer, nullable=False)
    #  Number of encryption keys for all requested hashes
    enc_keys_by_records = db.Column(db.Integer, nullable=False)
    #  Number of encryption keys fo all returned records
    timestamp = db.Column(db.DateTime,
                          default=datetime.now(),
                          nullable=False)


class BillingInfo(db.Model):
    """
    SQLAlchemy class representing storage server billing information,
    i.e. the retrieval of a record by a data owner
    """
    __tablename__ = 'billing_information'
    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"),
                          nullable=False)
    client = db.relationship("Client",
                             uselist=False,
                             foreign_keys=[client_id])
    provider_id = db.Column(db.Integer,
                            db.ForeignKey("owner.id"),
                            nullable=False)
    provider = db.relationship("Owner",
                               uselist=False,
                               foreign_keys=[provider_id])
    count = db.Column(db.Integer, nullable=False)  # Num. of retr. items
    transaction_id = db.Column(db.Integer,
                               db.ForeignKey("record_retrieval_accesses.id"),
                               nullable=False)  # ID of transaction
    transaction = db.relationship("RecordRetrieval",
                                  uselist=False,
                                  foreign_keys=[transaction_id])
    timestamp = db.Column(db.DateTime, default=datetime.now(), nullable=False)


class BloomAccess(db.Model):
    """
    SQLAlchemy class representing one access to the Bloom API
    """
    __tablename__ = 'bloom_accesses'

    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"),
                          nullable=False)
    client = db.relationship("Client",
                             uselist=False,
                             foreign_keys=[client_id])
    timestamp = db.Column(db.DateTime,
                          default=datetime.now(),
                          nullable=False)


class PSIAccess(db.Model):
    """
    SQLAlchemy class representing one access to the PSI API
    """
    __tablename__ = 'psi_accesses'

    id = db.Column(db.Integer,
                   nullable=False,
                   primary_key=True)  # Auto
    client_id = db.Column(db.Integer,
                          db.ForeignKey("client.id"),
                          nullable=False)
    client = db.relationship("Client",
                             uselist=False,
                             foreign_keys=[client_id])
    timestamp = db.Column(db.DateTime,
                          default=datetime.now(),
                          nullable=False)
