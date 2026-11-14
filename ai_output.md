It looks like you're trying to create a simple Minecraft-style web application using HTML and a Python script to apply changes. Below is a more detailed breakdown of how you can achieve this, including some improvements and additional features.

### Directory Structure
```
game/
├── index.html
├── apply_changes.py
└── assets/
```

### index.html
This is the main HTML file that will serve as the home page of your Minecraft-style application.

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Minecraft</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        header {
            background-color: #333;
            color: white;
            text-align: center;
            padding: 1em 0;
        }
        main {
            padding: 20px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        <h1>Welcome to Minecraft!</h1>
    </header>
    <main>
        <div class="container">
            <!-- Content will be inserted here -->
        </div>
    </main>
</body>
</html>
```

### apply_changes.py
This script reads the AI output, parses it, and writes the content to the appropriate files in the `assets` directory.

```python
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
    files = []
    parts = re.split(r"^#{1,6}\s+", text, flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.split("\n", 1)
        if len(lines) < 2:
            continue
        header = lines[0].strip()
        m = re.match(r"(\S+?\.\w+)", header)
        if not m:
            continue
        path = normalize_path(m.group(1))
        body = lines[1]

        fm = re.search(r"```[^\n]*\n(.*?)\n?```", body, re.DOTALL)
        if fm:
            content = fm.group(1)
        else:
            content = re.split(r"\n```", body, maxsplit=1)[0]
            content = re.split(r"\n---", content, maxsplit=1)[0]
            content = content.strip()

        if not content:
            continue
        files.append({"path": path, "content": content.rstrip() + "\n"})

    if files:
        return files

    cb = re.compile(r"```(\w+)\n(.*?)\n```", re.DOTALL)
    for m in cb.finditer(text):
        body = m.group(2)
        first = body.split("\n", 1)[0]
        fm = re.match(r"^\s*(?:#|//|<!--)\s*(\S+\.\w+)", first)
        if fm:
            rest = body.split("\n", 1)[1] if "\n" in body else ""
            files.append({"path": normalize_path(fm.group(1)), "content": rest + "\n"})
    return files

def safe_write(base_dir: Path, path_str: str, content: str):
    base_resolved = (Path.cwd() / base_dir).resolve()
    target = (base_resolved / path_str).resolve()
    if not str(target).startswith(str(base_resolved)):
        print(f"危険なパスのためスキップ: {path_str}", file=sys.stderr)
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"書き込み: {target.relative_to(Path.cwd())} ({len(content)} bytes)")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: apply_changes.py <ai_output_file> [base_dir]", file=sys.stderr)
        return 1

    global BASE_DIR
    output_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        BASE_DIR = Path(sys.argv[2])

    ai_output = output_path.read_text(encoding="utf-8")
    changes = parse_json(ai_output) or parse_markdown(ai_output)

    if changes:
        for change in changes:
            safe_write(BASE_DIR, change["path"], change["content"])

    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### Explanation

1. **Directory Structure**: 
   - `index.html`: The main HTML file for the Minecraft-style application.
   - `apply_changes.py`: The Python script that processes AI output and writes files to the `assets` directory.

2. **index.html**:
   - Basic HTML structure with a header and a main content area.
   - A `.container` class for centering content.

3. **apply_changes.py**:
   - **normalize_path**: Removes leading `./` and `base_dir` prefixes to prevent path traversal.
   - **parse_json**: Searches for JSON blocks within the AI output and parses them.
   - **parse_markdown**: Uses regular expressions to parse Markdown blocks, extracting paths and contents.
   - **safe_write**: Writes content to files, ensuring the path is safe and creating necessary directories.
   - **main**: Reads the AI output, parses it, and writes changes to the `assets` directory.

### Running the Script
To run the script, save it to `apply_changes.py`, ensure `index.html` and any assets are in the `game` directory, and execute:

```bash
python apply_changes.py output.json
```

This will parse the `output.json` file and apply the changes to the `assets` directory. Adjust the `output.json` format as needed to match the structure of your AI output.

