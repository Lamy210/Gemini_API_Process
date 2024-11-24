#!/bin/bash

INPUT_DIR="/app/input"
PROCESSED_DIR="/app/input/processed"
LOG_FILE="/app/logs/watcher.log"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# 初期化
mkdir -p "$PROCESSED_DIR"
touch "$LOG_FILE"

log "Watcher started"

# メインループ
while true; do
    if [ -f "$INPUT_DIR/input.csv" ]; then
        log "Found new input.csv file"
        
        # ファイルのアップロード完了を待機
        initial_size=$(stat -f%z "$INPUT_DIR/input.csv" 2>/dev/null || stat -c%s "$INPUT_DIR/input.csv")
        sleep 5
        current_size=$(stat -f%z "$INPUT_DIR/input.csv" 2>/dev/null || stat -c%s "$INPUT_DIR/input.csv")
        
        if [ "$initial_size" = "$current_size" ]; then
            log "File size stable, proceeding with processing"
            
            # プロセッサーの実行状態を確認
            if ! pgrep -f "python /app/src/gemini_processor.py" > /dev/null; then
                log "Starting processor"
                python /app/src/gemini_processor.py &
            fi
        fi
    fi
    sleep 10
done