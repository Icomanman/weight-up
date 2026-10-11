"""Pure request signing and RC4 encryption for Xiaomi's signed cloud API.

Nothing here performs I/O. Keys and nonces are base64 strings, matching how
Xiaomi transmits them.
"""

import base64
import hashlib
import json
from typing import Any

from Crypto.Cipher import ARC4

NONCE_RANDOM_BYTES = 8
RC4_DISCARDED_KEYSTREAM_BYTES = 1024


def build_nonce(random_bytes: bytes, unix_seconds: float) -> str:
    """Return a base64 nonce: 8 random bytes plus big-endian minutes since epoch.

    The caller supplies the randomness and the clock so the result is
    reproducible in tests.
    """
    if len(random_bytes) != NONCE_RANDOM_BYTES:
        raise ValueError(f"nonce needs {NONCE_RANDOM_BYTES} random bytes")
    minutes = int(unix_seconds // 60)
    return base64.b64encode(random_bytes + minutes.to_bytes(4, "big")).decode()


def derive_signed_nonce(ssecurity: str, nonce: str) -> str:
    """Return base64(sha256(ssecurity + nonce)), the per-request key."""
    digest = hashlib.sha256(
        base64.b64decode(ssecurity) + base64.b64decode(nonce)).digest()
    return base64.b64encode(digest).decode()


def rc4_crypt(signed_nonce: str, payload: bytes) -> bytes:
    """Encrypt or decrypt payload; RC4 is symmetric."""
    cipher = ARC4.new(base64.b64decode(signed_nonce))
    # Xiaomi discards the first 1024 bytes of the keystream.
    cipher.encrypt(bytes(RC4_DISCARDED_KEYSTREAM_BYTES))
    return cipher.encrypt(payload)


def encrypted_signature(
    method: str, path: str, signed_nonce: str, params: dict[str, str]
) -> str:
    """Return the base64 SHA-1 signature over method, path and parameters.

    The signed path never carries the /app prefix, although the URL does.
    """
    parts = [method.upper(), path.replace("/app/", "/")]
    parts += [f"{key}={value}" for key, value in params.items()]
    parts.append(signed_nonce)
    return base64.b64encode(
        hashlib.sha1("&".join(parts).encode()).digest()).decode()


def build_encrypted_params(
    path: str, ssecurity: str, nonce: str, params: dict[str, str]
) -> dict[str, str]:
    """Return the form fields for a signed POST: encrypted params, signature, nonce.

    ssecurity is used to derive the key only; it is never sent.
    """
    signed_nonce = derive_signed_nonce(ssecurity, nonce)
    plain_params = dict(params)
    plain_params["rc4_hash__"] = encrypted_signature(
        "POST", path, signed_nonce, plain_params)
    encrypted = {
        key: base64.b64encode(
            rc4_crypt(signed_nonce, value.encode())).decode()
        for key, value in plain_params.items()
    }
    encrypted["signature"] = encrypted_signature(
        "POST", path, signed_nonce, encrypted)
    encrypted["_nonce"] = nonce
    return encrypted


def decrypt_response(ssecurity: str, nonce: str, response_text: str) -> Any:
    """Decrypt a base64 RC4 response body and parse it as JSON.

    Raises ValueError if the body is not valid base64, or does not decrypt to
    JSON (typically because ssecurity is wrong).
    """
    signed_nonce = derive_signed_nonce(ssecurity, nonce)
    plaintext = rc4_crypt(signed_nonce, base64.b64decode(response_text))
    return json.loads(plaintext)
