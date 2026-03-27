#!/bin/bash
set -e

# SSL証明書の初期取得スクリプト
# 使い方: ./init-ssl.sh your-email@example.com

EMAIL=${1:?"Usage: ./init-ssl.sh your-email@example.com"}
DOMAINS=("camera-admin.evoxr.jp" "camera-app.evoxr.jp")

echo "=== Step 1: HTTP-only nginx で起動 ==="
cp nginx/nginx.conf nginx/nginx.ssl.conf.bak
cp nginx/nginx.init.conf nginx/nginx.conf
docker compose up -d nginx

echo "=== Step 2: SSL証明書を取得 ==="
for domain in "${DOMAINS[@]}"; do
    echo "--- Requesting cert for $domain ---"
    docker compose run --rm certbot certonly \
        --webroot -w /var/www/certbot \
        --email "$EMAIL" \
        --agree-tos \
        --no-eff-email \
        -d "$domain"
done

echo "=== Step 3: SSL版 nginx に切り替え ==="
cp nginx/nginx.ssl.conf.bak nginx/nginx.conf
rm nginx/nginx.ssl.conf.bak

echo "=== Step 4: 全サービス起動 ==="
docker compose up -d

echo ""
echo "=== Done! ==="
echo "  Admin: https://camera-admin.evoxr.jp/"
echo "  Client: https://camera-app.evoxr.jp/"
