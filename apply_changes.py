#!/usr/bin/env python3
"""AIの出力（JSON / Markdown）をファイルに書き込む。開きフェンスが無くても対応。"""
import json
import re
import sys
from pathlib import Path


def parse_json(text: str):
    """```json ブロック、または "files" を含む生JSONを抽出。"""
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass
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
    """### path 見出しで分割し、フェンス有無を問わず内容を取り出す。"""
    files = []
    # ヘッダで分割（### など）
    parts = re.split(r"^#{1,6}\s+", text, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.split("\n", 1)
        if len(lines) < 2:
            continue
        header = lines[0].strip()
        # パスを抽出（先頭の ./ は除去）
        m = re.match(r"(\S+?\.\w+)", header)
        if not m:
            continue
        path = re.sub(r"^\./", "", m.group(1))
        body = lines[1]

        # フェンスがある場合は中身を取り出す
        fm = re.search(r"```[^\n]*\n(.*?)\n?```", body, re.DOTALL)
        if fm:
            content = fm.group(1)
        else:
            # 開きフェンスが無い：閉じフェンス or `--- ... ---` までを本文扱い
            content = re.split(r"\n```", body, maxsplit=1)[0]
            content = re.split(r"\n---", content, maxsplit=1)[0]
            content = content.strip()

        if not content:
            continue
        files.append({"path": path, "content": content.rstrip() + "\n"})

    if files:
        return files

    # フォールバック: コードブロック先頭コメントでパス判定
    cb = re.compile(r"```(\w+)\n(.*?)\n```", re.DOTALL)
    for m in cb.finditer(text):
        body = m.group(2)
        first = body.split("\n", 1)[0]
        fm = re.match(r"^\s*(?:#|//|<!--)\s*(\S+\.\w+)", first)
        if fm:
            rest = body.split("\n", 1)[1] if "\n" in body else ""
            files.append({"path": re.sub(r"^\./", "", fm.group(1)), "content": rest + "\n"})
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

    data = parse_json(text)
    if data is not None:
        files = data.get("files", [])
        print(f"JSON形式で {len(files)} ファイル検出")
        for item in files:
            if item.get("path") and item.get("content") is not None:
                safe_write(item["path"], item["content"])
        return 0

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
