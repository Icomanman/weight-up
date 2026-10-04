import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from .auth import AuthMixin, APP_MI_FITNESS

SUPPORTED_REGIONS = {"de", "i2", "ru", "sg", "us"}


@dataclass
class XiaomiWeight:
    date: datetime | None = None
    weight: float = 0.0
    bmi: float = 0.0
    body_fat: float = 0.0
    body_water: float = 0.0
    bone_mass: float = 0.0
    metabolic_age: int = 0
    muscle_mass: float = 0.0
    physique_rating: int = 0
    protein_mass: float = 0.0
    visceral_fat: int = 0
    basal_metabolism: int = 0
    body_score: int = 0
    heart_rate: int = 0
    height: float = 0.0
    skeletal_muscle_mass: float = 0.0
    user: str = ""
    source: str = ""


def mifitness_url(region: str = "") -> str:
    if region in ("", "cn"):
        return "https://hlth.io.mi.com"
    if region in SUPPORTED_REGIONS:
        return f"https://{region}.hlth.io.mi.com"
    return ""


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":")).encode()


def _float(value: Any) -> float:
    if isinstance(value, bool) or value is None:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    if isinstance(value, bool) or value is None:
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError, OverflowError):
        return 0


def _timestamp(seconds: Any) -> datetime:
    return datetime.fromtimestamp(_int(seconds), tz=timezone.utc)


def _timestamp_millis(milliseconds: Any) -> datetime:
    return datetime.fromtimestamp(_int(milliseconds) / 1000, tz=timezone.utc)


def _read_proxy_response(data: bytes) -> bytes:
    proxy_response = json.loads(data)
    return _json_bytes(json.loads(proxy_response["resp"]).get("result"))


def _weight_from_fitness(item: dict[str, Any]) -> XiaomiWeight:
    value = json.loads(item["value"])
    return XiaomiWeight(
        date=_timestamp(value.get("time")),
        weight=_float(value.get("weight")),
        bmi=_float(value.get("bmi")),
        body_fat=_float(value.get("body_fat_rate")),
        body_water=_float(value.get("moisture_rate")),
        bone_mass=_float(value.get("bone_mass")),
        metabolic_age=_int(value.get("body_age")),
        muscle_mass=_float(value.get("muscle_mass")),
        protein_mass=_float(value.get("protein_mass")),
        visceral_fat=_int(value.get("visceral_fat")),
        basal_metabolism=_int(value.get("basal_metabolism")),
        body_score=_int(value.get("body_score")),
        heart_rate=_int(value.get("bpm")),
        skeletal_muscle_mass=_float(value.get("skeletal_muscle_mass")),
        source=str(item.get("sid", "")),
    )


def _weight_from_scale_item(item: dict[str, Any]) -> XiaomiWeight | None:
    source_type = _int(item.get("fromSource"))
    if source_type not in (1, 2, 3):
        return None
    value = json.loads(item["data"])

    if source_type in (1, 2):
        user = value.get("user") or {}

        def number(key: str) -> float:
            return _float(value.get(key))

        def integer(key: str) -> int:
            return _int(value.get(key))

        height = _float(user.get("height"))

        return XiaomiWeight(
            date=_timestamp_millis(item.get("createTime")),
            weight=number("weight"),
            bmi=number("bmi"),
            body_fat=number("bfp"),
            body_water=number("bwp"),
            bone_mass=number("bmc"),
            metabolic_age=integer("ma"),
            muscle_mass=number("slm"),
            physique_rating=integer("bt"),
            protein_mass=number("pm"),
            visceral_fat=integer("vfl"),
            basal_metabolism=integer("bmr"),
            body_score=integer("sbc"),
            heart_rate=integer("heartRate"),
            height=height,
            skeletal_muscle_mass=number("smm"),
            user=str(user.get("name", "")),
            source=(
                str(value.get("reportFrom", ""))
                if source_type == 1
                else str(user.get("deviceId", ""))
            ),
        )

    user = value.get("user") or {}
    weight = XiaomiWeight(
        date=_timestamp_millis(value.get("time")),
        weight=_float(value.get("weight")),
        bmi=_float(value.get("bmi")),
        heart_rate=_int(value.get("heartRate")),
        user=str(user.get("name", "")),
        source=str(item.get("did", "")),
    )
    body_res_data = value.get("bodyResData", "")
    if body_res_data:
        details = json.loads(body_res_data)
        weight.body_fat = _float(details.get("bfp"))
        weight.body_water = _float(details.get("bwp"))
        weight.bone_mass = _float(details.get("bmc"))
        weight.metabolic_age = _int(details.get("ma"))
        weight.muscle_mass = _float(details.get("slm"))
        weight.protein_mass = _float(details.get("pm"))
        weight.visceral_fat = _int(details.get("vfl"))
        weight.basal_metabolism = _int(details.get("bmr"))
        weight.body_score = _int(details.get("sbc"))
        weight.skeletal_muscle_mass = _float(details.get("smm"))
    return weight


def _unmarshal_scale_data(data: bytes) -> tuple[list[XiaomiWeight], int]:
    items = json.loads(data) or []
    weights = [
        weight
        for item in items
        if (weight := _weight_from_scale_item(item)) is not None
    ]
    next_timestamp = _int(items[19].get(
        "createTime")) if len(items) >= 20 else 0
    return weights, next_timestamp


class Client(AuthMixin):
    def __init__(self, app: str = APP_MI_FITNESS, timeout: float = 60.0) -> None:
        self.session = requests.Session()
        self.timeout = timeout
        self.sid = app
        self.cookies = ""
        self.user_id = 0
        self.ssecurity = b""
        self.pass_token = ""

    def close(self) -> None:
        self.session.close()

    def get_all_weights(self) -> list[XiaomiWeight]:
        return self._get_all_weights("")

    def _get_all_weights(self, region: str) -> list[XiaomiWeight]:
        timestamp = int(time.time()) + 24 * 60 * 60
        params: dict[str, Any] = {
            "start_time": 1,
            "end_time": timestamp,
            "key": "weight",
        }
        weights: list[XiaomiWeight] = []

        while True:
            data = self.request(
                mifitness_url(region),
                "/app/v1/data/get_fitness_data_by_time",
                json.dumps(params, separators=(",", ":")),
            )
            response = json.loads(data)
            for item in response.get("data_list", []):
                if item.get("key") == "weight":
                    weights.append(_weight_from_fitness(item))
            if not response.get("has_more"):
                return weights
            params["next_key"] = response.get("next_key", "")

    def get_filter_weights(self, filter: str) -> list[XiaomiWeight]:
        if mifitness_url(filter):
            return self._get_all_weights(filter)

        weights: list[XiaomiWeight] = []
        timestamp = int(time.time() * 1000)
        while timestamp > 0:
            query = {
                "param": {"endTime": 1, "beginTime": timestamp},
                "model": filter,
                "uid": self.user_id,
                "did": 0,
            }
            params = _json_bytes(
                {
                    "eco_api": "eco/scale/getData",
                    "params": json.dumps(query, separators=(",", ":")),
                }
            ).decode()
            data = self.request(
                mifitness_url(), "/app/v1/eco/api_proxy", params
            )
            batch, timestamp = _unmarshal_scale_data(
                _read_proxy_response(data))
            weights.extend(batch)
        return weights

    def get_model_weights(self, region: str, model: str) -> list[XiaomiWeight]:
        if region not in ("", "cn", *SUPPORTED_REGIONS):
            raise ValueError(f"xiaomi: unsupported region: {region}")

        weights: list[XiaomiWeight] = []
        timestamp = int(time.time() * 1000)
        while timestamp > 0:
            if region in ("", "cn"):
                query = {
                    "param": {"endTime": 1, "beginTime": timestamp},
                    "model": model,
                    "uid": self.user_id,
                    "did": 0,
                }
                base_url = "https://api.io.mi.com/app"
                api_url = "/eco/scale/getData"
            else:
                query = {
                    "endTime": 1,
                    "beginTime": timestamp,
                    "model": model,
                    "uid": str(self.user_id),
                    "did": 0,
                    "accountId": 0,
                }
                base_url = f"https://{region}.api.io.mi.com/app"
                api_url = "/eco/common/scale/getUserDataByPage"

            data = self.request(
                base_url,
                api_url,
                json.dumps(query, separators=(",", ":")),
                {"MIOT-REQUEST-MODEL": model},
            )
            batch, timestamp = _unmarshal_scale_data(data)
            weights.extend(batch)
        return weights
