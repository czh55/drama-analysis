#!/usr/bin/env python3
"""通用关键帧抽取：每集 hero.jpg（第 2 场景中点）+ 每场景 s{N}.jpg。

用法：
  python3 scripts/extract-frames.py --drama meigui-de-gushi            # content 目录名
  python3 scripts/extract-frames.py --drama meigui-de-gushi --video "玫瑰的故事"
  python3 scripts/extract-frames.py --drama meigui-de-gushi --ep 01   # 单集
  python3 scripts/extract-frames.py --drama meigui-de-gushi --video "玫瑰的故事" --ep 01

--video 缺省时依次尝试：content 目录名、项目根下同名目录；
视频文件按 {NN}.mp4 / {NN}.mkv 查找。
"""
import argparse
import glob
import json
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, 'content')
IMG_DIR = os.path.join(ROOT, 'docs', 'images')

def parse_time(t):
    """MM:SS 或 HH:MM:SS -> 秒"""
    parts = [int(x) for x in t.split(':')]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

def fmt_hms(sec):
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    if h > 0:
        return f'{h:02d}:{m:02d}:{s:02d}'
    return f'{m:02d}:{s:02d}'

def extract(video, ts, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run(
        ['ffmpeg', '-y', '-ss', str(ts), '-i', video, '-frames:v', '1',
         '-vf', 'scale=1920:-1', '-q:v', '2', out],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print(f'  失败: {os.path.basename(out)} @ {fmt_hms(ts)}: {r.stderr[-200:]}')
        return False
    return True

def scene_midpoint(t):
    a, b = t.split('–')
    return (parse_time(a) + parse_time(b)) // 2

def find_video(video_dir, ep):
    """按 NN* 通配匹配，优先选不带 "(1)" 的重复副本（支持 "01 4K.mp4" / "01..mp4" / "01-4K.高码率.mkv"）"""
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

def auto_find_video_dir(ep):
    """扫描项目根下所有目录，找含 {ep}.mp4/.mkv 的目录（视频目录名常为中文，与 content 拼音名不同）"""
    if not os.path.isdir(ROOT):
        return None
    for name in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, name)
        if not os.path.isdir(d):
            continue
        if find_video(d, ep):
            return d
    return None

def main():
    ap = argparse.ArgumentParser(description='抽取关键帧：每集 hero + 每场景帧')
    ap.add_argument('--drama', required=True, help='content 目录名，如 meigui-de-gushi')
    ap.add_argument('--video', default=None, help='视频目录（缺省自动扫描项目根下含视频的目录）')
    ap.add_argument('--ep', default=None, help='只处理单集（如 01），缺省处理全部')
    args = ap.parse_args()

    content_dir = os.path.join(CONTENT_DIR, args.drama)
    files = sorted(glob.glob(os.path.join(content_dir, 'content-e*.json')))
    if args.ep:
        ep_arg = args.ep.replace('e', '').zfill(2)
        files = [f for f in files if os.path.basename(f).split('content-e')[1].split('.')[0] == ep_arg]

    if not files:
        print(f'错误: {content_dir} 下没有 content-e*.json')
        return 1

    # 用第一个文件定位视频目录
    first_ep = os.path.basename(files[0]).split('content-e')[1].split('.')[0]
    if args.video:
        video_dir = args.video
    else:
        video_dir = auto_find_video_dir(first_ep)
    if video_dir is None:
        print(f'错误: 找不到视频目录，请用 --video 指定（按 {first_ep}.mp4/.mkv 扫描项目根未命中）')
        return 1

    for f in files:
        ep = os.path.basename(f).split('content-e')[1].split('.')[0]
        video = find_video(video_dir, ep)
        if video is None:
            print(f'E{ep}: 视频不存在于 {video_dir}')
            continue
        d = json.load(open(f))
        slug = d['slug']
        outdir = os.path.join(IMG_DIR, slug)
        print(f'E{ep} ({slug}):')
        scenes = d['scenes']
        hero_scene = scenes[1] if len(scenes) > 1 else scenes[0]
        hero_ts = scene_midpoint(hero_scene['time'])
        extract(video, hero_ts, os.path.join(outdir, 'hero.jpg'))
        for s in scenes:
            ts = scene_midpoint(s['time'])
            extract(video, ts, os.path.join(outdir, f'{s["id"]}.jpg'))
        print(f'  完成: {len(scenes)} 场景帧 + hero')
    print('ALL DONE')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
