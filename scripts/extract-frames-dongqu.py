#!/usr/bin/env python3
"""为冬去春来全部 32 集抽取关键帧：每集 hero.jpg + 每场景 s{N}.jpg"""
import json, glob, os, subprocess, sys

CONTENT_DIR = '/Users/chenzhiheng/Projects/drama-analysis/content/dongqu-chunlai'
VIDEO_DIR = '/Users/chenzhiheng/Projects/drama-analysis/DONGQU'
IMG_DIR = '/Users/chenzhiheng/Projects/drama-analysis/docs/images'

def parse_time(t):
    """MM:SS 或 HH:MM:SS -> 秒"""
    parts = [int(x) for x in t.split(':')]
    if len(parts) == 2:
        return parts[0]*60 + parts[1]
    if len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
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
        ['ffmpeg', '-y', '-ss', str(ts), '-i', video, '-frames:v', '1', '-vf', 'scale=1920:-1', '-q:v', '2', out],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print(f'  失败: {os.path.basename(out)} @ {fmt_hms(ts)}: {r.stderr[-200:]}')
        return False
    return True

def scene_midpoint(t):
    a, b = t.split('–')
    return (parse_time(a) + parse_time(b)) // 2

files = sorted(glob.glob(f'{CONTENT_DIR}/content-e*.json'))
for f in files:
    ep = f.split('content-e')[1].split('.')[0]
    video = f'{VIDEO_DIR}/{ep}.mkv'
    if not os.path.exists(video):
        print(f'E{ep}: 视频不存在 {video}')
        continue
    d = json.load(open(f))
    slug = d['slug']
    outdir = f'{IMG_DIR}/{slug}'
    print(f'E{ep} ({slug}):')
    # hero: 取片头，避开片头水印（用第一个场景的中点前 30s 或 40s 固定值）
    hero_ts = 40
    extract(video, hero_ts, f'{outdir}/hero.jpg')
    # 场景帧
    for s in d['scenes']:
        ts = scene_midpoint(s['time'])
        extract(video, ts, f'{outdir}/{s["id"]}.jpg')
    print(f'  完成: {len(d["scenes"])} 场景帧 + hero')
print('ALL DONE')
