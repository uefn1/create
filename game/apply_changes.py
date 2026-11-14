#!/usr/bin/env python3
"""AIの出力を指定フォルダ配下に書き込む。"""
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path("game")  # デフォルトの出力先

def normalize_path(path_str: str) -> str:
    """先頭の ./ や base_dir プレフィックスを除去。"""
    p = re.sub(r"^\./", "", path_str.strip())
    # AIが game/index.html のように書いてきた場合の二重プレフィックス防止
    p = re.sub(rf"^{re.escape(BASE_DIR.name)}/", "", p)
    return p

def parse_json(text: str):
    m = re.search(r"
