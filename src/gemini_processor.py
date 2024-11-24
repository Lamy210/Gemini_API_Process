# src/gemini_processor.py
import os
import csv
from datetime import datetime
import google.generativeai as genai
from typing import List, Dict, Optional
import asyncio
import urllib3
import logging
import time
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定数設定
INPUT_DIR = Path("/app/input")
OUTPUT_DIR = Path("/app/output")
PROCESSED_DIR = INPUT_DIR / "processed"
INPUT_FILE = "input.csv"

# プロキシ設定
os.environ['http_proxy'] = 'http://wwwproxy.osakac.ac.jp:8080'
os.environ['https_proxy'] = 'http://wwwproxy.osakac.ac.jp:8080'

# SSL証明書の警告を無視
urllib3.disable_warnings()

# Gemini APIの設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("環境変数 'GEMINI_API_KEY' が設定されていません。")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# 設定パラメータ
SKIP_ROWS = [int(x) for x in os.getenv("SKIP_ROWS", "1").split(",")]
PROBLEM_COLUMN = os.getenv("PROBLEM_COLUMN", "B")
CODE_COLUMN = os.getenv("CODE_COLUMN", "C")

def clean_code(code: str) -> str:
    """CSVから読み込んだコードの""を"に置換する"""
    return code.replace('""', '"') if code else ""

def create_prompt(problem: str, code: str) -> str:
    """プロンプトテンプレートに値を埋め込む"""
    return f"""#Instructions
貴方は、プログラミングに関連する質問に対して詳細な説明とアドバイスを提供するアシスタントです。サンプルコードは絶対に出力しないように注意してください。質問に対しては、 対応の説明とヒントを提供しますが、その回答が要件に合っているか、思考を促すような 内容になっているか、質問者に答えをそのまま出力していないかを確認し、適宜修正してから出力します。質問者の理解を確認するために、回答の最後には、「これで説明は理解できましたか？」という確認の文言を入れるようにしてください。 #problem {problem}
#code {code}
#answer"""

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_gemini_api(prompt: str) -> str:
    """Gemini APIを呼び出す（リトライ機能付き）"""
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        raise

async def process_csv() -> None:
    """CSVファイルを処理し、結果を新しいCSVファイルに出力する"""
    input_path = INPUT_DIR / INPUT_FILE
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"output_{timestamp}.csv"
    processed_path = PROCESSED_DIR / f"input_{timestamp}.csv"

    try:
        logger.info(f"Processing file: {input_path}")
        
        if not input_path.exists():
            logger.warning("Input file not found")
            return

        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            
            # ヘッダー行を処理
            header = next(reader)
            writer.writerow(header + ['API_Response'])
            
            # 各行を処理
            for row_num, row in enumerate(reader, start=2):
                if not any(row):  # 空行チェック
                    logger.info("Reached empty row, stopping processing")
                    break
                    
                if row_num in SKIP_ROWS:
                    writer.writerow(row + ['Skipped'])
                    logger.info(f"Skipped row {row_num}")
                    continue
                
                try:
                    problem = row[ord(PROBLEM_COLUMN) - ord('A')]
                    code = clean_code(row[ord(CODE_COLUMN) - ord('A')])
                    
                    prompt = create_prompt(problem, code)
                    response = await call_gemini_api(prompt)
                    
                    writer.writerow(row + [response])
                    logger.info(f"Processed row {row_num}")
                    
                except IndexError:
                    error_msg = f"Invalid column index at row {row_num}"
                    writer.writerow(row + [f'Error: {error_msg}'])
                    logger.error(error_msg)
                except Exception as e:
                    error_msg = f"Error processing row {row_num}: {str(e)}"
                    writer.writerow(row + [f'Error: {error_msg}'])
                    logger.error(error_msg)

        # 処理済みファイルを移動
        input_path.rename(processed_path)
        logger.info(f"Moved processed file to {processed_path}")

    except Exception as e:
        logger.error(f"Fatal error during processing: {str(e)}")
        raise

async def main() -> None:
    """メイン処理ループ"""
    while True:
        try:
            await process_csv()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
        
        await asyncio.sleep(60)  # 1分待機

if __name__ == "__main__":
    asyncio.run(main())