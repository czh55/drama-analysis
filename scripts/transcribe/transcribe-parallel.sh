#!/bin/bash
# 并行转录：ffmpeg 提取音频 + faster-whisper 转录，最多 2 个并发进程。
# 用法: bash scripts/transcribe/transcribe-parallel.sh <视频目录> <输出前缀> <起始集号> <结束集号>
# 例:   bash scripts/transcribe/transcribe-parallel.sh "玫瑰的故事" /tmp/meigui-e 1 38
# 输出: /tmp/meigui-e01.wav /tmp/meigui-e01.json ... （已存在的 json 自动跳过，可断点续跑）
set -u

VIDEO_DIR="${1:?视频目录}"
PREFIX="${2:?输出前缀，如 /tmp/meigui-e}"
START="${3:-1}"
END="${4:-38}"

for n in $(seq "$START" "$END"); do
  ep=$(printf "%02d" "$n")
  wav="${PREFIX}${ep}.wav"
  out="${PREFIX}${ep}.json"
  if [ -f "$out" ]; then echo "E$ep: 已存在跳过"; continue; fi
  if [ ! -f "$wav" ]; then
    video=""
    for ext in mp4 mkv; do
      [ -f "$VIDEO_DIR/$ep.$ext" ] && video="$VIDEO_DIR/$ep.$ext" && break
    done
    if [ -z "$video" ]; then echo "E$ep: 无视频"; continue; fi
    ffmpeg -y -i "$video" -ar 16000 -ac 1 "$wav" -loglevel error
  fi
  echo "E$ep: 开始转录 $(date '+%H:%M:%S')"
  python3 "$(dirname "$0")/fw_transcribe.py" "$wav" "$out" 4 &
  while [ "$(jobs -rp | wc -l | tr -d ' ')" -ge 2 ]; do sleep 5; done
done
wait
echo "ALL TRANSCRIBE DONE $(date '+%Y-%m-%d %H:%M:%S')"
