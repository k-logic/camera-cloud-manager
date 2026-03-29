# VR180 Cloud Manager 設計書

## 概要
複数企業・複数カメラを一元管理するクラウド側SaaS管理システム。
Jetson上のカメラ（vr180-live-encoder/camera-api）とMQTTで連携する。

## アーキテクチャ

```
[管理者ブラウザ] ──HTTP/2秒ポーリング──→ [クラウド FastAPI + Vue.js]
                                              │
                                         [Mosquitto MQTT Broker]
                                              │
                               ┌──────────────┼──────────────┐
                         [Jetson 1]      [Jetson 2]      [Jetson N]
                          jetson_client.py ──HTTP──→ camera-api :8000
```

### 通信方式
- **ブラウザ ↔ クラウド**: HTTP API（JWT認証）+ 2秒間隔ポーリング
- **クラウド ↔ カメラ**: MQTT（Mosquitto）
- **jetson_client.py ↔ camera-api**: localhost HTTP（既存APIをそのまま利用）

### 設計方針
- **Desired State方式**: クラウドは「あるべき状態」を設定、カメラが自律的に反映
- **既存camera-api非侵入**: jetson_client.pyが外側からHTTPで呼ぶだけ、camera-apiのコード変更不要
- **HTTPポーリングをフォールバックとして維持**: MQTTが使えない環境用

## 技術スタック

- Backend: FastAPI + SQLAlchemy 2.0 + JWT (python-jose) + passlib + paho-mqtt
- Frontend: Vue.js 3 (CDN, ビルドステップなし) + Vue Router 4 (HTML5 History mode)
- MQTT Broker: Mosquitto
- DB: SQLite（開発） → PostgreSQL（本番）
- Redis: カメラステータス管理（プライマリストア）

## Docker構成

設定ファイルはdev/prodで分離。`docker-compose.yml`は使う方をコピーして利用（gitignore）。

| ファイル | 参照先 | git管理 |
|---|---|---|
| `docker-compose.dev.yml` | `.env.dev` + `nginx/nginx.dev.conf` | あり |
| `docker-compose.prod.yml` | `.env.prod` + `nginx/nginx.prod.conf` | あり |
| `docker-compose.yml` | 上記いずれかのコピー | **gitignore** |

```bash
# ローカル開発
cp docker-compose.dev.yml docker-compose.yml
docker compose up --build

# 本番デプロイ
cp docker-compose.prod.yml docker-compose.yml
docker compose up --build -d
```

## UI

Bootstrap 5 + サイドバーダッシュボードレイアウト。

- **デスクトップ (≥768px)**: 左250px固定ダークサイドバー + 右メインコンテンツ
- **スマホ (<768px)**: 上部ナビバー + ハンバーガーメニュー → Bootstrap offcanvasサイドバー
- ページ遷移時にoffcanvasを自動クローズ（router.afterEach）

## プロジェクト構成

```
cloud-manager/
├── docker-compose.dev.yml        # 開発用Docker構成
├── docker-compose.prod.yml       # 本番用Docker構成（SSL + certbot）
├── nginx/
│   ├── nginx.dev.conf            # 開発用nginx（HTTP only）
│   ├── nginx.prod.conf           # 本番用nginx（SSL + サブドメイン）
│   └── nginx.init.conf           # SSL初回取得用
├── app/
│   ├── main.py                   # FastAPIアプリ + Redis/MQTT起動
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py           # get_db, get_current_user, get_camera_by_key
│   ├── models/
│   │   ├── user.py
│   │   ├── company.py
│   │   └── camera.py             # Camera, CameraSettings, CommandLog
│   ├── schemas/
│   │   ├── auth.py, user.py, company.py, camera.py
│   │   └── polling.py            # StreamStatus, SystemStatus, PollSync*
│   ├── routers/
│   │   ├── auth.py               # ログイン/リフレッシュ
│   │   ├── companies.py          # 企業CRUD
│   │   ├── cameras.py            # カメラCRUD + 設定 + MQTT配信
│   │   └── polling.py            # HTTPポーリング（フォールバック）
│   └── services/
│       ├── mqtt_service.py       # MQTTクライアント管理
│       └── redis_service.py      # Redisステータス管理（保存/取得/TTL）
├── static/
│   ├── admin/                    # 管理者UI
│   └── client/                   # クライアント企業UI
├── simulate_camera.py            # カメラシミュレーター（MQTT版）
├── jetson_client.py              # Jetson用MQTTクライアント
├── create_user.py
└── requirements.txt
```

## DBスキーマ

### cameras
| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| company_id | FK → companies | 所属企業 |
| name | String(100) | カメラ名（UI編集可能） |
| camera_key | String(32) UNIQUE | 認証キー（デバイスに事前書込み済みのものをadminが手動登録） |
| is_active | Boolean | 有効/無効 |
| pending_command | String(50) NULL | 一発コマンド（現在未使用） |

### camera_settings（1:1）
| カラム | 型 | 説明 |
|---|---|---|
| camera_id | FK → cameras | |
| camera_source | String(10) | "mipi" / "usb"（デフォルト: mipi） |
| width | Integer | カメラ入力幅（1280/1920/3840） |
| height | Integer | カメラ入力高さ（720/1080/2160） |
| output_width | Integer | 配信解像度幅（1280/1920/3840） |
| output_height | Integer | 配信解像度高さ（720/1080/2160） |
| fps | Integer | フレームレート（30/60） |
| bitrate | Integer | ビットレート kbps（800〜50000） |
| stream_url | String(500) NULL | RTMP URL（キー込み） |
| stream_running | Boolean | Desired State（配信するかどうか） |
| settings_version | Integer | 変更ごとにインクリメント |

### camera_status（Redis）
DBテーブルではなくRedisハッシュで管理。キー: `camera_status:{camera_id}`、TTL: 10秒。

| フィールド | 型 | 説明 |
|---|---|---|
| is_online | Boolean | 自動付与（True）。TTL切れ=オフライン |
| last_seen | String(ISO) | 自動付与（UTC） |
| stream_running | Boolean | Actual State（実際の配信状態） |
| stream_fps | Float | 実際のFPS |
| stream_bitrate | Integer | 実際のビットレート |
| stream_started_at | String(ISO) | 配信開始時刻（Redisで自動管理） |
| stream_quality | String | "good" / "unstable" / "bad" |
| cpu_usage, gpu_usage | Float | CPU/GPU使用率 |
| mem_used, mem_total | Integer | メモリ (MB) |
| temperature | Float | 温度 (℃) |
| disk_used, disk_total | Float | ディスク (GB) |
| uptime | Integer | 稼働時間 (秒) |

- カメラが2秒ごとにステータス送信 → TTLが10秒にリセット
- カメラが停止 → 10秒後にキーが自動消滅 → APIは「オフライン」を返す
- DBへの書き込みはゼロ（offline_checkerも不要）
- カメラごとにキーが独立しているため、1台が切れても他に影響なし
- `stream_started_at`はRedis内で自動管理（配信開始時にセット、停止でクリア）
- 配信経過時間はフロントのJavaScriptで`stream_started_at`から毎秒計算（カメラ側は送らない）

### command_logs
| カラム | 型 | 説明 |
|---|---|---|
| id | Integer PK | |
| camera_id | FK → cameras | |
| command | String(50) | "start" / "stop" |
| issued_by | FK → users | 操作者 |
| issued_at | DateTime | 操作日時 |

## MQTT設計

### トピック

| トピック | 方向 | Retained | 内容 |
|---|---|---|---|
| `cameras/{camera_key}/status` | カメラ → クラウド | No | ステータス報告（2秒間隔） |
| `cameras/{camera_key}/settings` | クラウド → カメラ | Yes | 設定配信（変更時のみ） |

### メッセージ形式

**status（カメラ → クラウド）**
```json
{
  "settings_version": 14,
  "stream_status": {
    "running": true,
    "width": 1920, "height": 1080,
    "fps": 30, "bitrate": 4129,
    "stream_quality": "good"
  },
  "system_status": {
    "cpu_usage": 45.2, "gpu_usage": 62.1,
    "mem_used": 3500, "mem_total": 8192,
    "temperature": 52.3,
    "disk_used": 12.5, "disk_total": 64.0,
    "uptime": 86400
  }
}
```

**settings（クラウド → カメラ、Retained）**
```json
{
  "camera_source": "mipi",
  "width": 1920, "height": 1080,
  "output_width": 1920, "output_height": 1080,
  "fps": 30, "bitrate": 4000,
  "stream_url": "rtmp://...",
  "stream_running": true,
  "settings_version": 14
}
```

### 動作フロー

1. **設定変更**: UI → API → DB保存 → settings_version++ → MQTT Publish (Retained)
2. **カメラ受信**: jetson_client.py が settings を Subscribe → settings_version比較 → camera-api HTTP呼び出し
3. **ステータス報告**: camera-api → jetson_client.py → MQTT Publish → Redis保存（TTL 10秒）
4. **再接続**: Retained Messageにより最新設定を即座に取得
5. **オフライン検知**: Redis TTL切れ（10秒）でキー自動消滅 → APIが「オフライン」を返す
6. **オフライン時自動停止**: カメラがオフライン + settings.stream_running=True → 自動的にFalseに更新 + Retained Message更新（APIポーリング時に検知）

## Jetson側構成

```
Jetson (<JETSON_HOST>)
├── vr180-live-encoder/camera-api/    # 既存（変更なし）
│   ├── app/main.py                   # FastAPI :8000
│   ├── app/api/stream.py             # POST /stream/start, /stop, GET /status
│   ├── app/core/streamer.py          # GStreamer + FFmpeg パイプライン
│   ├── app/core/system_status.py     # CPU/GPU/メモリ/温度
│   └── app/core/uart_sender.py       # ESP32 UART通信
└── jetson_client.py                  # MQTTクライアント（新規追加のみ）
```

### jetson_client.py の役割
- MQTTブローカーに接続、settings/commandをSubscribe
- 設定変更受信 → camera-api の `POST /stream/start` or `POST /stream/stop` を呼ぶ
- 2秒間隔で camera-api の `GET /stream/status` + `GET /system/status` を取得 → MQTTでPublish
- camera-apiのコードは一切変更しない

### camera-api の StartRequest パラメータ
| パラメータ | クラウドから | デフォルト |
|---|---|---|
| camera_source | ○ | "mipi" |
| width, height | ○ | 1920x1080 |
| output_width, output_height | ○ | 1920x1080 |
| fps | ○ | 30 |
| bitrate | ○ | 4000 |
| stream_url | ○ | - |
| audio_bitrate | - | "128k" |
| audio_sample_rate | - | 44100 |
| audio_channels | - | 1 |
| image_overlay 1〜3 | - | disabled |
| text_overlay 1〜3 | - | disabled |
| show_fps | - | false |

## APIエンドポイント

| 認証 | メソッド | パス | 説明 |
|---|---|---|---|
| - | POST | /api/auth/login | ログイン(JWT発行) |
| JWT | POST | /api/auth/refresh | トークン更新 |
| JWT | GET/POST | /api/companies/* | 企業CRUD |
| JWT | GET/POST | /api/companies/{id}/cameras | カメラ一覧/作成 |
| JWT | GET/PUT/DELETE | /api/cameras/{id} | カメラ詳細/更新/削除 |
| JWT | GET/PUT | /api/cameras/{id}/settings | 設定取得/更新（→MQTT配信） |
| JWT | GET | /api/cameras/{id}/commands | コマンド履歴 |
| camera_key | POST | /api/poll/sync | HTTPポーリング（フォールバック） |

## UI構成

### Admin UI（管理者）
- 全企業・全カメラ管理
- カメラ詳細:
  - **Camera Info**: カメラ名（ダブルクリック編集）、Camera Key（コピーボタン）、Connection（Online/Offline）、作成日
  - **Stream Control**: Desired State、Actual State、Bitrate、FPS、Stream Time（配信中のみ）、Start/Stopボタン
  - **Stream Settings**: Camera Input（HD/FHD/4K）、Output Resolution、FPS（30/60）、Bitrate、Stream URL（変更時自動保存）
  - **Device Status**: CPU/GPU/メモリ/温度/ディスク/Uptime
- 2秒間隔で自動更新

### Client UI（クライアント企業）
- 自社カメラのみ閲覧・操作
- Admin UIと同じカメラ詳細画面

## Desired State方式

```
[UI] → stream_running: true → [DB] → [MQTT] → [jetson_client.py] → [camera-api]
                                                                          │
                                                                    実際にGStreamer起動
                                                                          │
[UI] ← Actual State ← [DB] ← [MQTT] ← [jetson_client.py] ← stream/status
```

- **Desired State** (camera_settings.stream_running): 管理者が設定した「あるべき状態」
- **Actual State** (camera_status.stream_running): カメラから報告される「実際の状態」
- エラー時: Desired=Running, Actual=Stopped → 異常と判断可能
- settings_versionで差分検知、Retained Messageで再接続時の設定自動同期
- **オフライン時自動停止**: カメラがオフラインになると自動的にstream_running=Falseに更新 + Retained Message更新 → 再起動時に配信が自動再開しない（手動Startが必要）

## 起動方法

### クラウド（Mac開発環境）
```bash
# Mosquitto
brew services start mosquitto

# サーバー
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Jetson
```bash
# camera-api（既存）
cd ~/vr180-live-encoder/camera-api
source venv/bin/activate
uvicorn app.main:app --port 8000

# MQTTクライアント（別ターミナル）
cd ~
source venv/bin/activate
python3 jetson_client.py --camera-key <KEY> --broker <CLOUD_IP>
```

### テスト（シミュレーター）
```bash
source venv/bin/activate
python -u simulate_camera.py --camera-key <KEY>
```

## Mosquitto設定

```
# /opt/homebrew/etc/mosquitto/mosquitto.conf
listener 1883 0.0.0.0
allow_anonymous true
```

## スケーラビリティ

- 3000台カメラ × 2秒間隔 = 毎秒1500メッセージ（Mosquittoで対応可能）
- MQTT常時接続のため、HTTPポーリングと比較してオーバーヘッドが極小
- 将来的にブラウザ↔クラウドもWebSocketに置換可能

## 実装フェーズ

| Phase | 内容 | 状態 |
|---|---|---|
| Phase 1 | 基盤（認証 + 企業 + ユーザー） | ✅ |
| Phase 2 | カメラ管理（CRUD + 設定 + UI） | ✅ |
| Phase 3 | 配信制御（Desired State + command_logs） | ✅ |
| Phase 4 | ポーリング + ステータス監視 | ✅ |
| Phase 5 | MQTT移行 + Jetson実機接続 | ✅ |
| Phase 6 | Bootstrap 5 UIリニューアル + 本番デプロイ | ✅ |
| Phase 7 | Redis移行（ステータス全てRedis、CameraStatusテーブル廃止） | ✅ |
| Phase 8 | Stream Control強化（Bitrate/FPS/経過時間表示、オフライン時自動停止） | ✅ |

## 今後のロードマップ

### 権限モデルの変更
現在のadmin（運営者）を企業管理者に格下げし、3階層にする。

```
現在:
  admin（運営者） → 全企業・全カメラを管理
  app（企業ユーザー） → 自社カメラの閲覧・操作

将来:
  運営者（佐藤） → 画面なし。DB直接 or CLIで企業・ユーザー作成
  admin（企業の管理者） → 自社カメラの登録・設定・ユーザー管理
  app（企業の一般ユーザー） → 自社カメラの閲覧・操作のみ
```

### ドメイン構成（将来）
```
camera-admin.evoxr.jp → 企業管理者向け画面（カメラ登録・設定変更）
camera-app.evoxr.jp   → 一般ユーザー向け画面（閲覧・操作のみ）
camera-api.evoxr.jp   → API専用（スマホアプリ対応時に追加）
```
- フロントは2つ（admin/app）に分離したまま、将来別々に進化させる
- バックエンドは1つ（共通API）
- API専用ドメインはスマホアプリ対応時に追加

### ステータス管理 → Redis移行済み ✅
カメラステータスを全てRedisに移行完了。DBへの書き込みはゼロ。

```
Jetson → MQTT → Redis(TTL 10秒) ← API ← ブラウザ/スマホ
```

#### 設計判断
- **Redisはキャッシュではなくプライマリストア**（DBの前段ではない）
- ステータスは2秒ごとに上書きされる揮発データ → DBに永続化する意味がない
- CameraStatusテーブルは廃止（offline_checkerも廃止）
- TTL切れ = オフライン（Redis側で自動管理、バックグラウンドタスク不要）
- カメラごとにキーが独立 → 1台が切れても他に影響なし
- Twitch, Mux等の配信サービスも同様のアーキテクチャを採用

#### DBとRedisの役割分担
| 保存先 | データ | 例 |
|---|---|---|
| PostgreSQL | 永続ビジネスデータ | ユーザー、企業、カメラ、設定、コマンド履歴 |
| Redis | リアルタイムステータス | is_online, stream_running, CPU/GPU/メモリ/温度/ビットレート等 |

#### スケーラビリティ
| 台数 | DB方式 | Redis方式 |
|---|---|---|
| 100台 | 余裕 | 余裕 |
| 3,000台 | 余裕 | 余裕 |
| 10,000台 | 限界付近（WAL/VACUUM問題） | 余裕 |

#### 将来の拡張
- 履歴グラフ（CPU推移等）が必要な場合 → 時系列DB（InfluxDB等）を追加
- 現在のRedis + PostgreSQL構成はそのまま維持
