import os
import csv
import google.generativeai as genai
from typing import List, Dict, Optional, Tuple
import pandas as pd
import json
import traceback
import sys
import time
import random
from datetime import datetime
from tqdm import tqdm
import signal
from itertools import cycle
from dotenv import load_dotenv

class GeminiPromptValidator:
    def __init__(self):
        # .envファイルの読み込み
        load_dotenv()
        
        self.api_keys = self._load_api_keys()
        if not self.api_keys:
            raise ValueError("No API keys found in environment variables")
        
        print(f"Loaded {len(self.api_keys)} API keys")
        self.api_key_cycle = cycle(self.api_keys)
        self.current_api_key = next(self.api_key_cycle)
        
        self.model_name = "gemini-1.5-flash"  # モデルをflashに変更
        self.prompt_template = """#Instructions
貴方は、プログラミングに関連する質問に対して詳細な説明とアドバイスを提供するアシスタントです。サンプルコードは絶対に出力しないように注意してください。質問に対しては、対応の説明とヒントを提供しますが、その回答が要件に合っているか、思考を促すような内容になっているか、質問者に答えをそのまま出力していないかを確認し、適宜修正してから出力します。質問者の理解を確認するために、回答の最後には、「これで説明は理解できましたか？」という確認の文言を入れるようにしてください。
#problem {problem}
#code {code}
#answer {answer}"""

        self._configure_genai()
        self.is_processing = False
        
        # API使用状況の追跡
        self.api_usage = {key[-4:]: 0 for key in self.api_keys}

    def _load_api_keys(self) -> List[str]:
        """環境変数から利用可能なAPI keyを読み込む"""
        api_keys = []
        for i in range(1, 4):  # API_KEY_1 から API_KEY_3 まで確認
            key = os.getenv(f'API_KEY_{i}')
            if key:
                api_keys.append(key)
                print(f"Found API_KEY_{i} (ends with: ...{key[-4:]})")
        return api_keys

    def _configure_genai(self):
        """現在のAPI keyでGenAIを設定"""
        genai.configure(api_key=self.current_api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _switch_api_key(self):
        """次のAPI keyに切り替え"""
        old_key = self.current_api_key
        self.current_api_key = next(self.api_key_cycle)
        print(f"\nSwitching API key (Previous: ...{old_key[-4:]}, New: ...{self.current_api_key[-4:]})")
        self._configure_genai()
        
        # API使用状況の表示
        print("\nAPI Key Usage Statistics:")
        for key_suffix, count in self.api_usage.items():
            print(f"Key ...{key_suffix}: {count} requests")

    def api_request_with_retry(self, row_num: int, problem: str, code: str, answer: str) -> Tuple[str, str, int, str]:
        """APIリクエストを実行し、エラー時は再試行"""
        attempt = 0
        prompt = self.get_prompt_template(problem, code, answer)
        base_delay = 2

        while True:
            try:
                print(f"\nAttempting request for row {row_num} (attempt {attempt + 1}) using key ...{self.current_api_key[-4:]}")
                response = self.model.generate_content(prompt)
                
                # 成功したリクエストをカウント
                self.api_usage[self.current_api_key[-4:]] += 1
                
                return prompt, response.text, attempt + 1, self.current_api_key[-4:]

            except Exception as e:
                error_str = str(e)
                print(f"\nError on row {row_num}, attempt {attempt + 1}:")
                print(f"Error message: {error_str}")
                
                if "429" in error_str:
                    attempt += 1
                    self._switch_api_key()
                    
                    # 待機時間の計算を改善
                    delay = base_delay * (1 + random.random())
                    print(f"Waiting {delay:.2f} seconds before retrying...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Unexpected error: {error_str}")
                    traceback.print_exc()
                    raise

    def clean_code(self, code: str) -> str:
        """Remove extra quotes from code string"""
        if isinstance(code, str):
            return code.replace('""', '"')
        return str(code)

    def process_excel(self, input_file: str) -> None:
        """Process Excel file and write results"""
        try:
            print(f"Reading Excel file: {input_file}")
            df = pd.read_excel(input_file)
            print(f"Excel file loaded successfully. Columns: {df.columns.tolist()}")
            
            # 出力ファイル名に日時を追加
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'/app/output_{timestamp}.csv'
            
            self.is_processing = True
            results = []
            
            with tqdm(total=len(df.iloc[1:]), desc="Processing rows", dynamic_ncols=True) as pbar:
                for i, row in df.iloc[1:].iterrows():
                    if row.isna().all():
                        break
                    
                    result = self.process_row(row, i + 2)
                    if result:
                        results.append(result)
                        self.write_partial_results([result], output_file, i == 1)
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Row': i + 2,
                        'API Key': f'...{self.current_api_key[-4:]}',
                        'Requests': self.api_usage[self.current_api_key[-4:]]
                    })
            
            print("\nFinal API Key Usage Statistics:")
            for key_suffix, count in self.api_usage.items():
                print(f"Key ...{key_suffix}: {count} requests")
            
            print(f"\nProcessing completed. Total processed: {len(results)} rows")
            print(f"Results written to: {output_file}")
            self.is_processing = False
            
        except Exception as e:
            print(f"\nError processing Excel file: {e}")
            traceback.print_exc()

    def process_row(self, row: pd.Series, row_num: int) -> Optional[Dict]:
        """Process a single row"""
        try:
            problem = str(row['問題文'])
            code = self.clean_code(row['正解プログラム'])
            answer = str(row['pico-js動作結果'])  # D列の値を取得
            
            print(f"\nProcessing row {row_num}")
            prompt, response, attempts, used_key = self.api_request_with_retry(row_num, problem, code, answer)
            
            return {
                'row': row_num,
                'problem': problem,
                'code': code,
                'answer': answer,  # D列の値を追加
                'prompt': prompt,
                'response': response,
                'timestamp': datetime.now().isoformat(),
                'attempts': attempts,
                'api_key': used_key,
                'total_requests': self.api_usage[used_key]
            }
            
        except Exception as e:
            print(f"\nError processing row {row_num}:")
            traceback.print_exc()
            return None

    def get_prompt_template(self, problem: str, code: str, answer: str) -> str:
        """Return the formatted prompt template"""
        return self.prompt_template.format(problem=problem, code=code, answer=answer)

    def write_partial_results(self, results: List[Dict], output_file: str, write_header: bool = False) -> None:
        """Write results to CSV file incrementally"""
        fieldnames = [
            'row', 'problem', 'code', 'answer', 'prompt', 'response', 
            'timestamp', 'attempts', 'api_key', 'total_requests'
        ]
        mode = 'w' if write_header else 'a'
        
        try:
            with open(output_file, mode, encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if write_header:
                    writer.writeheader()
                writer.writerows(results)
        except Exception as e:
            print(f"\nError writing results: {e}")
            traceback.print_exc()

def handle_sigterm(signum, frame):
    print("\nReceived SIGTERM signal. Cleaning up...")
    sys.exit(0)

def main():
    """メイン処理"""
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    try:
        print("Script starting...")
        print(f"Python version: {sys.version}")
        
        validator = GeminiPromptValidator()
        validator.process_excel('/app/input.csv')
        
        print("\nProcessing completed. Press Ctrl+C to exit.")
        while True:
            time.sleep(3600)
            
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Cleaning up...")
    except Exception as e:
        print(f"\nMain script error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()