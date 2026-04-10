from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CERTS_DIR = BASE_DIR / "certs"
LOGS_DIR = BASE_DIR / "logs"

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8443
BUFFER_SIZE = 8192

TLS_VERSION = "TLSv1.3"

CA_CERT_PATH = CERTS_DIR / "ca_cert.pem"
CA_KEY_PATH = CERTS_DIR / "ca_key.pem"

SERVER_CERT_PATH = CERTS_DIR / "server_cert.pem"
SERVER_KEY_PATH = CERTS_DIR / "server_key.pem"

CLIENT_CERT_PATH = CERTS_DIR / "client_cert.pem"
CLIENT_KEY_PATH = CERTS_DIR / "client_key.pem"

SERVER_LOG_PATH = LOGS_DIR / "server_audit.log"
CLIENT_LOG_PATH = LOGS_DIR / "client_audit.log"

AES_KEY_SIZE = 32
GCM_NONCE_SIZE = 12
