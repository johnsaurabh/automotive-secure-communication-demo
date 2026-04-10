from __future__ import annotations

import argparse
import json
import socket
import ssl
import uuid
from datetime import datetime, timezone

from config import CA_CERT_PATH, CLIENT_CERT_PATH, CLIENT_KEY_PATH, CLIENT_LOG_PATH, SERVER_HOST, SERVER_PORT
from crypto.aes_utils import decrypt_payload, encrypt_payload
from crypto.cert_utils import ensure_certificates
from crypto.hash_utils import sha256_hex
from logging_utils import build_logger, redact_message
from protocol import decode_b64, encode_b64, recv_json, send_json


logger = build_logger("secure_client", CLIENT_LOG_PATH)


def create_client_context() -> ssl.SSLContext:
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(CA_CERT_PATH))
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.load_cert_chain(certfile=str(CLIENT_CERT_PATH), keyfile=str(CLIENT_KEY_PATH))
    context.check_hostname = True
    context.verify_mode = ssl.CERT_REQUIRED
    return context


def run_client(host: str = SERVER_HOST, port: int = SERVER_PORT, plaintext_message: str = "Brake status nominal") -> dict:
    ensure_certificates()
    context = create_client_context()

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname="localhost") as tls_socket:
            peer_cert = tls_socket.getpeercert()
            subject = dict(item[0] for item in peer_cert["subject"])
            server_cn = subject.get("commonName", "unknown")
            logger.info(
                "TLS server certificate verified",
                extra={"event": "authentication_success", "details": {"server_common_name": server_cn}},
            )

            key_message = recv_json(tls_socket)
            if key_message.get("message_type") != "session_key":
                raise ValueError("Server did not provide an AES session key")
            session_key = decode_b64(key_message["session_key_b64"])

            payload = {
                "message_id": str(uuid.uuid4()),
                "asset": "adas_domain_controller",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "telemetry": {
                    "ecu_id": "ECU-ADAS-01",
                    "vehicle_speed_kph": 42,
                    "lane_confidence": 0.98,
                    "status_text": plaintext_message,
                },
            }
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            nonce, ciphertext = encrypt_payload(session_key, payload_bytes)
            outbound = {
                "message_type": "secure_payload",
                "nonce_b64": encode_b64(nonce),
                "ciphertext_b64": encode_b64(ciphertext),
                "sha256": sha256_hex(payload_bytes),
            }
            send_json(tls_socket, outbound)
            logger.info(
                "Protected payload sent",
                extra={
                    "event": "message_sent",
                    "details": {
                        "message_id": payload["message_id"],
                        "payload_sha256": outbound["sha256"],
                        "status_preview": redact_message(plaintext_message),
                    },
                },
            )

            inbound = recv_json(tls_socket)
            if inbound.get("message_type") != "secure_response":
                raise ValueError("Unexpected response type received from server")
            response_nonce = decode_b64(inbound["nonce_b64"])
            response_ciphertext = decode_b64(inbound["ciphertext_b64"])
            response_bytes = decrypt_payload(session_key, response_nonce, response_ciphertext)
            if sha256_hex(response_bytes) != inbound["sha256"]:
                raise ValueError("Response integrity verification failed")

            response = json.loads(response_bytes.decode("utf-8"))
            logger.info(
                "Protected response received",
                extra={"event": "message_received", "details": {"message_id": response["message_id"], "status": response["status"]}},
            )
            return response


def main() -> None:
    parser = argparse.ArgumentParser(description="Secure TLS client with application-level AES protection")
    parser.add_argument("--host", default=SERVER_HOST)
    parser.add_argument("--port", type=int, default=SERVER_PORT)
    parser.add_argument("--message", default="Brake status nominal")
    args = parser.parse_args()

    response = run_client(host=args.host, port=args.port, plaintext_message=args.message)
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    main()
