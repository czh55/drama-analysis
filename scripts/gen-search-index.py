#!/usr/bin/env python3
"""生成全站搜索索引 docs/search-index.json（首页中英文全文搜索的数据源）。

用法：
  python3 scripts/gen-search-index.py            # 扫描 content/ 全部剧集，输出 docs/search-index.json

说明：
  - 每集一条记录，含可点击的锚点单元（units）：
      scene   -> 单场景（id=sN，含标题/正文/中英文台词），锚点 #sN
      section -> 人生启示/关键看点/伏笔悬念/登场人物（合并整段），锚点 #lessons/#highlights/#foreshadowing/#cast
  - html / cover 字段与 docs/index.json 的命名约定保持一致。
  - 仅依赖 Python 标准库。
"""
import glob
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT_DIR = os.path.join(ROOT, 'content')
DOCS_DIR = os.path.join(ROOT, 'docs')
OUT_FILE = os.path.join(DOCS_DIR, 'search-index.json')

# 剧名 -> html 文件名前缀（content 目录名是拼音，docs 下 HTML 用中文剧名）
def html_prefix_for_drama(drama):
    return drama


def _norm(s):
    """把文本压平为单行，便于前端匹配与高亮上下文。"""
    if s is None:
        return ''
    return re.sub(r'\s+', ' ', str(s)).strip()


def quote_text(q):
    """一条 quote -> 中英文文本。q 可能是 {zh,en} 对象（新格式）。"""
    if isinstance(q, dict):
        parts = []
        if q.get('zh'):
            parts.append(q['zh'])
        if q.get('en'):
            parts.append(q['en'])
        return ' ||| '.join(parts)
    return _norm(q)


def build_record(cpath):
    d = json.load(open(cpath, encoding='utf-8'))
    slug = d.get('slug', '')
    drama = d.get('drama', '')
    episode = d.get('episode', '')
    title = d.get('title', '')
    ep_num = re.sub(r'\D', '', str(episode))

    # html 文件名：docs/《剧名》-第NN集-剧情总结.html（集号两位补零，与 docs/index.json 一致）
    html = f'{drama}-第{ep_num.zfill(2)}集-剧情总结.html' if ep_num else ''

    # episode 展示字段与 docs/index.json 保持一致：「第 N 集」
    episode_disp = f'第 {ep_num} 集' if ep_num else str(episode)
    cover = f'images/{slug}/hero.jpg' if slug else ''

    units = []

    # 场景单元（锚点 #sN）
    for s in d.get('scenes', []):
        sid = s.get('id', '')
        parts = [s.get('title', '')]
        parts.extend(_norm(b) for b in (s.get('body') or []))
        for q in (s.get('quotes') or []):
            qt = quote_text(q)
            if qt:
                parts.append(qt)
        units.append({
            'id': sid,
            'kind': 'scene',
            'label': s.get('title', f'场景 {sid}'),
            'text': ' ||| '.join(parts),
        })

    # 段落单元（锚点 #lessons/#highlights/#foreshadowing/#cast）
    section_defs = [
        ('lessons', '人生启示', d.get('lessons') or [],
         lambda l: [l.get('tag', ''), l.get('title', ''), l.get('situation', '')] + list(l.get('advice') or [])),
        ('highlights', '关键看点', d.get('highlights') or [],
         lambda h: [h.get('title', ''), h.get('desc', '')]),
        ('foreshadowing', '伏笔悬念', d.get('foreshadows') or [],
         lambda f: [f.get('title', ''), f.get('desc', '')]),
        ('cast', '登场人物', d.get('cast') or [],
         lambda c: [c.get('name', ''), c.get('role', ''), c.get('desc', '')]),
    ]
    for anchor, label, items, fn in section_defs:
        parts = []
        for it in items:
            parts.extend(_norm(p) for p in fn(it))
        units.append({
            'id': anchor,
            'kind': 'section',
            'label': label,
            'text': ' ||| '.join(p for p in parts if p),
        })

    return {
        'slug': slug,
        'drama': drama,
        'episode': episode_disp,
        'title': title,
        'html': html,
        'cover': cover,
        'units': units,
    }


def main():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, '*', 'content-e*.json')))
    if not files:
        print('错误: content/ 下没有 content-e*.json')
        return 1

    records = [build_record(f) for f in files]
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(OUT_FILE, 'w', encoding='utf-8') as fh:
        json.dump(records, fh, ensure_ascii=False, separators=(',', ':'))

    total_units = sum(len(r['units']) for r in records)
    print(f'生成 {len(records)} 条索引（{total_units} 个锚点单元）→ {OUT_FILE}')
    size = os.path.getsize(OUT_FILE)
    print(f'文件大小: {size/1024/1024:.2f} MB')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
