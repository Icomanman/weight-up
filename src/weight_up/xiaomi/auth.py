import base64
import hashlib
import json
import secrets
import string
import time
from collections.abc import Mapping
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from Crypto.Cipher import ARC4

APP_XIAOMI_HOME = "xiaomiio"
APP_MI_FITNESS = "miothealth"
LOGIN_PREFIX = b"&&&START&&&"


def gen_nonce() -> bytes:
    return secrets.token_bytes(8) + (int(time.time()) // 60).to_bytes(4, "big")


def gen_signed_nonce(ssecurity: bytes, nonce: bytes) -> bytes:
    return hashlib.sha256(ssecurity + nonce).digest()


def crypt(key: bytes, plaintext: bytes) -> bytes:
    cipher = ARC4.new(key)
    cipher.encrypt(bytes(1024))
    return cipher.encrypt(plaintext)


def gen_signature64(
    method: str, path: str, values: Mapping[str, str], signed_nonce: bytes
) -> str:
    signature_text = f"{method}&{path}&data={values.get('data', '')}"
    if "rc4_hash__" in values:
        signature_text += f"&rc4_hash__={values['rc4_hash__']}"
    signature_text += "&" + base64.b64encode(signed_nonce).decode("ascii")
    return base64.b64encode(hashlib.sha1(signature_text.encode()).digest()).decode(
        "ascii"
    )


def _read_login_response(response: requests.Response) -> dict[str, object]:
    response.raise_for_status()
    body = response.content
    if not body.startswith(LOGIN_PREFIX):
        raise ValueError("xiaomi: wrong loginPrefix")
    return json.loads(body[len(LOGIN_PREFIX):])


def _login_location(result: Mapping[str, object]) -> str:
    location = result.get("location")
    if isinstance(location, str):
        parsed_location = urlparse(location)
        if parsed_location.scheme in ("http", "https") and parsed_location.netloc:
            return location

    reasons = []
    if result.get("captchaUrl"):
        reasons.append("captcha verification is required")
    if result.get("notificationUrl"):
        reasons.append("additional account verification is required")
    if not reasons:
        reasons.append(
            f"no valid redirect location was returned (response code={result.get('code', 'unknown')})"
        )
    raise RuntimeError("xiaomi: login did not complete: " + "; ".join(reasons))


class AuthMixin:
    sid: str
    cookies: str
    pass_token: str
    ssecurity: bytes
    user_id: int
    session: requests.Session
    timeout: float

    def login(self, username: str, password: str) -> None:
        response1 = self._service_login()
        response2 = self._service_login2(response1, username, password)
        self._service_login3(_login_location(response2))

    def _service_login(self) -> dict[str, object]:
        response = self.session.get(
            "https://account.xiaomi.com/pass/serviceLogin",
            params={"_json": "true", "sid": self.sid},
            timeout=self.timeout,
        )
        return _read_login_response(response)

    def _service_login2(
        self, response1: Mapping[str, object], username: str, password: str
    ) -> dict[str, object]:
        password_hash = hashlib.md5(password.encode()).hexdigest().upper()
        response = self.session.post(
            "https://account.xiaomi.com/pass/serviceLoginAuth2",
            data={
                "_json": "true",
                "hash": password_hash,
                "sid": str(response1.get("sid", "")),
                "callback": str(response1.get("callback", "")),
                "_sign": str(response1.get("_sign", "")),
                "qs": str(response1.get("qs", "")),
                "user": username,
            },
            headers={
                "Cookie": "deviceId="
                + "".join(
                    secrets.choice(string.ascii_letters + string.digits)
                    for _ in range(16)
                ),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=self.timeout,
        )
        result = _read_login_response(response)
        self.pass_token = str(result.get("passToken", ""))
        self.ssecurity = base64.b64decode(str(result.get("ssecurity", "")))
        self.user_id = int(result.get("userId", 0))
        return result

    def _service_login3(self, location: str) -> None:
        response = self.session.get(location, timeout=self.timeout)
        response.raise_for_status()
        new_cookies = "; ".join(
            f"{name}={value}" for name, value in response.cookies.items()
        )
        if new_cookies:
            self.cookies = "; ".join(value for value in (
                self.cookies, new_cookies) if value)

    def oauth2(self, params: str, username: str, password: str) -> str:
        response1 = self._oauth2_authorize(params)
        response2 = self._service_login2(response1, username, password)

        oauth_session = requests.Session()
        try:
            redirect_url = _login_location(response2)
            location = ""
            for _ in range(2):
                response = oauth_session.get(
                    redirect_url,
                    timeout=self.timeout,
                    allow_redirects=False,
                )
                location = response.headers.get("Location", "")
                if not location:
                    response.raise_for_status()
                    raise ValueError(
                        "xiaomi: OAuth redirect did not include a Location"
                    )
                code = parse_qs(urlparse(location).query).get("code", [""])[0]
                if code:
                    return code
                redirect_url = urljoin(response.url, location)
            return parse_qs(urlparse(location).query).get("code", [""])[0]
        finally:
            oauth_session.close()

    def _oauth2_authorize(self, params: str) -> dict[str, object]:
        response = self.session.get(
            "https://account.xiaomi.com/oauth2/authorize?" + params,
            timeout=self.timeout,
        )
        result = _read_login_response(response)
        oauth_url = result.get("data", {}).get("oauthLoginUrl", "")
        response = self.session.get(str(oauth_url), timeout=self.timeout)
        return _read_login_response(response)

    def request(
        self,
        base_url: str,
        api_url: str,
        params: str,
        headers: Mapping[str, str] | None = None,
    ) -> bytes:
        nonce = gen_nonce()
        signed_nonce = gen_signed_nonce(self.ssecurity, nonce)
        form = {"data": params}
        form["rc4_hash__"] = gen_signature64(
            "POST", api_url, form, signed_nonce)

        for key, value in tuple(form.items()):
            encrypted = crypt(signed_nonce, value.encode())
            form[key] = base64.b64encode(encrypted).decode("ascii")

        form["signature"] = gen_signature64(
            "POST", api_url, form, signed_nonce)
        form["_nonce"] = base64.b64encode(nonce).decode("ascii")

        response = self.session.post(
            base_url + api_url,
            data=form,
            headers={
                "Cookie": self.cookies,
                "Content-Type": "application/x-www-form-urlencoded",
                **(headers or {}),
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        ciphertext = base64.b64decode(response.content)
        decoded = json.loads(crypt(signed_nonce, ciphertext))
        if decoded.get("code", 0) != 0:
            raise RuntimeError("xiaomi: " + str(decoded.get("message", "")))
        return json.dumps(decoded.get("result")).encode()

    def login_with_token(self, token: str) -> None:
        user_id, separator, pass_token = token.partition(":")
        if not separator:
            pass_token = ""
        response = self.session.get(
            "https://account.xiaomi.com/pass/serviceLogin",
            params={"_json": "true", "sid": self.sid},
            headers={"Cookie": f"userId={user_id}; passToken={pass_token}"},
            timeout=self.timeout,
        )
        result = _read_login_response(response)
        self.pass_token = str(result.get("passToken", ""))
        self.ssecurity = base64.b64decode(str(result.get("ssecurity", "")))
        self.user_id = int(result.get("userId", 0))
        self._service_login3(_login_location(result))

    def token(self) -> str:
        return f"{self.user_id}:{self.pass_token}"
