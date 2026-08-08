# 剧集 → 剧情总结 处理规范

本文档定义「从剧集视频到 GitHub Pages 剧情总结」的完整处理规范，供人工执行或 Cursor Automation 触发时严格参照执行。**不要跳过或合并任何步骤。**

> **自动化环境约束（重要）**：剧集视频是本地网盘文件（`小夫妻/` 目录，约 13G，已被 `.gitignore` 排除），**不会也不应推送到 GitHub**。Cursor Automation 的 cloud agent 无法访问本地文件系统，因此**输入源必须由本地提供**——automation 只能做「本地已产出 HTML 后，负责索引更新 + 提交推送」的半自动模式，不能像 language_paraphrase 那样从在线 URL 全自动下载处理。

```
Task Progress:
- [ ] 1. 解析入口，得到剧集信息（剧名 + 集数 + 本地视频路径）
- [ ] 2. ffmpeg 提取音频
- [ ] 3. Whisper 转录（带时间戳 json）
- [ ] 4. 场景切分 + 撰写剧情内容（content JSON 入库）
- [ ] 5. 抽帧配图
- [ ] 6. 关键台词英文翻译 + 批量生成朗读 MP3
- [ ] 7. 生成 HTML（图文总结，含朗读功能）
- [ ] 8. 质量自检
- [ ] 9. 更新 index.json
- [ ] 10. Git 提交并推送到 main（**必须**，Pages 才能展示）
- [ ] 11. 清理临时文件
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

## 触发方式

### 方式 A：人工触发（当前主路径）

本地环境执行完整 11 步流程（本机已有 ffmpeg / whisper / node / edge-tts）。

### 方式 B：Cursor Automation（半自动，待配置）

由于视频是本地文件，automation **只负责下游步骤**，输入源由人工在本地生成：

1. 人工本地完成 Step 2–7（转录/切分/抽帧/翻译/生成 HTML）
2. 通过 automation 触发（Webhook / GitHub Issue / cron），payload 提供 `drama` + `episode` 等元信息
3. automation 执行 Step 8–11（自检 / 更新 index.json / push / 清理）

> 若未来改为视频托管在可下载的远程位置，可扩展为全自动模式（从 URL 下载 → 转录 → 总结 → 部署）。

### 重复处理检查

automation 处理前必须检查 `docs/index.json` 是否已有相同 `drama + episode`，有则跳过。

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

### quotes 格式（必须）

`quotes` 使用**中英对象数组**，`en` 为必填（供英文朗读）：

```json
"quotes": [
  {
    "zh": "「我们要知晓最差的情况，但抱有好的期待。」",
    "en": "We should know the worst-case scenario, but hold good expectations."
  }
]
```

> 兼容旧格式：纯字符串（只有 `zh`）也能渲染，但没有朗读按钮。**新内容必须写成对象。**

### highlights / foreshadows 格式（必须）

顶层 `highlights`（关键看点）与 `foreshadows`（伏笔悬念）必须是**对象数组**，每个对象含 `title`（3–12 字短标题）与 `desc`（40–100 字展开描述）：

```json
"highlights": [
  { "title": "一只会说话的鸡", "desc": "小桃道别后，一人一鸡隔着门对上了话；行云一句「我就是在玩你」，揭穿「他早能听懂沈璃」的真相。" }
],
"foreshadows": [
  { "title": "行云绝非普通人", "desc": "自称凡人病秧子的行云，能听懂凤凰说话、一眼买下凤凰——这位「凡人大夫」的真实身份疑云重重。" }
]
```

> **禁止写成纯字符串数组**（如 `"highlights": ["整句话..."]`）——渲染脚本取 `h.title` / `h.desc`，字符串会导致页面显示 undefined。

### 转录纠错（必做）

Whisper 中文同音字错误必须先行校正（专有名词按语境/剧集资料修正，角色名可参考演职员表）。

### content JSON 入库（必须）

撰写完成的 content JSON 存入 **`content/{drama-拼音}/content-e{NN}.json`**（如 `content/wenxin2/content-e01.json`），随 Git 提交入库。**禁止只放在 /tmp**——content 是唯一可重渲染的源（HTML 由它生成、MP3 由它生成），丢失后该集将无法再升级模板或补朗读功能。目录按当前已有剧集：`content/wenxin2/`、`content/xiao-fuqi/`。

---

## Step 5：抽帧配图

**hero.jpg 取该集第 2 个场景的中点**（只有 1 个场景时用第 1 个场景中点）——每集场景切分天然不同，封面为差异化剧情画面。**禁止固定取早期片头帧（如 40s）**，否则各集封面视觉雷同。

```bash
# 每场景取代表时间点（场景时间中点），抽 1920 宽关键帧
ffmpeg -y -ss {场景中点} -i "{video}" -frames:v 1 docs/images/{slug}/s{N}.jpg
# hero：第 2 个场景中点（示例用 python 计算，或直接用脚本）
python3 -c "a,b='06:10–09:50'.split('–'); m=(int(a.split(':')[0])*60+int(a.split(':')[1])+int(b.split(':')[0])*60+int(b.split(':')[1]))//2; print(m)"
ffmpeg -y -ss {第2场景中点} -i "{video}" -frames:v 1 docs/images/{slug}/hero.jpg
```

- hero.jpg 取第 2 个场景中点，避开片头 Logo
- 每场景一帧 `s1.jpg`~`sN.jpg`，数量与场景数一致
- 若抽帧为黑帧/广告帧，换时间点重抽
- 批量处理优先复用 `scripts/extract-frames-*.py`（已内置 hero 第 2 场景中点逻辑）

---

## Step 6：关键台词英文翻译 + 批量生成朗读 MP3

### 6a. 导出未翻译台词

```bash
python3 scripts/export-untranslated.py --dir content/wenxin2 --out /tmp/untranslated.txt
```

输出格式为按文件分组的 `「中文原文」` 列表，供人工或 LLM 批量翻译。

### 6b. 翻译并写回（维护 content JSON）

翻译为 JSON 映射文件（key 为 content 文件路径，value 为「中文原文 → 英文译文」的字典），再写回：

```bash
python3 scripts/apply-quote-en.py /tmp/translate-batch.json
```

脚本会把匹配的 `quotes` 字符串升级为 `{zh, en}` 对象。**对照译文必须与 content 原文逐字一致**（含「」与空格），否则匹配不上；遗漏的会打印在输出里，需人工补。

### 6c. 批量生成英文朗读 MP3

```bash
python3 scripts/generate-quote-audio.py --dir content/wenxin2
python3 scripts/generate-quote-audio.py --dir content/xiao-fuqi
```

- 使用 `edge-tts`（`en-US-JennyNeural`），产出 `docs/audio/{slug}/{scene_id}-{idx:02d}.mp3`
- 命名强制两位索引（如 `s1-01.mp3`），与 HTML 中 `data-audio` 一致
- 已存在的文件自动跳过（可重复执行）
- 结束后核对：日志显示 `完成: N/N 条`，且 HTML 中每个 `data-audio` 引用都能找到对应文件

---

## Step 7：生成 HTML

产出 `docs/{drama}-第{NN}集-剧情总结.html`，单文件、CSS 内嵌。页面模块顺序固定如下（与现行第 1 集 HTML 一致）：

1. **Hero 头部**：剧名 + 集号 + 封面 hero.jpg + chips（时长/场景数/总集数）+ 朗读工具栏（语速选择、停止朗读）
2. **Sticky 剧情地图侧边栏**：S1–Sn 锚点导航 + 底部「人生启示」入口（琥珀色徽章，`#lessons`）
3. **剧情梗概**：一句话导读 + 全集概述
4. **人生启示**：6 张「剧情情境 → 处世方法」卡片（标注源自场景，如「源自 S5 · 校园风波」），置于关键情节之前
5. **关键情节**：场景卡片（截图 + 编号 + 时间 + 情节叙述 + 关键台词引用）
   - 台词区显示中文 `quote-zh` + 英文 `quote-en`，英文旁带 **▶ 朗读** 按钮（`data-audio` 指向 MP3）
   - 英文长单词渲染为可点击发音的 `.pronounce-word`（Web Speech API 单词朗读）
6. **登场人物**：grid 卡片（姓名 + 身份 + 本集表现）
7. **关键看点**：grid 卡片
8. **伏笔悬念**：grid 卡片

生成命令：

```bash
node render-recap.mjs content/{drama}/content-e{NN}.json docs/{drama}-第{NN}集-剧情总结.html
```

参考样式：teal 配色、Hero 渐变、卡片式布局、响应式（桌面双列/移动单列）。页脚标注「ASR 专有名词已按语境校正」。

---

## Step 8：质量自检

**先跑校验脚本（必做）**：

```bash
python3 scripts/validate-content.py --dir content/{剧名}
# 校验通过（退出码 0）才继续；失败项按提示修正后重跑
```

脚本检查：顶层字段齐全、scenes 8–12 且 quotes 2–4 条为 `{zh, en}` 对象、**highlights/foreshadows 必须为 `{title, desc}` 对象数组（纯字符串数组会导致页面渲染 undefined）**、lessons 含 advice≥3、cast 字段齐全、slug 集号与文件名一致。

> 若脚本报出「highlights/foreshadows 是纯字符串」错误，必须把字符串改写为 `{title, desc}` 对象：title 用 3–12 字短标题，desc 用 40–100 字展开描述。

再逐项人工核对：

- [ ] 产出为 HTML 单文件，浏览器可正常渲染
- [ ] 场景数 8–12，每个有时间范围和截图
- [ ] 每个场景有情节叙述 + 关键台词引用
- [ ] 剧情描述忠于转录内容、无编造
- [ ] hero.jpg + 每场景 s{N}.jpg 齐全，数量与场景一致
- [ ] hero.jpg 为剧情画面（第 2 场景中点），各集封面视觉上不重复
- [ ] 页面含剧情梗概 / 人生启示 / 关键情节 / 登场人物 / 关键看点 / 伏笔悬念 6 大模块，顺序与 Step 7 一致
- [ ] 人生启示 6 张卡片每张含「情境 + 方法」结构
- [ ] 侧边栏含场景锚点导航 + 人生启示入口
- [ ] 每条关键台词含中文 + 英文，英文旁有朗读按钮
- [ ] content JSON 中每条台词为 `{zh, en}` 对象（无纯字符串残留）
- [ ] content JSON 中 `highlights`/`foreshadows` 均为 `{title, desc}` 对象（页面关键看点/伏笔悬念处无 undefined）
- [ ] `docs/audio/{slug}/` 下 MP3 与 HTML `data-audio` 引用一一对应、无缺失
- [ ] 页脚标注「ASR 专有名词已按语境校正」

---

## Step 9：更新 index.json

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

> `docs/index.html` 首页是**动态读取 `index.json` 渲染**的，新增条目无需改首页代码，只需更新 index.json 后 push。

---

## Step 10：Git 提交并推送到 main（**必须**）

> GitHub Pages 从 `main` 的 `docs/` 部署。

```bash
git add docs/ content/
git commit -m "drama: {剧名} 第{NN}集剧情总结"
git pull origin main --rebase
git push -u origin main
```

> `docs/audio/`（MP3，~2MB/集）与 `content/`（content JSON）**必须随 docs/ 一起提交**，缺一不可：HTML 引用音频、未来重渲染依赖 content。

最终变更必须在 `origin/main`。

---

## Step 11：清理

```bash
rm /tmp/{slug}.wav /tmp/{slug}.json /tmp/{slug}.srt  # 临时转录件
```

> **content JSON 已入库（`content/` 目录），不要删除**；临时转录件可删。生成脚本入库保留（`scripts/` 下）。

---

## 约束

- 视频文件（`小夫妻/`、`*.mp4`、`*.pdf`）**永不入库**（.gitignore 排除）
- **content JSON 必须入库**（`content/{剧名}/`），不入库视为未完成
- 不修改 `.gitignore`
- 同 `drama + episode` 不重复处理
- 主产出是剧情图文总结 HTML，不是视频文件
- 关键台词 `quotes` 一律为 `{zh, en}` 对象（纯字符串视为未完成）
- 朗读 MP3（`docs/audio/`）随 HTML 一起提交，缺失会导致页面朗读功能失效
- 页脚标注「ASR 专有名词已按语境校正」
- 页面模块顺序固定（人生启示在关键情节之前），新增集数不得擅自调整
