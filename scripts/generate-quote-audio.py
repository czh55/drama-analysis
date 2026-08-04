#!/usr/bin/env python3
"""
从剧情总结 content JSON 提取关键台词英文翻译，用 edge-tts 生成逐条 MP3。

用法：
  python3 scripts/generate-quote-audio.py --file /tmp/wenxin2-trans/content-e01.json
  python3 scripts/generate-quote-audio.py --dir /tmp/wenxin2-trans
  python3 scripts/generate-quote-audio.py --dir /tmp/xqf-trans
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
AUDIO_DIR = DOCS / "audio"

EN_VOICE = "en-US-JennyNeural"
MAX_CHUNK_LEN = 2000


def collect_quotes(content: dict) -> list[tuple[str, int, str]]:
    """返回 [(scene_id, idx, english_text), ...]"""
    items: list[tuple[str, int, str]] = []
    for scene in content.get("scenes", []):
        sid = scene.get("id", "")
        for i, q in enumerate(scene.get("quotes", []), 1):
            if isinstance(q, dict) and q.get("en"):
                items.append((sid, i, q["en"]))
    return items


def split_text(text: str, max_len: int = MAX_CHUNK_LEN) -> list[str]:
    if len(text) <= max_len:
        return [text]
    chunks: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        if len(para) > max_len:
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(para), max_len):
                chunks.append(para[i : i + max_len])
            continue
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= max_len:
            current = candidate
        else:
            if current:
                chunks.append(current.strip())
            current = para
    if current:
        chunks.append(current.strip())
    return chunks


async def _synthesize_chunk(text: str, output: Path, voice: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output))


def _concat_mp3(files: list[Path], output: Path) -> None:
    import subprocess

    list_file = output.parent / f".concat_{output.stem}.txt"
    try:
        with open(list_file, "w", encoding="utf-8") as f:
            for p in files:
                f.write(f"file '{p.resolve()}'\n")
        subprocess.run(
            [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file), "-c", "copy", str(output),
            ],
            check=True,
            capture_output=True,
        )
    finally:
        if list_file.exists():
            list_file.unlink()


async def synthesize_speech(text: str, output_path: Path, voice: str) -> bool:
    chunks = split_text(text)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if len(chunks) == 1:
        await _synthesize_chunk(chunks[0], output_path, voice)
        return output_path.exists()

    temp_files: list[Path] = []
    try:
        for i, chunk in enumerate(chunks):
            tmp = output_path.parent / f".tmp_{output_path.stem}_{i}.mp3"
            await _synthesize_chunk(chunk, tmp, voice)
            temp_files.append(tmp)
        _concat_mp3(temp_files, output_path)
        return output_path.exists()
    finally:
        for f in temp_files:
            if f.exists():
                f.unlink()


async def generate_one(slug: str, scene_id: str, idx: int, text: str) -> bool:
    out = AUDIO_DIR / slug / f"{scene_id}-{idx:02d}.mp3"
    if out.exists():
        return True
    ok = await synthesize_speech(text, out, EN_VOICE)
    if not ok:
        print(f"  ✗ FAIL {out}")
    return ok


async def process_content(content_path: Path, verbose: bool = True) -> tuple[int, int]:
    content = json.loads(content_path.read_text(encoding="utf-8"))
    slug = content.get("slug", content_path.stem)
    quotes = collect_quotes(content)
    if not quotes:
        if verbose:
            print(f"  (skip {content_path.name}: 无英文台词)")
        return 0, 0
    if verbose:
        print(f"\n{content_path.name} → audio/{slug}/ ({len(quotes)} 条)")
    results = await asyncio.gather(
        *(generate_one(slug, sid, idx, text) for sid, idx, text in quotes)
    )
    ok = sum(1 for r in results if r)
    if verbose:
        print(f"  ✓ {ok}/{len(quotes)} 条 (已有 {len(quotes) - ok} 条跳过/失败)")
    return ok, len(quotes)


async def main() -> None:
    parser = argparse.ArgumentParser(description="生成关键台词英文朗读 MP3")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", type=Path, help="单个 content JSON")
    group.add_argument("--dir", type=Path, help="目录，处理其中所有 content-*.json")
    args = parser.parse_args()

    if args.file:
        files = [args.file]
    else:
        files = sorted(args.dir.glob("content-*.json"))

    if not files:
        print("未找到 content JSON")
        sys.exit(1)

    total_ok = total_all = 0
    for f in files:
        ok, n = await process_content(f)
        total_ok += ok
        total_all += n

    print(f"\n{'='*40}\n完成: {total_ok}/{total_all} 条音频\n{'='*40}")
    sys.exit(0 if total_ok == total_all else 1)


if __name__ == "__main__":
    asyncio.run(main())
