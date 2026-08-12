#!/usr/bin/env python3
"""为一部剧生成 index.json 新条目（输出到 stdout 或文件，由人工合并进 docs/index.json）。

用法：
  python3 scripts/gen-index.py --drama meigui-de-gushi --drama-name "玫瑰的故事" --date 2026-08-09
  python3 scripts/gen-index.py --drama meigui-de-gushi --drama-name "玫瑰的故事" --video "玫瑰的故事" --out /tmp/index-entries.json

说明：
  - 逐集读取 content JSON，生成 {slug,date,drama,episode,title,duration,scenes,html,cover,summary}
  - duration 优先用 content meta 里的「N 分钟」；给了 --video 则用 ffprobe 读真实时长
  - 输出条目打印后请人工核对再合并进 docs/index.json（每部剧一个 date 批次）
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, 'content')


def duration_from_meta(meta):
    """meta 数组含「47 分钟」这类元素"""
    for m in meta:
        mm = re.match(r'^\d+\s*分钟$', m)
        if mm:
            return mm.group(0)
    return None


def duration_from_ffprobe(video_path):
    try:
        r = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'json', video_path],
            capture_output=True, text=True)
        d = json.loads(r.stdout)
        sec = float(d['format']['duration'])
        return f'{int(round(sec / 60))} 分钟'
    except Exception:
        return None


def find_video(video_dir, ep):
    import glob as _glob
    hits = []
    for pat in (f'{ep}*.mp4', f'{ep}*.mkv', f'{ep}*.MP4', f'{ep}*.MKV'):
        hits.extend(_glob.glob(os.path.join(video_dir, pat)))
    for h in hits:
        if os.path.isfile(h) and '(1)' not in os.path.basename(h):
            return h
    for h in hits:
        if os.path.isfile(h):
            return h
    return None


def main():
    ap = argparse.ArgumentParser(description='生成 index.json 条目')
    ap.add_argument('--drama', required=True, help='content 目录名，如 meigui-de-gushi')
    ap.add_argument('--drama-name', required=True, help='index.json 中的剧名，如 玫瑰的故事')
    ap.add_argument('--date', default=None, help='日期，缺省今天')
    ap.add_argument('--video', default=None, help='视频目录，用于 ffprobe 读取真实时长')
    ap.add_argument('--out', default=None, help='输出到文件（缺省打印 stdout）')
    args = ap.parse_args()

    import datetime
    date = args.date or datetime.date.today().isoformat()

    files = sorted(glob.glob(os.path.join(CONTENT_DIR, args.drama, 'content-e*.json')))
    if not files:
        print(f'错误: {args.drama} 下没有 content-e*.json')
        sys.exit(1)

    entries = []
    for f in files:
        d = json.load(open(f, encoding='utf-8'))
        n = int(d['episode'])
        duration = duration_from_meta(d.get('meta', []))
        if args.video:
            video = find_video(args.video, f'{n:02d}')
            if video:
                probe = duration_from_ffprobe(video)
                if probe:
                    duration = probe
        entries.append({
            'slug': d['slug'],
            'date': date,
            'drama': args.drama_name,
            'episode': f'第 {n} 集',
            'title': d['title'],
            'duration': duration or '',
            'scenes': len(d['scenes']),
            'html': f'{args.drama_name}-第{n:02d}集-剧情总结.html',
            'cover': f"images/{d['slug']}/hero.jpg",
            'summary': d['overviewLead'],
        })

    text = json.dumps(entries, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as w:
            w.write(text)
        print(f'生成 {len(entries)} 条 → {args.out}')
    else:
        print(text)


if __name__ == '__main__':
    main()
