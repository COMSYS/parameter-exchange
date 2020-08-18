#!/usr/bin/env bash
CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$1'))")
BASE_DIR="$(dirname "$CURRENT_DIR")"
CERT_PATH="$BASE_DIR/data/certs/"
export FLASK_APP=key_server
if [ "$(uname)" == "Darwin" ]; then
  # Mac OS X
  export LANG=de_DE.UTF-8
else
  # Linux
  export LANG=C.UTF-8
fi
python3 -m flask run --host=0.0.0.0 --port=5000 --cert="${CERT_PATH}keyserver.crt" --key="${CERT_PATH}keyserver.key"