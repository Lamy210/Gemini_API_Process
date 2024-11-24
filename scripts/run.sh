#!/bin/bash

# コンテナをバックグラウンドで起動
docker-compose up -d

# ログの確認
echo "Checking logs... Press Ctrl+C to stop watching logs"
docker-compose logs -f

# プロセスの状態確認
docker-compose ps
