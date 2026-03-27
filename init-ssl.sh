#!/bin/bash
set -e

# SSL証明書の初期取得スクリプト（本番サーバーで実行）
# 使い方: ./init-ssl.sh your-email@example.com

EMAIL=${1:?"Usage: ./init-ssl.sh your-email@example.com"}
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"
DOMAINS=("camera-admin.evoxr.jp" "camera-app.evoxr.jp")

echo "=== Step 1: HTTP-only nginx で起動 ==="
# 一時的に init 用の nginx 設定を使う
$COMPOSE run -d --name nginx-init \
    -v "$(pwd)/nginx/nginx.init.conf:/etc/nginx/nginx.conf" \
    -p 80:80 \
    nginx nginx -g 'daemon off;' 2>/dev/null || \
docker run -d --name nginx-init \
    -v "$(pwd)/nginx/nginx.init.conf:/etc/nginx/nginx.conf" \
    -v camera-cloud-manager_certbot-webroot:/var/www/certbot \
    -p 80:80 \
    nginx:alpine

echo "=== Step 2: SSL証明書を取得 ==="
for domain in "${DOMAINS[@]}"; do
    echo "--- Requesting cert for $domain ---"
    $COMPOSE run --rm certbot certonly \
        --webroot -w /var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$domain"
done

echo "=== Step 3: init nginx を停止 ==="
docker stop nginx-init && docker rm nginx-init

echo "=== Step 4: 全サービス起動 ==="
$COMPOSE up -d

echo ""
echo "=== Done! ==="
echo "  Admin: https://camera-admin.evoxr.jp/"
echo "  Client: https://camera-app.evoxr.jp/"
