from __future__ import annotations

import argparse
import json
import secrets
import socket
import ssl
from datetime import datetime, timezone

from config import (
    AES_KEY_SIZE,
    CA_CERT_PATH,
    SERVER_CERT_PATH,
    SERVER_HOST,
    SERVER_KEY_PATH,
    SERVER_LOG_PATH,
    SERVER_PORT,
)
from crypto.aes_utils import decrypt_payload, encrypt_payload, generate_aes_key
from crypto.cert_utils import ensure_certificates
from crypto.hash_utils import sha256_hex
from logging_utils import build_logger
from protocol import decode_b64, encode_b64, recv_json, send_json


logger = build_logger("secure_server", SERVER_LOG_PATH)


def create_server_context() -> ssl.SSLContext:
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    context.verify_mode = ssl.CERT_REQUIRED
    context.load_cert_chain(certfile=str(SERVER_CERT_PATH), keyfile=str(SERVER_KEY_PATH))
    context.load_verify_locations(cafile=str(CA_CERT_PATH))
    return context


def run_server(host: str = SERVER_HOST, port: int = SERVER_PORT) -> None:
    ensure_certificates()
    context = create_server_context()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((host, port))
        listener.listen(5)
        print(f"Secure server listening on {host}:{port}")
        logger.info(
            "Server started",
            extra={"event": "server_start", "details": {"host": host, "port": port}},
        )

        while True:
            client_socket, address = listener.accept()
            logger.info(
                "Incoming connection",
                extra={"event": "connection_attempt", "details": {"source_ip": address[0], "source_port": address[1]}},
            )
            try:
                with context.wrap_socket(client_socket, server_side=True) as tls_socket:
                    peer_cert = tls_socket.getpeercert()
                    subject = dict(item[0] for item in peer_cert["subject"])
                    common_name = subject.get("commonName", "unknown")
                    logger.info(
                        "Mutual TLS authentication succeeded",
                        extra={"event": "authentication_success", "details": {"client_common_name": common_name}},
                    )
                    _handle_session(tls_socket, common_name)
            except ssl.SSLError as exc:
                logger.warning(
                    "TLS authentication failed",
                    extra={"event": "authentication_failure", "details": {"source_ip": address[0], "reason": str(exc)}},
                )
            except Exception as exc:
                logger.exception(
                    "Server error",
                    extra={"event": "server_error", "details": {"source_ip": address[0], "reason": str(exc)}},
                )


def _handle_session(tls_socket: ssl.SSLSocket, client_name: str) -> None:
    session_key = generate_aes_key(AES_KEY_SIZE)
    handshake_message = {
        "message_type": "session_key",
        "session_key_b64": encode_b64(session_key),
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "key_id": secrets.token_hex(8),
    }
    send_json(tls_socket, handshake_message)
    logger.info(
        "Ephemeral AES session key delivered inside TLS channel",
        extra={"event": "session_key_issued", "details": {"client_common_name": client_name, "key_id": handshake_message["key_id"]}},
    )

    inbound = recv_json(tls_socket)
    if inbound.get("message_type") != "secure_payload":
        raise ValueError("Unexpected message type received from client")

    nonce = decode_b64(inbound["nonce_b64"])
    ciphertext = decode_b64(inbound["ciphertext_b64"])
    plaintext = decrypt_payload(session_key, nonce, ciphertext)
    payload_digest = sha256_hex(plaintext)
    if payload_digest != inbound["sha256"]:
        raise ValueError("SHA-256 digest mismatch detected")

    payload = json.loads(plaintext.decode("utf-8"))
    logger.info(
        "Protected payload received",
        extra={
            "event": "message_received",
            "details": {
                "client_common_name": client_name,
                "message_id": payload["message_id"],
                "payload_sha256": payload_digest,
                "telemetry_summary": {
                    "ecu_id": payload["telemetry"]["ecu_id"],
                    "speed_kph": payload["telemetry"]["vehicle_speed_kph"],
                },
            },
        },
    )

    response = {
        "message_id": payload["message_id"],
        "status": "accepted",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "integrity_verified": True,
    }
    response_bytes = json.dumps(response, sort_keys=True).encode("utf-8")
    response_nonce, response_ciphertext = encrypt_payload(session_key, response_bytes)
    send_json(
        tls_socket,
        {
            "message_type": "secure_response",
            "nonce_b64": encode_b64(response_nonce),
            "ciphertext_b64": encode_b64(response_ciphertext),
            "sha256": sha256_hex(response_bytes),
        },
    )
    logger.info(
        "Protected response sent",
        extra={"event": "message_sent", "details": {"client_common_name": client_name, "message_id": payload["message_id"]}},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Secure TLS server with application-level AES protection")
    parser.add_argument("--host", default=SERVER_HOST)
    parser.add_argument("--port", type=int, default=SERVER_PORT)
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
