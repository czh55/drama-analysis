#!/usr/bin/env python3
"""将翻译 JSON 应用到一个或多个 content JSON 的关键台词。

翻译 JSON 格式：
{
  "/tmp/wenxin2-trans/content-e02.json": {
    "「中文原文」": "English translation",
    ...
  }
}

用法：
  python3 scripts/apply-quote-en.py translations.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def apply_to(content_path: Path, table: dict[str, str]) -> tuple[int, int, list[str]]:
    content = json.loads(content_path.read_text(encoding="utf-8"))
    updated = 0
    missing: list[str] = []
    for scene in content.get("scenes", []):
        new_quotes: list = []
        for q in scene.get("quotes", []):
            if isinstance(q, dict):
                new_quotes.append(q)
                continue
            en = table.get(q)
            if not en:
                missing.append(f"{scene.get('id')}: {q}")
                new_quotes.append(q)
                continue
            new_quotes.append({"zh": q, "en": en})
            updated += 1
        scene["quotes"] = new_quotes
    content_path.write_text(
        json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return updated, len(table), missing


def main() -> None:
    parser = argparse.ArgumentParser(description="应用关键台词英文翻译")
    parser.add_argument("translations", type=Path, help="翻译 JSON 文件路径")
    args = parser.parse_args()

    data = json.loads(args.translations.read_text(encoding="utf-8"))
    total_updated = 0
    for path_str, table in data.items():
        p = Path(path_str)
        if not p.exists():
            print(f"  (skip {path_str}: 文件不存在)")
            continue
        updated, total, missing = apply_to(p, table)
        total_updated += updated
        print(f"{p.name}: 更新 {updated} 条")
        for m in missing:
            print(f"  ! 缺失: {m}")
    print(f"\n完成: 共更新 {total_updated} 条")
    sys.exit(0)


if __name__ == "__main__":
    main()
