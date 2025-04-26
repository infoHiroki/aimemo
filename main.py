#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🤖 AI Memo Generator - 文字起こしテキストから議事録を生成するシンプルなツール
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional

# 📚 サードパーティライブラリのインポート
import requests

# 📝 ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ai_memo_generator")


class MemoGenerator:
    """🔄 文字起こしテキストから議事録を生成するクラス"""
    
    def __init__(self, config_path: str = "config.json"):
        """🚀 初期化"""
        self.config = self._load_config(config_path)
        self.config_path = config_path
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """📂 設定ファイルの読み込み"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"⚠️ 設定ファイルの読み込みエラー: {e}")
            # 最小限のデフォルト設定を返す
            return {
                "llm": {
                    "provider": "openai",
                    "api_key": "",
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": 1500
                },
                "templates": {
                    "default": "以下は会議の文字起こしです。これを元に議事録を作成してください。\n\n{transcription}"
                }
            }
    
    def save_config(self):
        """💾 設定を保存"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 設定を保存しました: {self.config_path}")
        except Exception as e:
            logger.error(f"⚠️ 設定の保存に失敗しました: {e}")
    
    def generate_memo_from_file(self, input_file: str, output_file: Optional[str] = None) -> Optional[str]:
        """📄 ファイルから文字起こしを読み込み、議事録を生成"""
        try:
            # 入力ファイル読み込み
            with open(input_file, "r", encoding="utf-8") as f:
                transcription = f.read()
            
            # 出力ファイル名が指定されていない場合
            if output_file is None:
                base_name = os.path.splitext(input_file)[0]
                output_file = f"{base_name}_memo.txt"
            
            # 議事録生成
            memo = self.generate_memo(transcription)
            
            if memo:
                # 生成結果の保存
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(memo)
                logger.info(f"✅ 議事録を保存しました: {output_file}")
                return memo
            
            return None
        
        except FileNotFoundError:
            logger.error(f"❌ ファイルが見つかりません: {input_file}")
            return None
        except Exception as e:
            logger.error(f"⚠️ 議事録生成エラー: {e}")
            return None
    
    def generate_memo(self, transcription: str) -> Optional[str]:
        """🧠 文字起こしテキストから議事録を生成"""
        # テンプレートを取得
        template = self.config["templates"]["default"]
        prompt = template.replace("{transcription}", transcription)
        
        # LLM API呼び出し
        provider = self.config["llm"]["provider"]
        logger.info(f"🔄 LLM API ({provider}) 呼び出し開始")
        
        result = None
        if provider == "openai":
            result = self._call_openai_api(prompt)
        elif provider == "anthropic":
            result = self._call_anthropic_api(prompt)
        elif provider == "google":
            result = self._call_google_api(prompt)
        else:
            logger.error(f"❌ サポートされていないプロバイダー: {provider}")
            return None
        
        if result:
            logger.info(f"✅ LLM API ({provider}) 呼び出し完了: 約{len(result)}文字の応答を受信")
        else:
            logger.error(f"❌ LLM API ({provider}) 呼び出し失敗: 応答なし")
        
        return result
    
    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """🔄 OpenAI APIを呼び出す"""
        api_key = self.config["llm"]["api_key"]
        if not api_key:
            logger.error("🔑 OpenAI APIキーが設定されていません。")
            return None
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            data = {
                "model": self.config["llm"]["model"],
                "messages": [
                    {"role": "system", "content": "あなたは会議の音声文字起こしから議事録を作成する専門家です。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config["llm"]["temperature"],
                "max_tokens": self.config["llm"]["max_tokens"]
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"❌ API呼び出しエラー: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"⚠️ OpenAI API呼び出し例外: {e}")
            return None
    
    def _call_anthropic_api(self, prompt: str) -> Optional[str]:
        """🔄 Anthropic Claude APIを呼び出す"""
        api_key = self.config["llm"]["api_key"]
        if not api_key:
            logger.error("🔑 Anthropic APIキーが設定されていません。")
            return None
        
        try:
            # Claude Messages API形式で呼び出し
            headers = {
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.config["llm"]["model"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": self.config["llm"]["temperature"],
                "max_tokens": self.config["llm"]["max_tokens"]
            }
            
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["content"][0]["text"]
            else:
                logger.error(f"❌ API呼び出しエラー: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"⚠️ Anthropic API呼び出し例外: {e}")
            return None
    
    def _call_google_api(self, prompt: str) -> Optional[str]:
        """🔄 Google Gemini APIを呼び出す"""
        api_key = self.config["llm"].get("google_api_key", "")
        if not api_key:
            logger.error("🔑 Google APIキーが設定されていません。")
            return None
        
        try:
            # モデル名に基づいてAPIパスを構築
            model = self.config["llm"]["model"]
            model_id = model.replace("gemini-", "")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent?key={api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": self.config["llm"]["temperature"],
                    "maxOutputTokens": self.config["llm"]["max_tokens"],
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    if "content" in result["candidates"][0]:
                        if "parts" in result["candidates"][0]["content"]:
                            text_parts = []
                            for part in result["candidates"][0]["content"]["parts"]:
                                if "text" in part:
                                    text_parts.append(part["text"])
                            return "".join(text_parts)
                
                logger.error(f"❌ Google API応答の解析に失敗しました: {result}")
                return None
            else:
                logger.error(f"❌ Google API呼び出しエラー: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"⚠️ Google API呼び出し例外: {e}")
            return None
    
    def set_provider(self, provider: str):
        """🔧 LLMプロバイダーを設定"""
        if provider not in self.config.get("providers", {}):
            logger.warning(f"⚠️ 未知のプロバイダー: {provider}")
        self.config["llm"]["provider"] = provider
    
    def set_model(self, model: str):
        """🔧 LLMモデルを設定"""
        provider = self.config["llm"]["provider"]
        models = self.config.get("providers", {}).get(provider, [])
        if models and model not in models:
            logger.warning(f"⚠️ プロバイダー '{provider}' では未知のモデル: {model}")
        self.config["llm"]["model"] = model
    
    def set_api_key(self, api_key: str):
        """🔑 APIキーを設定"""
        self.config["llm"]["api_key"] = api_key
    
    def set_google_api_key(self, api_key: str):
        """🔑 Google APIキーを設定"""
        self.config["llm"]["google_api_key"] = api_key
    
    def set_temperature(self, temperature: float):
        """🌡️ temperatureパラメータを設定"""
        self.config["llm"]["temperature"] = max(0.0, min(1.0, temperature))
    
    def set_max_tokens(self, max_tokens: int):
        """📏 max_tokensパラメータを設定"""
        self.config["llm"]["max_tokens"] = max(1, max_tokens)
    
    def set_template(self, template_text: str):
        """📝 テンプレートを設定"""
        self.config["templates"]["default"] = template_text


def parse_arguments():
    """🔍 コマンドライン引数のパース"""
    parser = argparse.ArgumentParser(description="🤖 AI Memo Generator - 文字起こしから議事録を生成")
    
    parser.add_argument("--input", "-i", required=True, help="文字起こしテキストファイルのパス")
    parser.add_argument("--output", "-o", help="出力ファイルパス（デフォルト：input_memo.txt）")
    parser.add_argument("--config", "-c", default="config.json", help="設定ファイルパス")
    parser.add_argument("--provider", "-p", help="LLMプロバイダー（openai/anthropic/google）")
    parser.add_argument("--model", "-m", help="使用するモデル名")
    parser.add_argument("--api-key", "-k", help="APIキー")
    parser.add_argument("--google-api-key", "-gk", help="Google APIキー（Googleプロバイダー使用時）")
    parser.add_argument("--temperature", "-t", type=float, help="Temperature値（0.0〜1.0）")
    parser.add_argument("--max-tokens", "-mt", type=int, help="最大トークン数")
    
    return parser.parse_args()


def main():
    """🚀 メインエントリーポイント"""
    # 引数解析
    args = parse_arguments()
    
    # 初期設定
    generator = MemoGenerator(config_path=args.config)
    
    # コマンドライン引数から設定を上書き
    if args.provider:
        generator.set_provider(args.provider)
    
    if args.model:
        generator.set_model(args.model)
    
    if args.api_key:
        generator.set_api_key(args.api_key)
    
    if args.google_api_key:
        generator.set_google_api_key(args.google_api_key)
    
    if args.temperature is not None:
        generator.set_temperature(args.temperature)
    
    if args.max_tokens is not None:
        generator.set_max_tokens(args.max_tokens)
    
    # 入力ファイルが存在するか確認
    if not os.path.isfile(args.input):
        logger.error(f"❌ 入力ファイルが存在しません: {args.input}")
        return 1
    
    # 議事録生成
    result = generator.generate_memo_from_file(args.input, args.output)
    
    if result:
        print("✅ 議事録の生成が完了しました。")
        return 0
    else:
        print("❌ 議事録の生成に失敗しました。詳細はログを確認してください。")
        return 1


if __name__ == "__main__":
    sys.exit(main())