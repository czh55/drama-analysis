# 剧集 → 剧情总结 处理规范

本文档定义「从剧集视频到 GitHub Pages 剧情总结」的完整处理规范，供人工执行或 Cursor Automation 触发时严格参照执行。**不要跳过或合并任何步骤。**

```
Task Progress:
- [ ] 1. 解析入口，得到剧集信息（剧名 + 集数 + 本地视频路径）
- [ ] 2. ffmpeg 提取音频
- [ ] 3. Whisper 转录（带时间戳 json）
- [ ] 4. 场景切分 + 撰写剧情内容
- [ ] 5. 抽帧配图
- [ ] 6. 生成 HTML（图文总结）
- [ ] 7. 质量自检
- [ ] 8. 更新 index.json
- [ ] 9. Git 提交并推送到 main（**必须**，Pages 才能展示）
- [ ] 10. 清理临时文件
```

---

## 入口

每次处理的输入统一为：

```json
{
  "drama": "小夫妻",
  "episode": 1,
  "video": "/Users/chenzhiheng/Projects/drama-analysis/小夫妻/01.mp4"
}
```

| 字段 | 必填 | 说明 |
|------|------|------|
| `drama` | 是 | 剧名（决定首页分组与 slug 前缀） |
| `episode` | 是 | 集号（决定文件名与展示） |
| `video` | 是 | 本地视频文件绝对路径 |

若剧集为网盘下载的伪装文件（`.pdf` 实为 `.mp4`），先重命名为 `NN.mp4` 再处理。

每个 `drama + episode` 只处理一次（检查 `docs/index.json` 是否已有相同条目）。

---

## Step 1：解析入口

从触发源提取 `drama` / `episode` / `video`。video 默认位于 `小夫妻/{episode:02d}.mp4`。

slug 规则：`{drama-拼音}-e{episode:02d}`，如 `xiao-fuqi-e01`。

---

## Step 2：提取音频

```bash
ffmpeg -y -i "{video}" -ar 16000 -ac 1 /tmp/{slug}.wav
```

---

## Step 3：Whisper 转录

```bash
export PATH="$PATH:/Users/chenzhiheng/Library/Python/3.9/bin:/opt/homebrew/bin"
python3 -m whisper /tmp/{slug}.wav --model small --language Chinese --output_dir /tmp/
```

必须保留带时间戳产物（`{slug}.json` / `{slug}.srt`），场景切分依赖时间轴。

---

## Step 4：场景切分 + 剧情撰写（核心）

读取转录稿（优先 `.json` 段落时间戳），按以下规则切分 **8–12 个关键场景**：

- 地点/活动切换
- 情绪转折 / 矛盾爆发点
- 叙事节点（角色介绍、冲突、和解、预告）

每个场景必须包含：

| 字段 | 说明 |
|------|------|
| `scene_id` | S1, S2… |
| `time_range` | 如 `00:12–00:48` |
| `scene_title` | 中文短标题 |
| `body` | 2–4 段情节叙述（忠于转录、可润色） |
| `quotes` | 2–4 条关键台词引用 |

### 转录纠错（必做）

Whisper 中文同音字错误必须先行校正（专有名词按语境/剧集资料修正，角色名可参考演职员表）。

---

## Step 5：抽帧配图

```bash
# 每场景取代表时间点，抽 1920 宽关键帧
ffmpeg -y -ss {time} -i "{video}" -frames:v 1 docs/images/{slug}/s{N}.jpg
ffmpeg -y -ss 00:06:30 -i "{video}" -frames:v 1 docs/images/{slug}/hero.jpg
```

- hero.jpg 取片头画面
- 每场景一帧 `s1.jpg`~`sN.jpg`，数量与场景数一致
- 若抽帧为黑帧/广告帧，换时间点重抽

---

## Step 6：生成 HTML

产出 `docs/{drama}-第{NN}集-剧情总结.html`，单文件、CSS 内嵌。必须包含 6 个固定区域：

1. **Hero 头部**：剧名 + 集号 + 封面 hero.jpg + chips（时长/场景数/总集数）
2. **Sticky 剧情地图侧边栏**：S1–Sn 锚点导航
3. **剧情梗概**：一句话导读 + 全集概述
4. **关键情节**：场景卡片（截图 + 编号 + 时间 + 情节叙述 + 关键台词引用）
5. **登场人物 / 关键看点 / 伏笔悬念**：grid 卡片
6. **人生启示**：6 张「剧情情境 → 处世方法」卡片（标注源自场景）

参考样式：teal 配色、Hero 渐变、卡片式布局、响应式（桌面双列/移动单列）。

---

## Step 7：质量自检

- [ ] 产出为 HTML 单文件，浏览器可正常渲染
- [ ] 场景数 8–12，每个有时间范围和截图
- [ ] 每个场景有情节叙述 + 关键台词引用
- [ ] 剧情描述忠于转录内容、无编造
- [ ] hero.jpg + 每场景 s{N}.jpg 齐全，数量与场景一致
- [ ] 人生启示卡片每张含「情境 + 方法」结构
- [ ] 页面含剧情梗概/关键情节/人物/看点/伏笔/人生启示 6 大模块

---

## Step 8：更新 index.json

将新条目追加到 `docs/index.json`：

```json
{
  "slug": "xiao-fuqi-e01",
  "date": "YYYY-MM-DD",
  "drama": "小夫妻",
  "episode": "第 1 集",
  "title": "短标题",
  "duration": "45 分钟",
  "scenes": 11,
  "html": "小夫妻-第01集-剧情总结.html",
  "cover": "images/xiao-fuqi-e01/hero.jpg",
  "summary": "本集一句话梗概"
}
```

失败项加 `"error": true` 与 `error_message`。

---

## Step 9：Git 提交并推送到 main（**必须**）

> GitHub Pages 从 `main` 的 `docs/` 部署。

```bash
git add docs/
git commit -m "drama: {剧名} 第{NN}集剧情总结"
git pull origin main --rebase
git push -u origin main
```

最终变更必须在 `origin/main`。

---

## Step 10：清理

```bash
rm /tmp/{slug}.wav /tmp/{slug}.json /tmp/{slug}.srt  # 临时转录件
```

生成脚本用完即删（不入库）。

---

## 约束

- 视频文件（`小夫妻/`、`*.mp4`、`*.pdf`）**永不入库**（.gitignore 排除）
- 不修改 `.gitignore`
- 同 `drama + episode` 不重复处理
- 主产出是剧情图文总结 HTML，不是视频文件
- 页脚标注「ASR 专有名词已按语境校正」
