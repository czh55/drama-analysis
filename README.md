# drama-analysis

电视剧剧集 → Whisper 转录 → 关键情节切分 → 图文并茂的剧情总结 HTML → GitHub Pages。

面向**追剧回顾**：每集输出关键情节叙述、关键台词引用、登场人物、关键看点、伏笔悬念与人生启示，配场景截图。

## 结构

```
drama-analysis/
├── docs/                          # GitHub Pages 网站根目录
│   ├── index.html                 # 剧集索引首页（按剧集分组展示）
│   ├── index.json                 # 剧集总结条目索引
│   ├── WORKFLOW.md                # 处理规范（Automation 执行时读取）
│   ├── *-剧情总结.html            # 每集产出
│   └── images/<slug>/             # hero.jpg + 各场景帧 s1.jpg~sN.jpg
├── 小夫妻/                        # 本地剧集视频（.gitignore 排除，不入库）
└── .gitignore
```

## 处理流程（一集）

1. **提取音频**：`ffmpeg -i <集.mp4> -ar 16000 -ac 1 /tmp/out.wav`
2. **Whisper 转录**：`python3 -m whisper /tmp/out.wav --model small --language Chinese --output_dir /tmp/`
3. **场景切分**：按地点/事件/情绪转折切 8-12 个关键场景，撰写剧情叙述 + 关键台词引用
4. **抽帧配图**：按场景时间点用 ffmpeg 抽关键帧 → `docs/images/<slug>/`
5. **生成 HTML**：单文件图文总结（CSS 内嵌），含剧情梗概/关键情节/人物/看点/伏笔/人生启示
6. **更新 index.json + 提交推送**：新条目追加到 `docs/index.json`，commit 后 push 到 main

## 依赖

- `ffmpeg`
- `python3` + `openai-whisper`
- Node.js（可选，用于脚本）

## GitHub Pages

Settings → Pages → Source：`main` 分支，`/docs` 目录。

详细自动化执行规范见 `docs/WORKFLOW.md`。
