#!/usr/bin/env bash
CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$1'))")
BASE_DIR="$(dirname "$CURRENT_DIR")"
cd $BASE_DIR/src || exit
tmux new-session -d -s 'celery' -n 'redis'
tmux send-keys 'redis-server --port 6379' 'C-m'
tmux split-window -t 'celery':0 -h
tmux send-keys 'redis-server --port 6380' 'C-m'
tmux new-window -t 'celery':1 -n 'celery'
tmux send-keys 'celery worker -A key_server.celery.celery_app --loglevel=info' 'C-m'
tmux split-window -h
tmux send-keys 'celery worker -A storage_server.celery.celery_app --loglevel=info' 'C-m'
