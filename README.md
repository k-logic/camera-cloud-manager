# VR180 Cloud Manager

複数企業・複数カメラを一元管理するクラウド側SaaS管理システム。
Jetson上のカメラ（camera-api）とMQTT over WebSocketで連携する。

## 技術スタック

| 項目 | 技術 |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 + JWT + paho-mqtt |
| Frontend | Vue.js 3 (CDN) + Vue Router 4 (hash-based) |
| DB | SQLite（開発） / PostgreSQL（本番） |
| MQTT | Mosquitto（TCP + WebSocket） |
| Proxy | nginx（HTTP + MQTT over WebSocket） |
| 環境 | Docker Compose |

## アーキテクチャ

```
ブラウザ ──HTTP──> nginx :80/443 ──> FastAPI :8000
                    │
外部MQTT ──WS──> nginx /mqtt ──> Mosquitto :9001
                                      │
内部app ──TCP:1883──────────> Mosquitto
                                      │
Jetson ──WS:80/mqtt──> nginx ──> Mosquitto
  └── jetson_client.py ──HTTP──> camera-api :8000
```

## セットアップ

### ローカル開発（Docker不使用）

```bash
# 依存インストール
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Mosquitto起動（初回: brew install mosquitto）
brew services start mosquitto

# サーバー起動
uvicorn app.main:app --reload --port 8000
```

- Admin UI: http://localhost:8000/admin/
- Client UI: http://localhost:8000/client/

### Docker開発環境

```bash
docker compose up --build
```

- Admin UI: http://localhost/admin/
- Client UI: http://localhost/client/

### 本番デプロイ

```bash
# 1. .env.prod を作成（.env.example を参考）
cp .env.example .env.prod
# DATABASE_URL, SECRET_KEY, POSTGRES_PASSWORD を本番用に変更

# 2. SSL証明書の初期取得
./init-ssl.sh your-email@example.com

# 3. 起動
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

- Admin UI: https://camera-admin.evoxr.jp/
- Client UI: https://camera-app.evoxr.jp/

## テストユーザー

| ユーザー | パスワード | 権限 |
|---|---|---|
| admin | admin | 管理者（全企業管理） |
| tanaka | tanaka | 企業ユーザー（Example Corp） |

```bash
# ユーザー作成
python create_user.py --username xxx --password xxx --display-name "Name" --admin
python create_user.py --username xxx --password xxx --display-name "Name" --company "Company Name"
```

## カメラ接続

### シミュレーター

```bash
python simulate_camera.py --camera-key <KEY> --broker localhost
```

### Jetson実機

```bash
# Jetsonにクライアントをコピー
scp jetson_client.py <JETSON_HOST>:~/jetson_client.py

# Jetson上で実行
python3 ~/jetson_client.py --camera-key <KEY> --broker <CLOUD_IP>
```

## ファイル構成

```
docker-compose.yml          # 開発用Docker構成
docker-compose.prod.yml     # 本番用Docker構成
nginx/nginx.conf            # 開発用nginx（HTTP）
nginx/nginx.prod.conf       # 本番用nginx（SSL + サブドメイン）
.env                        # 開発用環境変数
.env.prod                   # 本番用環境変数（gitignored）
app/                        # FastAPIアプリケーション
  main.py                   # エントリポイント
  routers/                  # APIエンドポイント
  models/                   # SQLAlchemyモデル
  schemas/                  # Pydanticスキーマ
  services/                 # MQTT・認証サービス
static/admin/               # Admin UI（Vue.js）
static/client/              # Client UI（Vue.js）
jetson_client.py            # Jetson用MQTTクライアント
simulate_camera.py          # カメラシミュレーター
seed.py                     # 初期データ投入
alembic/                    # DBマイグレーション
```

## MQTT設計

- トピック: `cameras/{camera_key}/status|settings|command`
- **settings**: Retained Message（カメラ再接続時に最新設定を即取得）
- **command**: 非Retained（reboot等の一回きりコマンド）
- **Desired State方式**: クラウドが「あるべき状態」を設定し、カメラが自律的に反映
