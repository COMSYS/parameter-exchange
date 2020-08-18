#!/usr/bin/env bash

CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$0'))")
CURRENT_DIR="$(dirname "$CURRENT_DIR")"

python3 $CURRENT_DIR/owner_db_cli.py testuser password -a
python3 $CURRENT_DIR/owner_db_cli.py testprovider password -a
python3 $CURRENT_DIR/client_db_cli.py testuser password -a
