"""MQTTサービス - カメラ↔クラウド通信"""
import json
import logging

import paho.mqtt.client as mqtt

from app.database import SessionLocal
from app.models.camera import Camera
from app.config import MQTT_BROKER, MQTT_PORT
from app.services import redis_service

logger = logging.getLogger(__name__)

# グローバルMQTTクライアント
_client: mqtt.Client | None = None


def get_client() -> mqtt.Client | None:
    return _client


def _on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"MQTT connected: {reason_code}")
    # 全カメラのstatusトピックをSubscribe
    client.subscribe("cameras/+/status")
    logger.info("Subscribed to cameras/+/status")


def _on_message(client, userdata, msg):
    """カメラからのステータス受信 → Redis保存"""
    try:
        parts = msg.topic.split("/")
        if len(parts) != 3 or parts[2] != "status":
            return

        camera_key = parts[1]
        data = json.loads(msg.payload.decode())

        db = SessionLocal()
        try:
            camera = db.query(Camera).filter(Camera.camera_key == camera_key).first()
            if not camera:
                logger.warning(f"Unknown camera key: {camera_key}")
                return
            if not camera.is_active:
                return

            # 全ステータス → Redis
            ss = data.get("stream_status", {})
            sys_s = data.get("system_status", {})
            redis_service.save_status(camera.id, {
                "stream_running": ss.get("running", False),
                "stream_fps": ss.get("fps"),
                "stream_bitrate": ss.get("bitrate"),
                "stream_quality": ss.get("stream_quality"),
                "cpu_usage": sys_s.get("cpu_usage"),
                "gpu_usage": sys_s.get("gpu_usage"),
                "mem_used": sys_s.get("mem_used"),
                "mem_total": sys_s.get("mem_total"),
                "temperature": sys_s.get("temperature"),
                "disk_used": sys_s.get("disk_used"),
                "disk_total": sys_s.get("disk_total"),
                "uptime": sys_s.get("uptime"),
            })

            # settings_version比較（DBからsettingsを読むだけ、書き込みなし）
            settings_version = data.get("settings_version", 0)
            if camera.settings and settings_version < camera.settings.settings_version:
                publish_settings(camera_key, camera.settings)
        finally:
            db.close()

    except Exception as e:
        logger.error(f"MQTT message error: {e}")


def publish_settings(camera_key: str, settings):
    """設定をRetained Messageとして配信"""
    if not _client:
        logger.warning("MQTT client not available, skipping publish_settings")
        return
    payload = json.dumps({
        "camera_source": settings.camera_source,
        "width": settings.width,
        "height": settings.height,
        "output_width": settings.output_width,
        "output_height": settings.output_height,
        "fps": settings.fps,
        "bitrate": settings.bitrate,
        "stream_url": settings.stream_url,
        "stream_running": settings.stream_running,
        "settings_version": settings.settings_version,
    })
    _client.publish(f"cameras/{camera_key}/settings", payload, retain=True)
    logger.info(f"Published settings to cameras/{camera_key}/settings")


def clear_retained(camera_key: str):
    """Retained Messageをクリア（カメラ削除時）"""
    if not _client:
        return
    _client.publish(f"cameras/{camera_key}/settings", "", retain=True)
    logger.info(f"Cleared retained message for cameras/{camera_key}/settings")


def publish_command(camera_key: str, command: str):
    """コマンドを配信（非Retained）"""
    if not _client:
        logger.warning("MQTT client not available, skipping publish_command")
        return
    payload = json.dumps({"command": command})
    _client.publish(f"cameras/{camera_key}/command", payload, retain=False)
    logger.info(f"Published command '{command}' to cameras/{camera_key}/command")


def start():
    """MQTTクライアントを起動"""
    global _client
    _client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    _client.on_connect = _on_connect
    _client.on_message = _on_message
    _client.connect(MQTT_BROKER, MQTT_PORT)
    _client.loop_start()
    logger.info(f"MQTT client started ({MQTT_BROKER}:{MQTT_PORT})")


def stop():
    """MQTTクライアントを停止"""
    global _client
    if _client:
        _client.loop_stop()
        _client.disconnect()
        _client = None
        logger.info("MQTT client stopped")
