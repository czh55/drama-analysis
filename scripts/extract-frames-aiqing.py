#!/usr/bin/env python3
"""为爱情没有神话已下载集抽取关键帧：每集 hero.jpg + 每场景 s{N}.jpg"""
import json, glob, os, subprocess

CONTENT_DIR = '/Users/chenzhiheng/Projects/drama-analysis/content/aiqing-meiyou-shenhua'
VIDEO_DIR = '/Users/chenzhiheng/Projects/drama-analysis/A 爱情-没有-神话'
IMG_DIR = '/Users/chenzhiheng/Projects/drama-analysis/docs/images'

def parse_time(t):
    """MM:SS 或 HH:MM:SS -> 秒"""
    parts = [int(x) for x in t.split(':')]
    if len(parts) == 2:
        return parts[0]*60 + parts[1]
    if len(parts) == 3:
        return parts[0]*3600 + parts[1]*60 + parts[2]
    return 0

def extract(video, ts, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run(
        ['ffmpeg', '-y', '-ss', str(ts), '-i', video, '-frames:v', '1', '-vf', 'scale=1920:-1', '-q:v', '2', out],
        capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out):
        print(f'  失败: {os.path.basename(out)} @ {ts}s: {r.stderr[-200:]}')
        return False
    return True

def scene_midpoint(t):
    a, b = t.split('–')
    return (parse_time(a) + parse_time(b)) // 2

files = sorted(glob.glob(f'{CONTENT_DIR}/content-e*.json'))
for f in files:
    ep = f.split('content-e')[1].split('.')[0]
    video = f'{VIDEO_DIR}/{ep}.mp4'
    if not os.path.exists(video):
        print(f'E{ep}: 视频不存在 {video}')
        continue
    d = json.load(open(f))
    slug = d['slug']
    outdir = f'{IMG_DIR}/{slug}'
    print(f'E{ep} ({slug}):')
    hero_ts = 40
    extract(video, hero_ts, f'{outdir}/hero.jpg')
    for s in d['scenes']:
        ts = scene_midpoint(s['time'])
        extract(video, ts, f'{outdir}/{s["id"]}.jpg')
    print(f'  完成: {len(d["scenes"])} 场景帧 + hero')
print('ALL DONE')
