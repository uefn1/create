#!/usr/bin/env python3
"""AIの出力（Markdownコードブロック or JSON）をファイルに書き込む。"""
import json
import re
import sys
from pathlib import Path


def parse_json(text: str):
    """まず ```json ブロック、次に生JSONを試す。"""
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
    # 生JSONを行ごとに試す（{{ テンプレート誤認を避けるため "files" を要求）
    for m in re.finditer(r"\{.*?\}", text, re.DOTALL):
        chunk = m.group(0)
        if '"files"' not in chunk:
            continue
        try:
            return json.loads(chunk)
        except json.JSONDecodeError:
            continue
    return None


def parse_markdown(text: str):
    """### filename や <!-- filename --> に続くコードブロックを抽出。"""
    files = []
    # パターン1: ### filename の後に ```lang ... ```
    pattern = re.compile(
        r"^#{1,6}\s+(\S+\.\w+)\s*\n+```[^\n]*\n(.*?)\n```",
        re.DOTALL | re.MULTILINE,
    )
    for m in pattern.finditer(text):
        files.append({"path": m.group(1), "content": m.group(2)})

    # パターン2: コードブロック内の先頭コメントでパス指定
    # ```python
    # # main.py
    # ...
    # ```
    if not files:
        cb = re.compile(r"```(\w+)\n(.*?)\n```", re.DOTALL)
        for m in cb.finditer(text):
            body = m.group(2)
            first = body.split("\n", 1)[0]
            fm = re.match(r"^\s*(?:#|//|<!--)\s*(\S+\.\w+)", first)
            if fm:
                # 先頭コメント行を除去
                body = body.split("\n", 1)[1] if "\n" in body else ""
                files.append({"path": fm.group(1), "content": body})
    return files


def safe_write(path_str: str, content: str):
    target = (Path.cwd() / path_str).resolve()
    if not str(target).startswith(str(Path.cwd().resolve())):
        print(f"危険なパスのためスキップ: {path_str}", file=sys.stderr)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"書き込み: {path_str} ({len(content)} bytes)")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: apply_changes.py <ai_output_file>", file=sys.stderr)
        return 1
    output_path = Path(sys.argv[1])
    if not output_path.exists():
        print(f"入力ファイルが存在しません: {output_path}", file=sys.stderr)
        return 1

    text = output_path.read_text(encoding="utf-8")

    # 1) JSON を試す
    data = parse_json(text)
    if data is not None:
        files = data.get("files", [])
        print(f"JSON形式で {len(files)} ファイル検出")
        for item in files:
            if item.get("path") and item.get("content") is not None:
                safe_write(item["path"], item["content"])
        return 0

    # 2) Markdown を試す
    files = parse_markdown(text)
    if files:
        print(f"Markdown形式で {len(files)} ファイル検出")
        for item in files:
            safe_write(item["path"], item["content"])
        return 0

    print("ファイルを抽出できませんでした。生の出力を表示します:", file=sys.stderr)
    print(text[:3000], file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
