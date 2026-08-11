#!/bin/bash
# 并行转录：ffmpeg 提取音频 + faster-whisper 转录，可指定并发进程数。
# 用法: bash scripts/transcribe/transcribe-parallel.sh <视频目录> <输出前缀> <起始集号> <结束集号> [并发数]
# 例:   bash scripts/transcribe/transcribe-parallel.sh "玫瑰的故事" /tmp/meigui-e 1 38 2
# 输出: /tmp/meigui-e01.wav /tmp/meigui-e01.json ... （已存在的 json 自动跳过，可断点续跑）
# 视频文件名支持任意后缀（如 "01 4K.mp4" / "01..mp4" / "01.mp4"），按 NN* 通配匹配
#
# 并发控制说明：用 PID 数组 + kill -0 检查存活，而非 `jobs -rp`
# （jobs 在管道/非交互环境下不可靠，会导致失控 fork 过度占用 CPU）。
set -u

VIDEO_DIR="${1:?视频目录}"
PREFIX="${2:?输出前缀，如 /tmp/meigui-e}"
START="${3:-1}"
END="${4:-38}"
CONC="${5:-2}"

find_video() {
  local ep="$1"
  for f in "$VIDEO_DIR/$ep"*.mp4 "$VIDEO_DIR/$ep"*.mkv "$VIDEO_DIR/$ep"*.MP4 "$VIDEO_DIR/$ep"*.MKV; do
    [ -f "$f" ] && echo "$f" && return 0
  done
  return 1
}

# 清理已结束的 pid，返回存活数量
alive_count() {
  local alive=0 p
  for p in "${PIDS[@]:-}"; do
    [ -z "$p" ] && continue
    if kill -0 "$p" 2>/dev/null; then
      alive=$((alive + 1))
    fi
  done
  echo "$alive"
}

PIDS=()

for n in $(seq "$START" "$END"); do
  ep=$(printf "%02d" "$n")
  wav="${PREFIX}${ep}.wav"
  out="${PREFIX}${ep}.json"
  if [ -f "$out" ]; then echo "E$ep: 已存在跳过"; continue; fi
  if [ ! -f "$wav" ]; then
    video=$(find_video "$ep") || { echo "E$ep: 无视频"; continue; }
    ffmpeg -y -i "$video" -ar 16000 -ac 1 "$wav" -loglevel error
  fi
  # 等并发槽位空出（CONC=0 表示不限制）
  if [ "$CONC" -gt 0 ]; then
    while [ "$(alive_count)" -ge "$CONC" ]; do sleep 10; done
  fi
  echo "E$ep: 开始转录 $(date '+%H:%M:%S')"
  python3 "$(dirname "$0")/fw_transcribe.py" "$wav" "$out" 4 &
  PIDS+=("$!")
done

wait
echo "ALL TRANSCRIBE DONE $(date '+%Y-%m-%d %H:%M:%S')"
