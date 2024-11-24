# docker/watcher.sh
#!/bin/bash

INPUT_DIR="/app/input"
PROCESSED_DIR="/app/input/processed"
LOG_FILE="/app/logs/watcher.log"

mkdir -p "$PROCESSED_DIR"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

while true; do
    if [ -f "$INPUT_DIR/input.csv" ]; then
        log "Found new input.csv file"
        
        # ファイルが完全にアップロードされるのを待つ
        sleep 10
        
        # プロセッサーを実行
        python /app/src/gemini_processor.py
        
        # 処理済みファイルを移動
        timestamp=$(date +%Y%m%d_%H%M%S)
        mv "$INPUT_DIR/input.csv" "$PROCESSED_DIR/input_${timestamp}.csv"
        log "Processed and moved input.csv to $PROCESSED_DIR/input_${timestamp}.csv"
    fi
    
    sleep 60
done