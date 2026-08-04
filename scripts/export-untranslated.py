#!/usr/bin/env python3
"""导出所有 content JSON 中未翻译的关键台词（用于批量翻译）。

用法：
  python3 scripts/export-untranslated.py --dir /tmp/wenxin2-trans
  python3 scripts/export-untranslated.py --dir /tmp/wenxin2-trans --out /tmp/untranslated.txt
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="导出未翻译的关键台词")
    parser.add_argument("--dir", type=Path, required=True, help="content JSON 目录")
    parser.add_argument("--out", type=Path, help="输出文件（默认打印）")
    args = parser.parse_args()

    lines: list[str] = []
    total = 0
    for f in sorted(args.dir.glob("content-*.json")):
        content = json.loads(f.read_text(encoding="utf-8"))
        un: list[str] = []
        for scene in content.get("scenes", []):
            for q in scene.get("quotes", []):
                if isinstance(q, str):
                    un.append(q)
        if un:
            lines.append(f"# {f.name} ({content.get('slug')})")
            lines.extend(f"  {q}" for q in un)
            total += len(un)
    lines.insert(0, f"# 共 {total} 条未翻译台词")
    text = "\n".join(lines) + "\n"

    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(f"已导出 {total} 条到 {args.out}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
