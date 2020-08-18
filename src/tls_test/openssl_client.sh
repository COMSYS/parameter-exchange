CURRENT_DIR=$(python3 -c "import os; print(os.path.realpath('$0'))")
CURRENT_DIR="$(dirname "$CURRENT_DIR")"
SRC="$(dirname "$CURRENT_DIR")"
CERT_DIR="$(dirname "$SRC")/data/certs/"
CERT="${CERT_DIR}keyserver.crt"
KEY="${CERT_DIR}keyserver.key"
ROOTCA="${CERT_DIR}rootCA.crt"
DHPARAM="${CERT_DIR}dhparam.pem"
CIPHER="ECDHE-RSA-AES256-GCM-SHA384;DHE-RSA-AES256-GCM-SHA384"
CURVES="secp384r1"
PORT=5000

openssl s_client -port "${PORT}" -tls1_2  -CAfile "$ROOTCA" -msg # -curves "${CURVES}" -cipher "${CIPHER}"
