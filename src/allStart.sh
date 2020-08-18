#!/usr/bin/env bash
CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$0'))")
BASE_DIR="$(dirname "$CURRENT_DIR")"
BASE_DIR="$(dirname "$BASE_DIR")"
SESSION_NAME='Server'
if [ $# -ge 1 ]; then
    SESSION_NAME=$1
fi
cd $BASE_DIR/src || exit
tmux new-session -d -s $SESSION_NAME -n 'Redis'
tmux send-keys -t $SESSION_NAME:0 'redis-server --port 6379' 'C-m'
tmux split-window -t $SESSION_NAME:0 -h
tmux send-keys -t $SESSION_NAME:0 'redis-server --port 6380' 'C-m'
tmux new-window -t $SESSION_NAME:1 -n 'Key Server'
tmux send-keys -t $SESSION_NAME:1 'celery worker -A key_server.celery.celery_app --loglevel=info' 'C-m'
tmux split-window -t $SESSION_NAME:1 -h
tmux send-keys -t $SESSION_NAME:1 './startKeyServer.sh' 'C-m'
tmux new-window -t $SESSION_NAME:2 -n 'Storage Server'
tmux send-keys -t $SESSION_NAME:2 'celery worker -A storage_server.celery.celery_app --loglevel=info' 'C-m'
tmux split-window -t $SESSION_NAME:2 -h
tmux send-keys -t $SESSION_NAME:2 './startStorageServer.sh' 'C-m'
tmux new-window -t $SESSION_NAME:3 -n 'Client'
