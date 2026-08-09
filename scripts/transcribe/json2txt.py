#!/usr/bin/env python3
"""把 whisper/faster-whisper 转录 JSON 转成带时间戳的纯文本，便于撰写 content JSON 时对照。

用法：
  python3 scripts/transcribe/json2txt.py <in.json> [out.txt]     # 单文件
  python3 scripts/transcribe/json2txt.py --dir /tmp/transcripts  # 批量（跳过已转换）
"""
import argparse
import glob
import json
import os
import sys


def convert(src, dst=None):
    if dst is None:
        dst = src.replace('.json', '.txt')
    if os.path.exists(dst):
        print(f'skip {os.path.basename(dst)}')
        return
    d = json.load(open(src, encoding='utf-8'))
    lines = []
    for seg in d.get('segments', []):
        m = int(seg['start'] // 60)
        s = int(seg['start'] % 60)
        lines.append(f"[{m:02d}:{s:02d}] {seg['text'].strip()}")
    with open(dst, 'w', encoding='utf-8') as w:
        w.write('\n'.join(lines))
    print(f'wrote {os.path.basename(dst)} ({len(lines)} 段)')


def main():
    ap = argparse.ArgumentParser(description='转录 JSON -> 带时间戳 txt')
    ap.add_argument('inputs', nargs='*', help='json 文件或 --dir 批量')
    ap.add_argument('--dir', help='批量处理该目录下所有转录 JSON')
    args = ap.parse_args()

    if args.dir:
        files = sorted(glob.glob(os.path.join(args.dir, '*.json')))
        if not files:
            print(f'{args.dir} 下没有 JSON')
            sys.exit(1)
        for f in files:
            convert(f)
        return
    if not args.inputs:
        print('用法: json2txt.py <in.json> [out.txt] 或 --dir <目录>')
        sys.exit(1)
    convert(args.inputs[0], args.inputs[1] if len(args.inputs) > 1 else None)


if __name__ == '__main__':
    main()
