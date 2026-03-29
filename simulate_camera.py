"""カメラポーリング シミュレーター（MQTT版）

Jetsonカメラの動作をシミュレートし、MQTTでクラウドと通信する。
UIからのStart/Stop/Rebootコマンドに即座に反応する。

Usage:
    python simulate_camera.py --camera-key <KEY> [--broker localhost]
"""
import argparse
import json
import random
import ssl
import time

import paho.mqtt.client as mqtt


def main():
    parser = argparse.ArgumentParser(description="Camera MQTT simulator")
    parser.add_argument("--camera-key", required=True, help="Camera key for authentication")
    parser.add_argument("--broker", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=80, help="MQTT broker port")
    parser.add_argument("--ws-path", default="/mqtt", help="WebSocket path")
    parser.add_argument("--ssl", action="store_true", default=False, help="Use SSL")
    args = parser.parse_args()

    camera_key = args.camera_key
    topic_status = f"cameras/{camera_key}/status"
    topic_settings = f"cameras/{camera_key}/settings"
    topic_command = f"cameras/{camera_key}/command"

    stream_running = False
    settings_version = 0
    uptime = 0
    stream_start_time = None

    def on_connect(client, userdata, flags, reason_code, properties):
        print(f"[Simulator] Connected to MQTT broker: {reason_code}")
        client.subscribe(topic_settings)
        client.subscribe(topic_command)
        print(f"[Simulator] Subscribed to {topic_settings}")
        print(f"[Simulator] Subscribed to {topic_command}")

    def format_stream_time():
        """配信経過時間をH:MM:SS形式で返す"""
        if not stream_start_time:
            return None
        elapsed = int(time.time() - stream_start_time)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60
        return f"{h}:{m:02d}:{s:02d}"

    def send_status_now():
        """即座にステータスを送信"""
        nonlocal uptime
        cpu_usage = round(random.uniform(10, 40) + (30 if stream_running else 0), 1)
        gpu_usage = round(random.uniform(5, 20) + (50 if stream_running else 0), 1)
        temperature = round(random.uniform(35, 45) + (10 if stream_running else 0), 1)
        mem_used = random.randint(1500, 2500) + (1500 if stream_running else 0)
        payload = json.dumps({
            "settings_version": settings_version,
            "stream_status": {
                "running": stream_running,
                "width": 1920 if stream_running else None,
                "height": 1080 if stream_running else None,
                "fps": round(random.uniform(29.5, 30.0), 2) if stream_running else None,
                "bitrate": random.randint(3800, 4200) if stream_running else None,
                "stream_quality": "good" if stream_running else None,
                "stream_time": format_stream_time() if stream_running else None,
            },
            "system_status": {
                "cpu_usage": cpu_usage, "gpu_usage": gpu_usage,
                "mem_used": mem_used, "mem_total": 8192,
                "temperature": temperature, "disk_used": 12.5, "disk_total": 64.0,
                "uptime": uptime,
            },
        })
        client.publish(topic_status, payload)

    def on_message(client, userdata, msg):
        nonlocal stream_running, settings_version, uptime, stream_start_time

        if msg.topic == topic_settings:
            data = json.loads(msg.payload.decode())
            new_version = data.get("settings_version", 0)
            if new_version <= settings_version:
                return
            settings_version = new_version
            new_stream = data.get("stream_running", False)
            if new_stream != stream_running:
                stream_running = new_stream
                if stream_running:
                    stream_start_time = time.time()
                else:
                    stream_start_time = None
                action = "STARTED" if stream_running else "STOPPED"
                print(f"[Simulator] Stream {action} (v{settings_version})")
            else:
                print(f"[Simulator] Settings updated (v{settings_version})")
            send_status_now()

        elif msg.topic == topic_command:
            data = json.loads(msg.payload.decode())
            cmd = data.get("command")
            print(f"[Simulator] Command received: {cmd}")
            if cmd == "reboot":
                print(f"[Simulator] Rebooting...")
                stream_running = False
                uptime = 0
                time.sleep(3)
                print(f"[Simulator] Reboot complete")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, transport="websockets")
    client.ws_set_options(path=args.ws_path)
    if args.ssl:
        client.tls_set(cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS_CLIENT)
    client.on_connect = on_connect
    client.on_message = on_message

    proto = "wss" if args.ssl else "ws"
    print(f"[Simulator] Starting MQTT camera simulator (WebSocket)")
    print(f"[Simulator] Camera Key: {camera_key}")
    print(f"[Simulator] Broker: {proto}://{args.broker}:{args.port}{args.ws_path}")
    print(f"[Simulator] Press Ctrl+C to stop")
    print()

    client.connect(args.broker, args.port)
    client.loop_start()

    try:
        while True:
            # システムメトリクスをランダム生成
            cpu_usage = round(random.uniform(10, 40) + (30 if stream_running else 0), 1)
            gpu_usage = round(random.uniform(5, 20) + (50 if stream_running else 0), 1)
            temperature = round(random.uniform(35, 45) + (10 if stream_running else 0), 1)
            mem_used = random.randint(1500, 2500) + (1500 if stream_running else 0)

            payload = json.dumps({
                "settings_version": settings_version,
                "stream_status": {
                    "running": stream_running,
                    "width": 1920 if stream_running else None,
                    "height": 1080 if stream_running else None,
                    "fps": round(random.uniform(29.5, 30.0), 2) if stream_running else None,
                    "bitrate": random.randint(3800, 4200) if stream_running else None,
                    "stream_quality": "good" if stream_running else None,
                    "stream_time": format_stream_time() if stream_running else None,
                },
                "system_status": {
                    "cpu_usage": cpu_usage,
                    "gpu_usage": gpu_usage,
                    "mem_used": mem_used,
                    "mem_total": 8192,
                    "temperature": temperature,
                    "disk_used": 12.5,
                    "disk_total": 64.0,
                    "uptime": uptime,
                },
            })

            client.publish(topic_status, payload)
            status = "STREAMING" if stream_running else "idle"
            print(f"[Simulator] Status sent | {status} | CPU:{cpu_usage}% GPU:{gpu_usage}% Temp:{temperature}C")

            time.sleep(2)
            uptime += 2

    except KeyboardInterrupt:
        print("\n[Simulator] Stopping...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
