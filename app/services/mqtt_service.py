"""MQTTサービス - カメラ↔クラウド通信"""
import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.camera import Camera, CameraStatus
from app.config import MQTT_BROKER, MQTT_PORT

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
    """カメラからのステータス受信 → DB更新"""
    try:
        parts = msg.topic.split("/")
        if len(parts) != 3 or parts[2] != "status":
            return

        camera_key = parts[1]
        data = json.loads(msg.payload.decode())

        db: Session = SessionLocal()
        try:
            camera = db.query(Camera).filter(Camera.camera_key == camera_key).first()
            if not camera:
                logger.warning(f"Unknown camera key: {camera_key}")
                return
            if not camera.is_active:
                return

            now = datetime.now(timezone.utc)

            # camera_status upsert
            status = camera.status
            if status is None:
                status = CameraStatus(camera_id=camera.id)
                db.add(status)

            status.is_online = True
            status.last_seen = now

            # stream_status
            ss = data.get("stream_status", {})
            status.stream_running = ss.get("running", False)
            status.stream_width = ss.get("width")
            status.stream_height = ss.get("height")
            status.stream_fps = ss.get("fps")
            status.stream_bitrate = ss.get("bitrate")
            status.stream_time = ss.get("stream_time")
            status.stream_quality = ss.get("stream_quality")

            # system_status
            sys_s = data.get("system_status", {})
            status.cpu_usage = sys_s.get("cpu_usage")
            status.gpu_usage = sys_s.get("gpu_usage")
            status.mem_used = sys_s.get("mem_used")
            status.mem_total = sys_s.get("mem_total")
            status.temperature = sys_s.get("temperature")
            status.disk_used = sys_s.get("disk_used")
            status.disk_total = sys_s.get("disk_total")
            status.uptime = sys_s.get("uptime")

            # pending_command があればMQTTで送信済みなのでクリア
            settings_version = data.get("settings_version", 0)
            if camera.settings and settings_version < camera.settings.settings_version:
                publish_settings(camera_key, camera.settings)

            db.commit()
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
