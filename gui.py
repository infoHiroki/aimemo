#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🖥️ AI Memo Generator GUI - 文字起こしからAIメモを生成するシンプルなGUIインターフェース
"""

import os
import sys
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import Dict, Any, Optional, List

# 🔄 メインモジュールをインポート
try:
    from main import MemoGenerator
except ImportError:
    print("❌ main.pyが見つかりません。同じディレクトリに配置してください。")
    sys.exit(1)


class MemoGeneratorGUI:
    """🖥️ AI Memo Generator GUIクラス"""
    
    def __init__(self, root: tk.Tk):
        """🚀 初期化"""
        self.root = root
        self.root.title("🤖 AI Memo Generator")
        self.root.geometry("1000x800")
        
        # 設定の読み込み
        self.config_path = "config.json"
        self.config = self._load_config()
        
        # MemoGeneratorインスタンス
        self.generator = MemoGenerator(config_path=self.config_path)
        
        # ファイルリスト
        self.input_files = []
        
        # UI構築
        self.build_ui()
    
    def _load_config(self) -> Dict[str, Any]:
        """📂 設定ファイルの読み込み"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # デフォルト設定を返す
            return {
                "llm": {
                    "provider": "openai",
                    "openai_api_key": "",
                    "anthropic_api_key": "",
                    "google_api_key": "",
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": 1500
                },
                "templates": {
                    "default": "以下は会議の文字起こしです。これを元にAIメモを作成してください。\n\n{transcription}"
                },
                "providers": {
                    "openai": ["gpt-3.5-turbo", "gpt-4o-mini"],
                    "anthropic": ["claude-3-haiku-20240307"],
                    "google": ["gemini-pro"]
                }
            }
    
    def save_config(self):
        """💾 設定を保存"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("エラー", f"設定ファイルの保存に失敗しました: {e}")
            return False
    
    def build_ui(self):
        """🏗️ UIの構築"""
        # タブコントロール
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # メインタブ（ファイル処理）
        main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(main_tab, text="処理")
        
        # 設定タブ
        settings_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(settings_tab, text="設定")
        
        # 各タブのUI構築
        self.build_main_tab(main_tab)
        self.build_settings_tab(settings_tab)
    
    def build_main_tab(self, parent):
        """🏗️ メインタブのUI構築"""
        # 入力セクション
        input_frame = ttk.LabelFrame(parent, text="📄 入力ファイル", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ファイルリストとスクロールバー
        file_frame = ttk.Frame(input_frame)
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.file_listbox = tk.Listbox(file_frame, selectmode=tk.EXTENDED, height=5)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # ファイル操作ボタン
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="📂 ファイル追加", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ 選択削除", command=self.remove_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🧹 すべて削除", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # 出力ディレクトリ
        output_frame = ttk.Frame(input_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="出力ディレクトリ:").pack(side=tk.LEFT, padx=5)
        self.output_dir_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, width=50)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(output_frame, text="参照...", command=self.browse_output_dir).pack(side=tk.LEFT, padx=5)
        
        # LLM設定（簡易表示）
        llm_frame = ttk.LabelFrame(parent, text="🤖 現在の設定", padding=10)
        llm_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(llm_frame, text="プロバイダー:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.current_provider_var = tk.StringVar(value=self.config["llm"]["provider"])
        ttk.Label(llm_frame, textvariable=self.current_provider_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(llm_frame, text="モデル:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.current_model_var = tk.StringVar(value=self.config["llm"]["model"])
        ttk.Label(llm_frame, textvariable=self.current_model_var).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(llm_frame, text="APIキー:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 現在選択されているプロバイダーのAPIキー状態を表示
        provider = self.config["llm"]["provider"]
        api_key = ""
        if provider == "openai":
            api_key = self.config["llm"].get("openai_api_key", "")
        elif provider == "anthropic":
            api_key = self.config["llm"].get("anthropic_api_key", "")
        elif provider == "google":
            api_key = self.config["llm"].get("google_api_key", "")
        
        masked_key = "設定済み" if api_key else "未設定"
        self.current_api_key_var = tk.StringVar(value=masked_key)
        ttk.Label(llm_frame, textvariable=self.current_api_key_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # ボタンセクション
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=10)
        
        self.generate_button = ttk.Button(button_frame, text="🚀 AIメモ生成", command=self.generate_memos)
        self.generate_button.pack(side=tk.RIGHT, padx=5)
        
        # 結果表示エリア
        result_frame = ttk.LabelFrame(parent, text="📝 処理結果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, wrap=tk.WORD, height=10)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def build_settings_tab(self, parent):
        """🏗️ 設定タブのUI構築"""
        # プロバイダー設定
        provider_frame = ttk.LabelFrame(parent, text="🔌 LLMプロバイダー設定", padding=10)
        provider_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(provider_frame, text="プロバイダー:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.provider_var = tk.StringVar(value=self.config["llm"]["provider"])
        providers = list(self.config.get("providers", {}).keys())
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.provider_var, values=providers, state="readonly", width=15)
        provider_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        provider_combo.bind("<<ComboboxSelected>>", self.update_model_list)
        
        ttk.Label(provider_frame, text="モデル:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.model_var = tk.StringVar(value=self.config["llm"]["model"])
        self.model_combo = ttk.Combobox(provider_frame, textvariable=self.model_var, state="readonly", width=20)
        self.model_combo.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # APIキー設定
        api_frame = ttk.LabelFrame(parent, text="🔑 APIキー設定", padding=10)
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="OpenAI APIキー:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.openai_api_key_var = tk.StringVar(value=self.config["llm"].get("openai_api_key", ""))
        openai_api_key_entry = ttk.Entry(api_frame, textvariable=self.openai_api_key_var, width=50, show="*")
        openai_api_key_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(api_frame, text="Anthropic APIキー:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.anthropic_api_key_var = tk.StringVar(value=self.config["llm"].get("anthropic_api_key", ""))
        anthropic_api_key_entry = ttk.Entry(api_frame, textvariable=self.anthropic_api_key_var, width=50, show="*")
        anthropic_api_key_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(api_frame, text="Google APIキー:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.google_api_key_var = tk.StringVar(value=self.config["llm"].get("google_api_key", ""))
        google_api_key_entry = ttk.Entry(api_frame, textvariable=self.google_api_key_var, width=50, show="*")
        google_api_key_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # パラメータ設定
        param_frame = ttk.LabelFrame(parent, text="⚙️ パラメータ設定", padding=10)
        param_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(param_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.temp_var = tk.DoubleVar(value=self.config["llm"]["temperature"])
        temp_scale = ttk.Scale(param_frame, from_=0.0, to=1.0, variable=self.temp_var, orient=tk.HORIZONTAL, length=200)
        temp_scale.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        temp_label = ttk.Label(param_frame, textvariable=self.temp_var, width=5)
        temp_label.grid(row=0, column=2, padx=5, pady=5)
        
        ttk.Label(param_frame, text="最大トークン数:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_tokens_var = tk.IntVar(value=self.config["llm"]["max_tokens"])
        tokens_spinbox = ttk.Spinbox(param_frame, from_=100, to=4000, textvariable=self.max_tokens_var, width=10)
        tokens_spinbox.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # テンプレート設定
        template_frame = ttk.LabelFrame(parent, text="📝 テンプレート設定", padding=10)
        template_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(template_frame, text="プロンプトテンプレート:").pack(anchor=tk.W, padx=5, pady=5)
        
        self.template_text = scrolledtext.ScrolledText(template_frame, wrap=tk.WORD, height=10)
        self.template_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.template_text.insert(tk.END, self.config["templates"]["default"])
        
        ttk.Label(template_frame, text="使用可能なプレースホルダー: {transcription} - 文字起こしテキスト").pack(anchor=tk.W, padx=5, pady=2)
        
        # 保存ボタン
        save_frame = ttk.Frame(parent)
        save_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(save_frame, text="💾 設定を保存", command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        
        # 初期化
        self.update_model_list()
    
    def update_model_list(self, event=None):
        """🔄 プロバイダーに基づいてモデルリストを更新"""
        provider = self.provider_var.get()
        models = self.config.get("providers", {}).get(provider, [])
        
        self.model_combo["values"] = models
        if models and self.model_var.get() not in models:
            self.model_var.set(models[0])
    
    def save_settings(self):
        """💾 設定を保存"""
        # 既存の設定を更新
        self.config["llm"]["provider"] = self.provider_var.get()
        self.config["llm"]["model"] = self.model_var.get()
        self.config["llm"]["openai_api_key"] = self.openai_api_key_var.get()
        self.config["llm"]["anthropic_api_key"] = self.anthropic_api_key_var.get()
        self.config["llm"]["google_api_key"] = self.google_api_key_var.get()
        self.config["llm"]["temperature"] = self.temp_var.get()
        self.config["llm"]["max_tokens"] = self.max_tokens_var.get()
        
        # テンプレートを更新
        template_text = self.template_text.get(1.0, tk.END).strip()
        if template_text:
            self.config["templates"]["default"] = template_text
        
        # 設定を保存
        if self.save_config():
            # 現在の設定表示を更新
            self.current_provider_var.set(self.config["llm"]["provider"])
            self.current_model_var.set(self.config["llm"]["model"])
            
            # 現在選択されているプロバイダーのAPIキー状態を表示
            provider = self.config["llm"]["provider"]
            api_key = ""
            if provider == "openai":
                api_key = self.config["llm"]["openai_api_key"]
            elif provider == "anthropic":
                api_key = self.config["llm"]["anthropic_api_key"]
            elif provider == "google":
                api_key = self.config["llm"]["google_api_key"]
            
            masked_key = "設定済み" if api_key else "未設定"
            self.current_api_key_var.set(masked_key)
            
            # MemoGeneratorインスタンスを更新
            self.generator = MemoGenerator(config_path=self.config_path)
            
            messagebox.showinfo("情報", "設定を保存しました")
            
            # メインタブに切り替え
            self.notebook.select(0)
    
    def add_files(self):
        """📂 ファイルの追加"""
        file_paths = filedialog.askopenfilenames(
            filetypes=[("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")]
        )
        
        if file_paths:
            for path in file_paths:
                if path not in self.input_files:
                    self.input_files.append(path)
                    self.file_listbox.insert(tk.END, os.path.basename(path))
    
    def remove_files(self):
        """🗑️ 選択ファイルの削除"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
            
        # 逆順にインデックスを処理（削除時にインデックスがずれるため）
        for i in sorted(selected_indices, reverse=True):
            del self.input_files[i]
            self.file_listbox.delete(i)
    
    def clear_files(self):
        """🧹 すべてのファイルを削除"""
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
    
    def browse_output_dir(self):
        """📂 出力ディレクトリの選択"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
    
    def update_generator_settings(self):
        """🔄 UIの設定をMemoGeneratorに適用"""
        provider = self.config["llm"]["provider"]
        self.generator.set_provider(provider)
        self.generator.set_model(self.config["llm"]["model"])
        
        # プロバイダーに対応するAPIキーを設定
        if provider == "openai":
            self.generator.set_api_key(self.config["llm"]["openai_api_key"], provider)
        elif provider == "anthropic":
            self.generator.set_api_key(self.config["llm"]["anthropic_api_key"], provider)
        elif provider == "google":
            self.generator.set_api_key(self.config["llm"]["google_api_key"], provider)
        
        self.generator.set_temperature(self.config["llm"]["temperature"])
        self.generator.set_max_tokens(self.config["llm"]["max_tokens"])
        self.generator.set_template(self.config["templates"]["default"])
    
    def generate_memos(self):
        """🚀 複数ファイルのAIメモ生成処理を実行"""
        if not self.input_files:
            messagebox.showerror("エラー", "処理するファイルを追加してください。")
            return
        
        output_dir = self.output_dir_var.get()
        if output_dir and not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("エラー", f"出力ディレクトリの作成に失敗しました: {e}")
                return
        
        # 設定を更新
        self.update_generator_settings()
        
        # UI状態の更新
        self.generate_button.config(state=tk.DISABLED, text="⏳ 生成中...")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, f"⏳ AIメモ生成を開始します（{len(self.input_files)}ファイル）\n")
        self.root.update()
        
        # 別スレッドで生成処理を実行
        threading.Thread(target=self._generate_all_in_thread, args=(output_dir,), daemon=True).start()
    
    def _generate_all_in_thread(self, output_dir: str):
        """🧵 別スレッドでの複数ファイル処理"""
        results = []
        
        for i, input_file in enumerate(self.input_files):
            try:
                # 進捗を更新
                self.root.after(0, lambda idx=i, file=input_file: 
                               self._update_progress(idx, len(self.input_files), file))
                
                # 出力ファイル名の決定
                if output_dir:
                    base_name = os.path.splitext(os.path.basename(input_file))[0]
                    output_file = os.path.join(output_dir, f"{base_name}_memo.txt")
                else:
                    base_name = os.path.splitext(input_file)[0]
                    output_file = f"{base_name}_memo.txt"
                
                # AIメモ生成
                result = self.generator.generate_memo_from_file(input_file, output_file)
                
                results.append((input_file, output_file, result is not None))
            except Exception as e:
                results.append((input_file, None, False))
                self.root.after(0, lambda msg=f"ファイル処理エラー ({os.path.basename(input_file)}): {e}": 
                               self._append_result(msg))
        
        # 処理完了時のUI更新
        self.root.after(0, lambda: self._show_final_results(results))
    
    def _update_progress(self, current: int, total: int, file: str):
        """📊 進捗状況の更新"""
        self.result_text.insert(tk.END, f"📄 処理中: {os.path.basename(file)} ({current+1}/{total})\n")
        self.result_text.see(tk.END)
        self.root.update()
    
    def _append_result(self, message: str):
        """📝 結果のテキストエリアに追加"""
        self.result_text.insert(tk.END, f"{message}\n")
        self.result_text.see(tk.END)
        self.root.update()
    
    def _show_final_results(self, results: List[tuple]):
        """📊 最終結果の表示"""
        self.generate_button.config(state=tk.NORMAL, text="🚀 AIメモ生成")
        
        success_count = sum(1 for _, _, success in results if success)
        fail_count = len(results) - success_count
        
        self.result_text.insert(tk.END, f"\n{'='*50}\n")
        self.result_text.insert(tk.END, f"✅ 処理完了: 成功 {success_count} / 失敗 {fail_count} / 合計 {len(results)}\n\n")
        
        if success_count > 0:
            self.result_text.insert(tk.END, "📄 生成されたAIメモ:\n")
            for input_file, output_file, success in results:
                if success:
                    self.result_text.insert(tk.END, f"- {os.path.basename(input_file)} → {output_file}\n")
        
        if fail_count > 0:
            self.result_text.insert(tk.END, "\n❌ 失敗したファイル:\n")
            for input_file, _, success in results:
                if not success:
                    self.result_text.insert(tk.END, f"- {os.path.basename(input_file)}\n")
        
        self.result_text.see(tk.END)


def main():
    """🚀 メインエントリーポイント"""
    root = tk.Tk()
    app = MemoGeneratorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()