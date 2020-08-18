#!/usr/bin/env bash
# Echo Server for TLS Perfomance Evaluation
# Start this script in another terminal before starting 'tls_client.py.'

DIR=$(python3 -c "import os; print(os.path.realpath('$0'))")
CERT_DIR="$(dirname "$(dirname "$(dirname "$DIR")")")/data/certs/"
CERT="${CERT_DIR}keyserver.crt"
KEY="${CERT_DIR}keyserver.key"
ROOTCA="${CERT_DIR}rootCA.crt"
DHPARAM="${CERT_DIR}dhparam.pem"
CIPHER="ECDHE-RSA-AES256-GCM-SHA384"
CURVES="prime256v1"  # secp256r1  is called prime256v1 in OpenSSL
PORT=5000
NACCEPT=100000

openssl s_server -cert "$CERT" -key "$KEY" -port "$PORT" -tls1_2  -cert_chain "$ROOTCA" -dhparam "$DHPARAM" \
                 -naccept "$NACCEPT" -rev # -cipher "$CIPHER" -curves "$CURVES" -msg