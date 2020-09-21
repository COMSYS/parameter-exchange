#!/usr/bin/env python3
"""Connector to backend and celery.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
import logging
import secrets
from typing import Dict

from celery import Task
from flask import g, current_app as app, request, url_for, render_template

from key_server.key_database import KeyRetrieval, HashKeyRetrieval
from lib import helpers
from lib.base_client import UserType
from lib.base_server import client_pw, provider_pw
from lib.database import db
from lib.helpers import to_base64
from lib.key_server_backend import KeyServer
from key_server import celery_app, database
from lib.user_database import get_user

log: logging.Logger = logging.getLogger(__name__)


class TaskType:
    """Allows key server tasks."""
    OT = "OT"


def get_keyserver_backend() -> KeyServer:
    """Return the request's backend KeyServer object and create one if it
    does not exists yet."""
    if 'keyserver' not in g:
        g.keyserver = KeyServer(app.config['DATA_DIR'])
    return g.keyserver


def get_hash_key(user_type: str, username: str) -> dict:
    """Return the hash key in Base64 encoding.

    :param username: Username
    :param user_type: Type of user
    :return on success looks like this:
            {
                'success': True,
                'hash_key': 'AAAAAAAAAAAAAAAAAAAAAQ=='
            }
    """
    app.logger.debug('Hash Key requested.')
    _add_to_hash_key_db(user_type, username)
    key = to_base64(get_keyserver_backend().get_hash_key())
    return {'success': True,
            'hash_key': key
            }


def _add_to_hash_key_db(user_type: str, username: str) -> HashKeyRetrieval:
    """
    Track access to get_hash_key in database.
    :param user_type: Type of user accessing API
    :param username: Username
    :return: Created DB object
    """
    u = get_user(user_type, username)
    if user_type == UserType.CLIENT:
        t = HashKeyRetrieval(
            client=u,
        )
    elif user_type == UserType.OWNER:
        t = HashKeyRetrieval(
            provider=u,
        )
    else:  # pragma no cover
        raise ValueError("Bad user type.")
    db.session.add(t)
    db.session.commit()
    return t


def _add_to_key_retrieval_db(user_type: str,
                             username: str,
                             num_ots: int) -> KeyRetrieval:
    """
    Track access to OT in database.
    :param user_type: Type of user accessing API
    :param username: Username
    :param num_ots: # OTs performed == # retrieved keys
    :return: Created DB object
    """
    u = get_user(user_type, username)
    if user_type == UserType.CLIENT:
        t = KeyRetrieval(
            client=u,
            retrieved_keys=num_ots
        )
    elif user_type == UserType.OWNER:
        t = KeyRetrieval(
            provider=u,
            retrieved_keys=num_ots
        )
    else:  # pragma no cover
        raise ValueError("Bad user type.")
    db.session.add(t)
    db.session.commit()
    return t


def retrieve_keys(user_type: str, username: str) -> dict:
    """
    Start an OT Server for encryption key retrieval.
    :param username: Username of User
    :param user_type: client or provider
    :return: Dict containing connection information:
             {
                'success': True,
                'port': "1213",
                'host': "127.0.0.1",
                'totalOTs': 10,
                'tls': True
            }
    """
    # Get Parameters
    total_ots = request.args.get('totalOTs', 0, type=int)
    try:
        if total_ots == 0:
            raise ValueError("No total OTs defined.")
    except ValueError as e:
        app.logger.warning(f"Key retrieval failed: {str(e)}")
        return {'success': False,
                'msg': str(e)}

    # Checks okay, start OT server
    port = secrets.randbelow(65536 - 1024) + 1024
    while not helpers.port_free(port):
        port = secrets.randbelow(65536 - 1024) + 1024  # pragma no cover
    if not app.config['KEY_RANDOMIZE_PORTS']:
        if helpers.port_free(1213):
            port = 1213
        else:
            app.logger.warning(f"Port 1213 already in use! Using {port} "
                               f"instead.")
    app.logger.info(f"Starting OT Sending instance on port {port}.")
    _add_to_key_retrieval_db(user_type, username, total_ots)
    task = execute_ot.delay(total_ots, port)
    if user_type == UserType.OWNER:
        from key_server.provider import provider_auth
        database.add_task(provider_auth.username(),
                          UserType.OWNER, task.id,
                          TaskType.OT)
    else:
        from key_server.client import client_auth
        database.add_task(client_auth.username(),
                          UserType.CLIENT, task.id,
                          TaskType.OT)
    app.logger.debug(f"OT Server Thread started on port {port}.")
    return {
        'success': True,
        'port': port,
        'host': app.config['OT_HOST'],
        'totalOTs': total_ots,
        'tls': app.config['OT_TLS']
    }


@celery_app.task(bind=True)
def execute_ot(self: Task, total_ots: int,
               port: int) -> None:  # pragma no cover
    """

    :param self: Celery task object
    :param total_ots: Number of OTs to perform
    :param port: Port to open the OT server on
    :return: None
    """
    log.info(f"Celery offering {total_ots} OTs on port {port}.")
    # Define time limit to kill task if it runs for too long, because the
    # python code has no access.
    self.time_limit = 3600
    self.update_state(state='STARTED')
    get_keyserver_backend().offer_ot(total_ots, port)
    self.update_state(state='SUCCESS')


def status_overview(user_type: str):
    """
    Display status of all background tasks of this user.
    :return: Page containing background task status.
    """
    if user_type == UserType.CLIENT:
        db_tasks = database.get_tasks(user_type,
                                      client_pw.username()
                                      )
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
                    <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
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
    TaskType.OT: execute_ot
}
