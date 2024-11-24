``bash
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
chmod 755 "$PROCESSED_DIR"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

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
            
            # ファイルのパーミッションを確認
            if [ ! -r "$INPUT_DIR/input.csv" ]; then
                log "Error: Cannot read input.csv"
                continue
            fi
            
            # ファイルが空でないことを確認
            if [ ! -s "$INPUT_DIR/input.csv" ]; then
                log "Error: input.csv is empty"
                continue
            fi
            
            # プロセッサーの実行状態を確認
            if pgrep -f "python /app/src/gemini_processor.py" > /dev/null; then
                log "Processor is already running"
            else
                log "Starting processor"
            fi
        else
            log "File size changed, waiting for upload to complete"
        fi
    else
        if [ $((RANDOM % 60)) -eq 0 ]; then
            log "Waiting for input.csv"
        fi
    fi
    
    sleep 10
done