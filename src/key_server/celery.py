#!/usr/bin/env python
"""Startup script for celery worker.

Copyright (c) 2020.
Author: Erik Buchholz
Maintainer: Erik Buchholz
E-mail: buchholz@comsys.rwth-aachen.de
"""
# noinspection PyUnresolvedReferences
from key_server import celery_app, create_app

app = create_app()
app.app_context().push()
