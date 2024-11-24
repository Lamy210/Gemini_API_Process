FROM python:3.9-slim

# プロキシ設定
ENV http_proxy=http://wwwproxy.osakac.ac.jp:8080
ENV https_proxy=http://wwwproxy.osakac.ac.jp:8080
ENV HTTP_PROXY=http://wwwproxy.osakac.ac.jp:8080
ENV HTTPS_PROXY=http://wwwproxy.osakac.ac.jp:8080

# 非rootユーザーを作成
ARG UID=1000
ARG GID=1000
ARG USERNAME=appuser

# 必要なパッケージをインストール
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# グループとユーザーを作成
RUN groupadd -g ${GID} ${USERNAME} && \
    useradd -u ${UID} -g ${USERNAME} -m -s /bin/bash ${USERNAME}

# アプリケーションディレクトリを作成
RUN mkdir -p /app/src /app/input /app/output /app/logs && \
    chown -R ${USERNAME}:${USERNAME} /app

WORKDIR /app

# Supervisord設定
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
RUN chmod 644 /etc/supervisor/conf.d/supervisord.conf

# pip用のプロキシ設定
RUN mkdir -p /etc/pip.conf && \
    echo "[global]" > /etc/pip.conf && \
    echo "proxy = http://wwwproxy.osakac.ac.jp:8080" >> /etc/pip.conf && \
    echo "https-proxy = http://wwwproxy.osakac.ac.jp:8080" >> /etc/pip.conf

# 必要なPythonパッケージをインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY src/ /app/src/
COPY docker/entrypoint.sh /app/docker/
COPY docker/watcher.sh /app/docker/

# 実行権限を付与
RUN chmod +x /app/docker/entrypoint.sh /app/docker/watcher.sh && \
    chown -R ${USERNAME}:${USERNAME} /app

USER root

ENTRYPOINT ["/app/docker/entrypoint.sh"]