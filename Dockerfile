FROM python:3.9-slim

# プロキシー設定
ENV http_proxy=http://wwwproxy.osakac.ac.jp:8080
ENV https_proxy=http://wwwproxy.osakac.ac.jp:8080

WORKDIR /app

# 必要なシステムパッケージのインストール
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をインストール
RUN pip install --no-cache-dir \
    google-generativeai>=0.1.0 \
    python-dotenv>=0.19.0 \
    pandas>=1.5.0 \
    openpyxl>=3.0.0 \
    tqdm>=4.65.0 \
    requests>=2.25.1

# アプリケーションのコピー
COPY main.py .
COPY input.csv .

# デバッグ用：インストールされたパッケージの一覧を表示
RUN pip list
