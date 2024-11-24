#!/bin/bash
set -e

# 必要なディレクトリの作成と権限設定
directories=("input/processed" "output" "logs")
for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    chmod 755 "$dir"
done

# スクリプトに実行権限を付与
chmod +x docker/*.sh scripts/*.sh

# Dockerコンテナの起動
docker-compose up -d

echo "Application started in background mode"
echo "Use 'scripts/check_logs.sh' to monitor logs"