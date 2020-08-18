#!/usr/bin/env python3
"""Database Models shared by both server types.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
from datetime import datetime
from typing import List

from flask_sqlalchemy import SQLAlchemy
import logging

db = SQLAlchemy()
log: logging.Logger = logging.getLogger(__name__)


class Task(db.Model):
    """
    SQLAlchemy Class representing one celery task
    """

    id = db.Column(db.Text, primary_key=True, nullable=False)
    user_id = db.Column(db.Text, nullable=False)
    task_type = db.Column(db.Text, nullable=False)
    user_type = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now())

    def __repr__(self):
        return f"<Task {self.id}>"


def add_task(username: str, user_type: str, task_id: str,
             task_type: str) -> None:
    """Store task into DB."""
    task = Task(user_id=username, user_type=user_type,
                id=task_id, task_type=task_type)
    db.session.add(task)
    db.session.commit()
    log.debug(f"Successfully stored task {task_id} into DB.")


def get_tasks(user_type: str, username: str) -> List[Task]:
    """Return all tasks of the given user."""
    res = Task.query.filter_by(user_id=username,
                               user_type=user_type
                               ).order_by(Task.timestamp).all()
    return res
