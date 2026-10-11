import base64
import hashlib
import os

import pytest

from weight_up.xiaomi import signing

SSECURITY = base64.b64encode(bytes(range(16))).decode()
RANDOM_BYTES = bytes(range(100, 108))
UNIX_SECONDS = 1_700_000_000
DATA = '{"endTime":1,"beginTime":5,"model":"m","uid":"7","did":0,"accountId":0}'
PATH = "/app/eco/common/scale/getUserDataByPage"


def test_nonce_is_random_bytes_then_big_endian_minutes():
    nonce = base64.b64decode(signing.build_nonce(RANDOM_BYTES, UNIX_SECONDS))

    assert nonce[:8] == RANDOM_BYTES
    assert int.from_bytes(nonce[8:], "big") == UNIX_SECONDS // 60


def test_nonce_rejects_wrong_random_length():
    with pytest.raises(ValueError):
        signing.build_nonce(b"short", UNIX_SECONDS)


def test_signed_nonce_is_sha256_of_key_then_nonce():
    nonce = signing.build_nonce(RANDOM_BYTES, UNIX_SECONDS)
    expected = hashlib.sha256(
        base64.b64decode(SSECURITY) + base64.b64decode(nonce)).digest()

    assert base64.b64decode(
        signing.derive_signed_nonce(SSECURITY, nonce)) == expected


def test_rc4_is_symmetric_and_discards_keystream_prefix():
    signed_nonce = signing.derive_signed_nonce(
        SSECURITY, signing.build_nonce(RANDOM_BYTES, UNIX_SECONDS))

    ciphertext = signing.rc4_crypt(signed_nonce, b"hello")

    assert signing.rc4_crypt(signed_nonce, ciphertext) == b"hello"
    # A plain RC4 without the 1024-byte discard would give different bytes.
    from Crypto.Cipher import ARC4
    plain_rc4 = ARC4.new(base64.b64decode(signed_nonce)).encrypt(b"hello")
    assert ciphertext != plain_rc4


def test_params_match_an_independent_implementation_of_the_csharp_client():
    """The C# GenSignature64 builds the string by hand; rebuild it the same way."""
    nonce = signing.build_nonce(RANDOM_BYTES, UNIX_SECONDS)
    signed_nonce = signing.derive_signed_nonce(SSECURITY, nonce)
    signed_path = "/eco/common/scale/getUserDataByPage"

    def csharp_signature(values: dict[str, str]) -> str:
        text = f"POST&{signed_path}&data={values['data']}"
        if values.get("rc4_hash__"):
            text += f"&rc4_hash__={values['rc4_hash__']}"
        text += "&" + signed_nonce
        return base64.b64encode(hashlib.sha1(text.encode()).digest()).decode()

    values = {"data": DATA}
    values["rc4_hash__"] = csharp_signature(values)
    for key in list(values):
        values[key] = base64.b64encode(
            signing.rc4_crypt(signed_nonce, values[key].encode())).decode()
    values["signature"] = csharp_signature(values)
    values["_nonce"] = nonce

    assert signing.build_encrypted_params(
        PATH, SSECURITY, nonce, {"data": DATA}) == values


def test_ssecurity_is_never_part_of_the_request_fields():
    nonce = signing.build_nonce(os.urandom(8), UNIX_SECONDS)

    fields = signing.build_encrypted_params(PATH, SSECURITY, nonce, {"data": DATA})

    assert set(fields) == {"data", "rc4_hash__", "signature", "_nonce"}


def test_decrypt_response_round_trips_and_rejects_the_wrong_key():
    nonce = signing.build_nonce(RANDOM_BYTES, UNIX_SECONDS)
    signed_nonce = signing.derive_signed_nonce(SSECURITY, nonce)
    body = base64.b64encode(
        signing.rc4_crypt(signed_nonce, b'{"code":0}')).decode()
    other_key = base64.b64encode(bytes(range(16, 32))).decode()

    assert signing.decrypt_response(SSECURITY, nonce, body) == {"code": 0}
    with pytest.raises(ValueError):
        signing.decrypt_response(other_key, nonce, body)
