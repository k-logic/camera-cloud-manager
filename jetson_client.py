"""Jetson用 MQTTクライアント

クラウドからの設定・コマンドをMQTTで受信し、
既存の camera-api (localhost:8000) のHTTPエンドポイントを呼んで配信を制御する。
vr180-live-encoder のコードは一切変更しない。

前提:
    - camera-api が localhost:8000 で起動済み
    - paho-mqtt が必要: pip install paho-mqtt

Usage:
    python jetson_client.py --camera-key <KEY> --broker <CLOUD_IP>

Example:
    python jetson_client.py --camera-key ZHUWypadNaWhO4V-ymnqsg --broker 192.168.0.121
"""
import argparse
import json
import os
import time
import urllib.request
import urllib.error

import paho.mqtt.client as mqtt

CAMERA_API = "http://localhost:8000"


def call_api(method, path, data=None):
    """camera-api にHTTPリクエストを送る"""
    url = f"{CAMERA_API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    if body:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode() if e.fp else str(e)
        print(f"[Jetson] API error {e.code}: {detail}")
        return None
    except Exception as e:
        print(f"[Jetson] API connection error: {e}")
        return None


def start_stream(settings):
    """camera-api の POST /stream/start を呼ぶ"""
    stream_url = settings.get("stream_url", "")
    if not stream_url:
        print("[Jetson] No stream_url configured, cannot start")
        return False

    camera_source = settings.get("camera_source", "mipi")
    width = settings.get("width", 1920)
    height = settings.get("height", 1080)
    output_width = settings.get("output_width", width)
    output_height = settings.get("output_height", height)
    fps = settings.get("fps", 30)
    bitrate = settings.get("bitrate", 4000)

    # camera-api の StartRequest に合わせたペイロード
    payload = {
        "camera_source": camera_source,
        "width": width,
        "height": height,
        "output_width": output_width,
        "output_height": output_height,
        "fps": fps,
        "bitrate": bitrate,
        "audio_bitrate": "128k",
        "audio_sample_rate": 44100,
        "audio_channels": 1,
        "image_overlay_1": {"enabled": False, "width": 400, "height": 100, "offset_x": 0, "offset_y": 0},
        "image_overlay_2": {"enabled": False, "width": 400, "height": 100, "offset_x": 0, "offset_y": 0},
        "image_overlay_3": {"enabled": False, "width": 400, "height": 100, "offset_x": 0, "offset_y": 0},
        "text_overlay_1": {"enabled": False, "text": "", "font_family": "Sans", "size": 24, "color": "#FFFFFF", "alignment": "center", "offset_x": 0, "offset_y": 0},
        "text_overlay_2": {"enabled": False, "text": "", "font_family": "Sans", "size": 24, "color": "#FFFFFF", "alignment": "center", "offset_x": 0, "offset_y": 0},
        "text_overlay_3": {"enabled": False, "text": "", "font_family": "Sans", "size": 24, "color": "#FFFFFF", "alignment": "center", "offset_x": 0, "offset_y": 0},
        "stream_url": stream_url,
        "show_fps": False,
    }

    print(f"[Jetson] Starting stream → {stream_url}")
    result = call_api("POST", "/stream/start", payload)
    if result:
        print(f"[Jetson] Stream started: {result}")
        return True
    return False


def stop_stream():
    """camera-api の POST /stream/stop を呼ぶ"""
    print("[Jetson] Stopping stream...")
    result = call_api("POST", "/stream/stop")
    if result:
        print(f"[Jetson] Stream stopped: {result}")
        return True
    return False


def get_stream_status():
    """camera-api の GET /stream/status を呼ぶ"""
    return call_api("GET", "/stream/status")


def get_system_status():
    """camera-api の GET /system/status を呼ぶ"""
    return call_api("GET", "/system/status")


def build_cloud_status(settings_version, stream_st, system_st):
    """camera-api のレスポンスをクラウド向けフォーマットに変換"""
    # stream status 変換
    stream_status = {"running": False}
    if stream_st:
        config = stream_st.get("config") or {}
        stats = stream_st.get("stats") or {}
        stream_status = {
            "running": stream_st.get("running", False),
            "width": config.get("width"),
            "height": config.get("height"),
            "fps": stats.get("fps"),
            "bitrate": stats.get("bitrate_kbps"),
            "stream_quality": stats.get("status"),
        }

    # system status 変換
    sys_status = {}
    if system_st:
        mem = system_st.get("memory") or {}
        disk = system_st.get("disk") or {}
        sys_status = {
            "cpu_usage": system_st.get("cpu"),
            "gpu_usage": system_st.get("gpu"),
            "mem_used": mem.get("used_mb"),
            "mem_total": mem.get("total_mb"),
            "temperature": system_st.get("temperature"),
            "disk_used": disk.get("used_gb"),
            "disk_total": disk.get("total_gb"),
            "uptime": system_st.get("uptime"),
        }

    return {
        "settings_version": settings_version,
        "stream_status": stream_status,
        "system_status": sys_status,
    }


def main():
    global CAMERA_API

    parser = argparse.ArgumentParser(description="Jetson MQTT camera client")
    parser.add_argument("--camera-key", required=True)
    parser.add_argument("--broker", required=True, help="MQTT broker IP")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--ws-path", default="/mqtt", help="WebSocket path")
    parser.add_argument("--api-url", default=CAMERA_API, help="camera-api URL")
    args = parser.parse_args()

    CAMERA_API = args.api_url

    camera_key = args.camera_key
    topic_status = f"cameras/{camera_key}/status"
    topic_settings = f"cameras/{camera_key}/settings"
    topic_command = f"cameras/{camera_key}/command"

    settings_version = 0
    current_settings = {}

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"[Jetson] Connected to broker: {reason_code}")
        client.subscribe(topic_settings)
        client.subscribe(topic_command)

    def on_message(client, userdata, msg):
        nonlocal settings_version, current_settings

        if msg.topic == topic_settings:
            data = json.loads(msg.payload.decode())
            new_version = data.get("settings_version", 0)
            if new_version <= settings_version:
                return
            settings_version = new_version
            current_settings = data
            new_stream = data.get("stream_running", False)

            # camera-api から現在の実際の状態を取得
            stream_st = get_stream_status()
            actually_running = stream_st.get("running", False) if stream_st else False

            if new_stream and not actually_running:
                start_stream(data)
            elif not new_stream and actually_running:
                stop_stream()
            else:
                print(f"[Jetson] Settings updated (v{settings_version})")

            # 即座にステータス送信
            send_status(client)

        elif msg.topic == topic_command:
            data = json.loads(msg.payload.decode())
            cmd = data.get("command")
            print(f"[Jetson] Command: {cmd}")
            if cmd == "reboot":
                stop_stream()
                print("[Jetson] Rebooting...")
                os.system("sudo reboot")

    def send_status(client):
        stream_st = get_stream_status()
        system_st = get_system_status()
        payload = json.dumps(build_cloud_status(settings_version, stream_st, system_st))
        client.publish(topic_status, payload)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
    client.ws_set_options(path=args.ws_path)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"[Jetson] Camera Key: {camera_key}")
    print(f"[Jetson] Broker: ws://{args.broker}:{args.port}{args.ws_path}")
    print(f"[Jetson] Camera API: {CAMERA_API}")

    client.connect(args.broker, args.port)
    client.loop_start()

    try:
        while True:
            send_status(client)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n[Jetson] Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
