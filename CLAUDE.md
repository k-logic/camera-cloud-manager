# VR180 Cloud Manager

## 概要
複数企業・複数カメラを一元管理するクラウド側SaaS管理システム。
Jetson上のカメラ（vr180-live-encoder/camera-api）とMQTTで連携する。

## 技術スタック
- Backend: FastAPI + SQLAlchemy 2.0 + JWT (python-jose) + passlib + paho-mqtt
- Frontend: Vue.js 3 (CDN, ビルドステップなし) + Vue Router 4 (hash-based)
- MQTT Broker: Mosquitto
- DB: SQLite（開発） → PostgreSQL（本番）
- Python仮想環境: `venv/`

## 起動方法
```bash
# Mosquitto（初回のみ brew install mosquitto）
brew services start mosquitto

# サーバー
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
- Admin UI: http://localhost:8000/admin/
- Client UI: http://localhost:8000/client/

## テストユーザー
- admin / admin（管理者、company_id=NULL）
- tanaka / tanaka（企業ユーザー、Example Corp所属）
- ユーザー作成: `python create_user.py --username xxx --password xxx --display-name "Name" --admin`

## カメラシミュレーター
```bash
python -u simulate_camera.py --camera-key <KEY>
```

## Jetson実機接続
```bash
# Mac → Jetson にクライアントをコピー
scp jetson_client.py <JETSON_HOST>:~/jetson_client.py

# Jetson上で実行（camera-api が :8000 で起動済みであること）
source ~/venv/bin/activate
python3 ~/jetson_client.py --camera-key <KEY> --broker <CLOUD_IP>
```

## アーキテクチャ
```
ブラウザ --HTTP(2秒ポーリング)--> クラウドFastAPI --MQTT--> Jetson
                                                          jetson_client.py --HTTP--> camera-api :8000
```
- 共有バックエンド + 分離フロントエンド（admin/client）
- Admin（運営会社）: 全企業・全カメラ管理、設定変更
- Client（クライアント企業）: 自社カメラの閲覧・操作
- 本番では `admin.example.com` / `app.example.com` でサブドメイン分離
- Desired State方式: クラウドは「あるべき状態」を設定、カメラが自律的に反映
- jetson_client.py は既存camera-apiのHTTPエンドポイントを呼ぶだけ（camera-apiのコード変更不要）

## ユーザーモデル
- 単一usersテーブルに `is_admin` フラグで管理者/企業ユーザーを区別
- 管理者: `is_admin=True`, `company_id=NULL`
- 企業ユーザー: `is_admin=False`, `company_id=企業ID`

## DBテーブル
- companies: 企業
- users: ユーザー（is_admin, company_id）
- cameras: カメラ（company_id, camera_key, pending_command）
- camera_settings: カメラ設定 1:1（camera_source, width, height, output_width, output_height, fps, bitrate, stream_url, stream_running, settings_version）
- camera_status: カメラ状態 1:1（is_online, stream_running, CPU/GPU/メモリ/温度等）
- command_logs: 操作履歴（command, issued_by, issued_at）

## MQTT設計
- トピック: `cameras/{camera_key}/status|settings|command`
- settings は Retained Message（カメラ再接続時に最新設定を即取得）
- command は非Retained（reboot等の一回きり）
- Mosquitto設定: `/opt/homebrew/etc/mosquitto/mosquitto.conf`
  - `listener 1883 0.0.0.0` + `allow_anonymous true`

## 主要ファイル
| ファイル | 説明 |
|---|---|
| `app/services/mqtt_service.py` | MQTTクライアント管理（Subscribe/Publish） |
| `app/routers/cameras.py` | カメラCRUD + 設定更新時にMQTT配信 |
| `app/main.py` | MQTT起動/停止 + offline_checker（10秒でオフライン判定） |
| `jetson_client.py` | Jetson用MQTTクライアント（Jetsonにscpでコピー） |
| `simulate_camera.py` | MQTT版カメラシミュレーター |
| `static/admin/js/components/CameraDetail.js` | Admin UI カメラ詳細 |
| `static/client/js/components/CameraDetail.js` | Client UI カメラ詳細 |

## 実装フェーズ
- Phase 1: 基盤（認証 + 企業 + ユーザー） ✅
- Phase 2: カメラ管理（CRUD + 設定 + UI） ✅
- Phase 3: 配信制御（Desired State + command_logs） ✅
- Phase 4: ポーリング + ステータス監視 ✅
- Phase 5: MQTT移行 + Jetson実機接続 ✅

## 既知の問題
- passlib + bcrypt 5.x非互換: bcrypt==4.1.3にピン留め（警告は出るが動作OK）
- SQLiteはALTER COLUMN非対応: スキーマ変更時はDB再作成（開発時のみ）
- jetson_client.py変更後はJetsonへscp忘れに注意

## 関連リポジトリ
- Jetson側: 別リポジトリ（vr180-live-encoder）
- Jetson camera-api: FastAPI :8000
