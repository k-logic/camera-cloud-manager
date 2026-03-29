# VR180 Cloud Manager

## 概要
複数企業・複数カメラを一元管理するクラウド側SaaS管理システム。
Jetson上のカメラ（vr180-live-encoder/camera-api）とMQTTで連携する。

## 技術スタック
- Backend: FastAPI + SQLAlchemy 2.0 + JWT (python-jose) + passlib + paho-mqtt
- Frontend: Vue.js 3 (CDN, ビルドステップなし) + Vue Router 4 (HTML5 History mode)
- MQTT Broker: Mosquitto
- DB: SQLite（開発） → PostgreSQL（本番）
- Redis: カメラステータス管理（プライマリストア、キャッシュではない）
- Python仮想環境: `venv/`

## 起動方法
```bash
# Mosquitto + Redis（初回のみ brew install mosquitto redis）
brew services start mosquitto
brew services start redis

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
scp jetson_client.py logic-jetson:~/vr180-live-encoder/jetson_client.py

# Jetsonではsystemdサービスとして稼働
ssh logic-jetson "sudo systemctl restart jetson-client"
```
- カメラキー: `auQ7TPYkooIqfc2pAAzxAA`
- systemdサービス: `/etc/systemd/system/jetson-client.service`
- image_overlay_1: 有効（1920x1080フルスクリーン）

## アーキテクチャ
```
ブラウザ --HTTP(2秒ポーリング)--> クラウドFastAPI --MQTT--> Jetson
                                                          jetson_client.py --HTTP--> camera-api :8000
```
- 共有バックエンド + 分離フロントエンド（admin/client）
- Admin（運営会社）: 全企業・全カメラ管理、設定変更
- Client（クライアント企業）: 自社カメラの閲覧・操作
- 本番では `camera-admin.evoxr.jp` / `camera-app.evoxr.jp` でサブドメイン分離
- Desired State方式: クラウドは「あるべき状態」を設定、カメラが自律的に反映
- jetson_client.py は既存camera-apiのHTTPエンドポイントを呼ぶだけ（camera-apiのコード変更不要）

## ユーザーモデル
- 単一usersテーブルに `is_admin` フラグで管理者/企業ユーザーを区別
- 管理者: `is_admin=True`, `company_id=NULL`
- 企業ユーザー: `is_admin=False`, `company_id=企業ID`

## データ保存先
### PostgreSQL（永続データ）
- companies: 企業
- users: ユーザー（is_admin, company_id）
- cameras: カメラ（company_id, camera_key, pending_command）
- camera_settings: カメラ設定 1:1（camera_source, width, height, output_width, output_height, fps, bitrate, stream_url, stream_running, settings_version）
- command_logs: 操作履歴（command, issued_by, issued_at）

### Redis（リアルタイムステータス）
- `camera_status:{camera_id}`: ハッシュ型、TTL 10秒
- 項目: is_online, last_seen, stream_running, stream_fps, stream_bitrate, stream_time, stream_quality, cpu_usage, gpu_usage, mem_used, mem_total, temperature, disk_used, disk_total, uptime
- TTL切れ = オフライン（offline_checkerは不要）
- CameraStatusテーブルは廃止済み（camera_statusテーブルはマイグレーションで作成されるがアプリでは使わない）

## MQTT設計
- トピック: `cameras/{camera_key}/status|settings|command`
- settings は Retained Message（カメラ再接続時に最新設定を即取得）
- command は非Retained（reboot等の一回きり）
- カメラ削除時にRetained Messageを自動クリア（バージョン不整合防止）
- Mosquitto設定: `/opt/homebrew/etc/mosquitto/mosquitto.conf`
  - `listener 1883 0.0.0.0` + `allow_anonymous true`
- MQTT over WebSocket採用理由:
  1. ポート80/443のみで通信（FW変更不要）
  2. Retained Messageで自動同期（Desired State方式）
  3. リアルタイムPush（ポーリング遅延なし）

## 主要ファイル
| ファイル | 説明 |
|---|---|
| `app/main.py` | Redis/MQTT起動/停止 + SPAStaticFiles |
| `app/services/redis_service.py` | Redisステータス管理（保存/取得/TTL/型変換） |
| `app/services/mqtt_service.py` | MQTTクライアント管理（Subscribe/Publish → Redis保存） |
| `app/routers/cameras.py` | カメラCRUD + 設定更新時にMQTT配信 + Redis統合レスポンス |
| `jetson_client.py` | Jetson用MQTTクライアント（Jetsonにscpでコピー） |
| `simulate_camera.py` | MQTT版カメラシミュレーター |
| `static/admin/js/components/CameraDetail.js` | Admin UI カメラ詳細 |
| `static/client/js/components/CameraDetail.js` | Client UI カメラ詳細 |
| `static/*/js/components/NotFound.js` | 404ページ |
| `docker-entrypoint.sh` | Alembicマイグレーション + seed（SEED_DB=1時のみ） |
| `seed.py` | 初期データ投入（dev環境のみ、本番では実行しない） |

## Docker構成
- 設定ファイルはdev/prodで分離、`docker-compose.yml`は使う方をコピー（gitignore）
  - `docker-compose.dev.yml` → `.env.dev` + `nginx/nginx.dev.conf` を参照
  - `docker-compose.prod.yml` → `.env.prod` + `nginx/nginx.prod.conf` を参照
- ローカル: `cp docker-compose.dev.yml docker-compose.yml && docker compose up --build`
- 本番: `cp docker-compose.prod.yml docker-compose.yml && docker compose up --build -d`

## UI
- Bootstrap 5 + サイドバーダッシュボードレイアウト
- デスクトップ: 左250pxダークサイドバー + 右メインコンテンツ
- スマホ: ハンバーガーメニュー + Bootstrap offcanvas

## 実装フェーズ
- Phase 1: 基盤（認証 + 企業 + ユーザー） ✅
- Phase 2: カメラ管理（CRUD + 設定 + UI） ✅
- Phase 3: 配信制御（Desired State + command_logs） ✅
- Phase 4: ポーリング + ステータス監視 ✅
- Phase 5: MQTT移行 + Jetson実機接続 ✅
- Phase 6: Bootstrap 5 UIリニューアル + 本番デプロイ ✅
- Phase 7: Redis移行（ステータス全てRedis、DB書き込みゼロ） ✅

## 本番デプロイ
```bash
git push gitlab main
ssh ipvdnp52042-dnp-encoder "cd ~/camera-cloud-manager && git pull && docker compose up --build -d"
```
- 本番サーバー: `ipvdnp52042-dnp-encoder` (logic@10.12.52.42)
- Admin: https://camera-admin.evoxr.jp/
- Client: https://camera-app.evoxr.jp/
- SSL: Let's Encrypt (certbot)
- seedは本番では実行されない（SEED_DB環境変数なし）

## SPA対応
- Vue Router: HTML5 History mode（`createWebHistory()`）
- FastAPI: `SPAStaticFiles` クラスで未知パスに `index.html` を返す
- Vue Router: `/:pathMatch(.*)*` でキャッチオール → 404ページ表示
- nginx: `/api/` はproxy直通、それ以外は `/admin` or `/client` にrewrite

## 既知の問題
- passlib + bcrypt 5.x非互換: bcrypt==4.1.3にピン留め（警告は出るが動作OK）
- SQLiteはALTER COLUMN非対応: スキーマ変更時はDB再作成（開発時のみ）
- jetson_client.py変更後はJetsonへscp + systemctl restart忘れに注意
- カメラキーは手動入力（デバイスに事前書き込み済みのキーをadminが登録）

## 関連リポジトリ
- Jetson側: git@gitlab-ld:INV_VisionAI/vr180-live-encoder.git（タグ: v1.0, v2.0）
- Jetson SSH: `ssh logic-jetson`（鍵: ~/.ssh/dnp-camera）
- Jetson camera-api: ~/vr180-live-encoder/camera-api/（FastAPI :8000）
- Gitリモート: gitlab（社内）, origin（GitHub, 機密除去済み）
