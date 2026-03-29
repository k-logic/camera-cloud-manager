"""Redisサービス - カメラステータスの保存/取得（全てRedisで管理）"""
import logging
from datetime import datetime, timezone

import redis

from app.config import REDIS_URL

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None

STATUS_TTL = 30  # 秒（ポーリング間隔2秒に対して十分な余裕。TTL切れ=オフライン）
KEY_PREFIX = "camera_status:"


def get_client() -> redis.Redis | None:
    return _client


def save_status(camera_id: int, data: dict):
    """カメラステータスをRedisハッシュに保存（全項目）"""
    if not _client:
        logger.warning("Redis client not available, skipping save_status")
        return
    key = f"{KEY_PREFIX}{camera_id}"
    # is_online/last_seenを自動付与
    data["is_online"] = "True"
    data["last_seen"] = datetime.now(timezone.utc).isoformat()
    # 値をstrに変換（Redisハッシュはstr/bytes）
    str_data = {k: str(v) if v is not None else "" for k, v in data.items()}
    _client.hset(key, mapping=str_data)
    _client.expire(key, STATUS_TTL)


def get_status(camera_id: int) -> dict | None:
    """カメラステータスをRedisから取得。キーなし=オフライン。"""
    if not _client:
        return None
    key = f"{KEY_PREFIX}{camera_id}"
    data = _client.hgetall(key)
    if not data:
        return None
    # bytes → str → 型変換
    result = {}
    for k, v in data.items():
        key_str = k.decode() if isinstance(k, bytes) else k
        val_str = v.decode() if isinstance(v, bytes) else v
        result[key_str] = _convert_value(key_str, val_str)
    return result


def _convert_value(key: str, value: str):
    """Redisの文字列値を適切な型に変換"""
    if value == "" or value == "None":
        return None

    bool_fields = {"is_online", "stream_running"}
    float_fields = {"stream_fps", "cpu_usage", "gpu_usage", "temperature", "disk_used", "disk_total"}
    int_fields = {"stream_bitrate", "mem_used", "mem_total", "uptime"}

    if key in bool_fields:
        return value == "True"
    if key == "last_seen":
        return value  # ISO文字列のまま返す
    if key in float_fields:
        try:
            return float(value)
        except ValueError:
            return None
    if key in int_fields:
        try:
            return int(float(value))
        except ValueError:
            return None
    return value


def start():
    """Redis接続開始"""
    global _client
    _client = redis.from_url(REDIS_URL, decode_responses=False)
    _client.ping()
    logger.info(f"Redis connected ({REDIS_URL})")


def stop():
    """Redis接続終了"""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("Redis disconnected")
