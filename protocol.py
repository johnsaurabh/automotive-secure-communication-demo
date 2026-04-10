from __future__ import annotations

import base64
import json
import struct
from typing import Any, Dict


def encode_b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def decode_b64(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def send_json(sock, message: Dict[str, Any]) -> None:
    payload = json.dumps(message, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def recv_json(sock) -> Dict[str, Any]:
    header = _recv_exact(sock, 4)
    if not header:
        raise ConnectionError("Socket closed before length header was received")
    expected = struct.unpack("!I", header)[0]
    payload = _recv_exact(sock, expected)
    if not payload:
        raise ConnectionError("Socket closed before full payload was received")
    return json.loads(payload.decode("utf-8"))


def _recv_exact(sock, expected: int) -> bytes:
    data = bytearray()
    while len(data) < expected:
        chunk = sock.recv(expected - len(data))
        if not chunk:
            if not data:
                return b""
            raise ConnectionError("Socket closed during framed read")
        data.extend(chunk)
    return bytes(data)
