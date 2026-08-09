#!/usr/bin/env python3
"""检查每个 HTML 的 data-audio 引用是否都能找到对应 MP3 文件。

用法：
  python3 scripts/check-audio-refs.py                          # 检查 docs/ 下全部 HTML
  python3 scripts/check-audio-refs.py --drama 玫瑰的故事        # 只查某部剧的 HTML

退出码：0 全部通过；1 存在缺失引用。
"""
import argparse
import glob
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(ROOT, 'docs')

AUDIO_RE = re.compile(r'data-audio="([^"]+)"')


def main():
    ap = argparse.ArgumentParser(description='检查 data-audio 引用与 MP3 文件一致性')
    ap.add_argument('--drama', default=None, help='只检查含该剧名的 HTML')
    args = ap.parse_args()

    audio_files = glob.glob(os.path.join(DOCS, 'audio', '*', '*.mp3'))
    existing = {os.path.basename(f) for f in audio_files}

    pattern = f'{DOCS}/{args.drama}-第*.html' if args.drama else f'{DOCS}/*-第*.html'
    htmls = sorted(glob.glob(pattern))
    if not htmls:
        print(f'未找到匹配 HTML: {pattern}')
        return 1

    problems = []
    total_refs = 0
    for h in htmls:
        html = open(h, encoding='utf-8').read()
        refs = AUDIO_RE.findall(html)
        total_refs += len(refs)
        missing = [r for r in refs if os.path.basename(r) not in existing]
        if missing:
            problems.append((os.path.basename(h), missing))

    if problems:
        for f, miss in problems:
            print(f'缺文件 {f}: {miss}')
        return 1
    print(f'检查 {len(htmls)} 个 HTML，全部 {total_refs} 条 data-audio 引用均能找到对应 MP3')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
