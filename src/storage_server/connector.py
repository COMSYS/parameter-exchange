#!/usr/bin/env python3
"""Connector to backend and celery.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
from typing import Dict, List

from celery import Task
from flask import g, current_app as app, render_template, url_for

from lib import database
from lib.base_client import UserType
from lib.base_server import client_pw, provider_pw
from lib.storage_server_backend import StorageServer
from . import celery_app

log: logging.Logger = logging.getLogger(__name__)


class TaskType:
    """Allows storage server tasks."""
    PSI = "PSI"
    BLOOM_INSERT = "BLOOM_INSERT"


def get_storageserver_backend() -> StorageServer:
    """Return the flask request's backend StorageServer object and create
    one if none exists."""
    if 'storageserver' not in g:
        g.storageserver = StorageServer(app.config['DATA_DIR'])
    return g.storageserver


def _batch_store_records(record_list: List[List[str]], username: str) -> None:
    """
    Batch storage of records.
    :param record_list: List of records to store of the following form:
    [
        ('hash1', 'record1', 'owner1'),
        ('hash2', 'record2', 'owner2')
    ]
    :return: None
    """
    StorageServer.batch_store_records_db(record_list)
    task = insert_bloom.delay(record_list)
    database.add_task(username,
                      UserType.OWNER,
                      task.id, TaskType.BLOOM_INSERT)


@celery_app.task(bind=True)  # pragma no cover
def execute_psi(self: Task, port: int) -> None:
    """Execute PSI with celery."""
    log.info(f"Celery offering PSI on Port {port}.")
    self.time_limit = 3600
    self.update_state(state='STARTED')
    StorageServer.offer_psi(port=port)
    self.update_state(state='SUCCESS')


@celery_app.task(bind=True)  # pragma no cover
def insert_bloom(self: Task, record_list: List[List[str]]) -> None:
    """Bloom Filter insertion done via celery becasue of high fluctuation
    in eval."""
    log.info(f"Celery Inserting values into Bloom Filter.")
    self.time_limit = 3600
    self.update_state(state='STARTED')
    get_storageserver_backend().batch_store_records_bloom(record_list)
    self.update_state(state='SUCCESS')


def status_overview(user_type: str):
    """
    Display status of all background tasks of this user.
    :return: Page containing background task status.
    """
    if user_type == UserType.CLIENT:
        db_tasks = database.get_tasks(user_type,
                                      client_pw.username())
    elif user_type == UserType.OWNER:
        db_tasks = database.get_tasks(
            user_type, provider_pw.username())
    else:
        raise ValueError("Unknown User Type.")
    tasks = []
    for db_task in db_tasks:
        if db_task.task_type in Tasks:
            task = Tasks[db_task.task_type].AsyncResult(db_task.id)
        else:
            raise ValueError("Unknown Task Type.")
        d = {
            'id': db_task.id,
            'type': db_task.task_type,
            'status': task.state,
            'time': db_task.timestamp,
            'error': "None",
            'task_url': url_for(f'/{user_type}.taskstatus', task_id=task.id,
                                task_type=db_task.task_type),
            'kill_url': url_for(f'/{user_type}.killtask', task_id=task.id,
                                task_type=db_task.task_type)
        }
        if task.state == 'FAILURE':
            d['error'] = str(task.info)
        tasks.append(d)
    g.tasks = sorted(tasks, key=lambda k: k['time'],
                     reverse=True)
    return render_template('status.html')


def task_status(task_type: str, task_id: str) -> Dict or str:
    """
    Return status of the defined background celery task.
    :param task_type: Type of task that shall be checked
    :param task_id: ID of the task
    :return: Status of the task as JSON
    """
    if task_type in Tasks:
        task = Tasks[task_type].AsyncResult(task_id)
    else:
        return """
                            <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 
                            Final//EN">
                            <title>404 Not Found</title>
                            <h1>Not Found</h1>
                            <p>No such task type exists.</p>
                       """, 404

    if task.state == 'PENDING':
        # job did not start yet
        response = {
            'state': task.state
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state
        }
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return response


def kill_task(task_type: str, task_id: str) -> Dict or str:
    """
        Return status of the defined background celery task.
        :param task_type: Type of task that shall be checked
        :param task_id: ID of the task
        :return: Status of the task as JSON
        """
    if task_type in Tasks:
        task = Tasks[task_type].AsyncResult(task_id)
    else:
        return """
                        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
                        <title>404 Not Found</title>
                        <h1>Not Found</h1>
                        <p>No such task type exists.</p>
                   """, 404

    if task.state != 'STARTED':
        # job did not start yet
        response = {
            'success': False,
            'msg': 'Task not running.'
        }
    else:
        log.warning(f"Killing Task '{task_id}'.")
        task.revoke(terminate=True, signal='SIGKILL')
        response = {
            'success': True,
            'msg': None
        }
    return response


Tasks = {
    TaskType.PSI: execute_psi,
    TaskType.BLOOM_INSERT: insert_bloom,
}
