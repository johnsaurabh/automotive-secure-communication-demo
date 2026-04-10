from __future__ import annotations

import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from config import GCM_NONCE_SIZE


def generate_aes_key(length: int = 32) -> bytes:
    return os.urandom(length)


def encrypt_payload(key: bytes, plaintext: bytes, associated_data: bytes | None = None) -> tuple[bytes, bytes]:
    nonce = os.urandom(GCM_NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext


def decrypt_payload(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes | None = None) -> bytes:
    return AESGCM(key).decrypt(nonce, ciphertext, associated_data)
