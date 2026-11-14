#!/usr/bin/env python3
"""AIのJSON出力を読み、ファイルに書き込むスクリプト。"""
import json
import re
import sys
from pathlib import Path


def extract_json(text: str) -> dict:
    """テキストから最初のJSONオブジェクトを抽出する。"""
    # ```json ... ``` のコードブロックを優先
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    # 生のJSONを探す
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError("JSONが見つかりませんでした")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: apply_changes.py <ai_output_file>", file=sys.stderr)
        return 1

    output_path = Path(sys.argv[1])
    if not output_path.exists():
        print(f"入力ファイルが存在しません: {output_path}", file=sys.stderr)
        return 1

    text = output_path.read_text(encoding="utf-8")

    try:
        data = extract_json(text)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"JSONパース失敗: {e}", file=sys.stderr)
        print("--- 生の出力 ---", file=sys.stderr)
        print(text[:2000], file=sys.stderr)
        return 1

    files = data.get("files", [])
    if not files:
        print("変更対象ファイルなし（files が空）")
        return 0

    for item in files:
        path_str = item.get("path")
        content = item.get("content")
        if not path_str or content is None:
            print(f"スキップ（path/content欠落）: {item}", file=sys.stderr)
            continue

        # パストラバーサル防止
        target = (Path.cwd() / path_str).resolve()
        if not str(target).startswith(str(Path.cwd().resolve())):
            print(f"危険なパスのためスキップ: {path_str}", file=sys.stderr)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        reason = item.get("reason", "")
        print(f"書き込み: {path_str}  {('(' + reason + ')') if reason else ''}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
