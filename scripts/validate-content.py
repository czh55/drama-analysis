#!/usr/bin/env python3
"""校验 content JSON 的结构完整性，防止渲染出 undefined 或缺失字段。

用法：
  python3 scripts/validate-content.py                              # 校验 content/ 下全部剧集
  python3 scripts/validate-content.py --dir content/yufengxing     # 指定目录
  python3 scripts/validate-content.py --file content/yufengxing/content-e01.json

检查项：
  - 顶层字段齐全（slug/drama/episode/title/meta/overviewLead/scenes/lessons/cast/highlights/foreshadows）
  - scenes 数量 8-12，每个含 id/num/time/title/body/quotes
  - quotes 每场景 2-4 条，且为 {zh, en} 对象（非纯字符串）
  - highlights / foreshadows 必须为 {title, desc} 对象数组（字符串数组会导致渲染 undefined）
  - lessons 含 tag/title/situation/advice(3条)
  - cast 含 name/role/desc
  - time 格式为 MM:SS–MM:SS
  - slug 与文件名一致

退出码：0 全部通过；1 存在错误。
"""
import argparse
import glob
import json
import os
import re
import sys

REQUIRED_TOP = {
    'slug', 'drama', 'episode', 'title', 'subtitle', 'meta',
    'overviewLead', 'overview', 'scenes', 'lessons', 'cast',
    'highlights', 'foreshadows',
}
TIME_RE = re.compile(r'^\d{2}:\d{2}–\d{2}:\d{2}$')
EPISODE_FROM_FILE = re.compile(r'content-e(\d+)\.json$')


def check_file(path):
    errors = []
    try:
        d = json.load(open(path, encoding='utf-8'))
    except Exception as e:
        return [f'{os.path.basename(path)}: JSON 解析失败: {e}']

    fname = os.path.basename(path)
    # slug 结尾与文件名一致（目录名不参与比较，可能不同）
    m = EPISODE_FROM_FILE.search(fname)
    if m:
        ep_file = m.group(1)          # 两位，如 "01"
        ep_file_norm = ep_file.lstrip('0') or '0'
        slug_ep = d.get('slug', '').rsplit('-e', 1)
        if len(slug_ep) != 2 or slug_ep[1] != ep_file:
            errors.append(f'slug={d.get("slug")!r} 集号与文件名 {fname} 不一致')
        if str(d.get('episode')) != ep_file_norm:
            errors.append(f'episode={d.get("episode")!r} 与文件名 {fname} 不一致')

    # 顶层字段
    for k in REQUIRED_TOP:
        if k not in d:
            errors.append(f'缺少顶层字段 {k}')

    # scenes
    scenes = d.get('scenes', [])
    if not (8 <= len(scenes) <= 12):
        errors.append(f'scenes 数量 {len(scenes)} 不在 8-12 范围')
    for i, s in enumerate(scenes, 1):
        for k in ('id', 'num', 'time', 'title', 'body', 'quotes'):
            if k not in s:
                errors.append(f'scenes[{i}] 缺少 {k}')
        if not TIME_RE.match(s.get('time', '')):
            errors.append(f'scenes[{i}] time 格式异常: {s.get("time")!r}')
        qs = s.get('quotes', [])
        if not (2 <= len(qs) <= 4):
            errors.append(f'scenes[{i}] quotes 数量 {len(qs)} 不在 2-4 范围')
        for j, q in enumerate(qs, 1):
            if isinstance(q, str):
                errors.append(f'scenes[{i}] quotes[{j}] 是纯字符串，必须为 {{zh, en}} 对象')
            elif not isinstance(q, dict) or 'zh' not in q or 'en' not in q:
                errors.append(f'scenes[{i}] quotes[{j}] 缺少 zh/en')

    # highlights / foreshadows 必须为 {title, desc} 对象数组
    for field in ('highlights', 'foreshadows'):
        items = d.get(field, [])
        for i, x in enumerate(items, 1):
            if isinstance(x, str):
                errors.append(f'{field}[{i}] 是纯字符串，必须为 {{title, desc}} 对象')
            elif not isinstance(x, dict) or 'title' not in x or 'desc' not in x:
                errors.append(f'{field}[{i}] 缺少 title/desc')

    # lessons
    for i, l in enumerate(d.get('lessons', []), 1):
        for k in ('tag', 'title', 'situation', 'advice'):
            if k not in l:
                errors.append(f'lessons[{i}] 缺少 {k}')
        if len(l.get('advice', [])) < 3:
            errors.append(f'lessons[{i}] advice 不足 3 条')

    # cast
    for i, c in enumerate(d.get('cast', []), 1):
        for k in ('name', 'role', 'desc'):
            if k not in c:
                errors.append(f'cast[{i}] 缺少 {k}')

    return errors


def main():
    ap = argparse.ArgumentParser(description='校验 content JSON 结构')
    group = ap.add_mutually_exclusive_group()
    group.add_argument('--dir', type=str, help='content 目录，校验其中全部 content-e*.json')
    group.add_argument('--file', type=str, help='单个 content JSON')
    args = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if args.file:
        files = [args.file]
    elif args.dir:
        files = sorted(glob.glob(os.path.join(args.dir, 'content-e*.json')))
    else:
        files = sorted(glob.glob(os.path.join(root, 'content', '*', 'content-e*.json')))

    if not files:
        print('未找到 content JSON')
        sys.exit(1)

    all_errors = {}
    for f in files:
        errs = check_file(f)
        if errs:
            all_errors[f] = errs

    n_total = len(files)
    n_ok = n_total - len(all_errors)
    print(f'校验 {n_total} 个文件：{n_ok} 通过，{len(all_errors)} 有问题')
    for f, errs in all_errors.items():
        print(f'\n{f}:')
        for e in errs[:10]:
            print(f'  ✗ {e}')
        if len(errs) > 10:
            print(f'  … 还有 {len(errs)-10} 个错误')
    sys.exit(0 if not all_errors else 1)


if __name__ == '__main__':
    main()
