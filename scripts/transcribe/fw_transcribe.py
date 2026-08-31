#!/usr/bin/env python3
"""faster-whisper 转录：把 WAV 音频转成带时间戳的 JSON。

用法：
  python3 scripts/transcribe/fw_transcribe.py <wav> <out.json> [threads]

输出 JSON：{text, segments:[{start,end,text}], language}
比原版 whisper 快 3-5 倍（CPU int8），且规避 whisper 在 Apple Silicon MPS 上的 NaN 崩溃。

推荐并行策略：2 进程 × 4 线程（Intel Mac），参考 transcribe-parallel.sh。
"""
import json
import os
import sys
import time

# 优先使用本地模型缓存，避免 huggingface_hub 联网检查触发代理 403
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from faster_whisper import WhisperModel

wav, out = sys.argv[1], sys.argv[2]
threads = int(sys.argv[3]) if len(sys.argv) > 3 else 4

t0 = time.time()
model = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=threads)
print(f"model loaded in {time.time()-t0:.1f}s", flush=True)

t1 = time.time()
# vad_filter=True：跳过片头片尾音乐，避免 condition_on_previous_text
# 在无语音片段上陷入「詞曲/重复幻觉」死循环（本剧实测会卡死单集）。
segments, info = model.transcribe(
    wav, language="zh", vad_filter=True, beam_size=5, condition_on_previous_text=False
)
segs = []
for seg in segments:
    segs.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
data = {
    "text": "\n".join(s["text"] for s in segs),
    "segments": segs,
    "language": "zh",
}
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False)
dur = time.time() - t1
print(f"DONE segments={len(segs)} elapsed={dur:.1f}s ({dur/60:.1f}min)", flush=True)
