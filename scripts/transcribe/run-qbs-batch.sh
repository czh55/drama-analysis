#!/bin/bash
# 《我的前半生》全剧转录：顺序单进程，避免多进程争抢 CPU 被杀。
# 用法: bash scripts/transcribe/run-qbs-batch.sh [起始集] [结束集]
# 输出: /tmp/wo-de-qian-ban-sheng-e{NN}.json（已存在则跳过）
set -u

VIDEO_DIR="/Users/chenzhiheng/Projects/drama-analysis/我的前半生（2017）"
PREFIX="/tmp/wo-de-qian-ban-sheng-e"
START="${1:-1}"
END="${2:-42}"
LOG="/tmp/wo-de-qian-ban-sheng-transcribe.log"
FW="$(dirname "$0")/fw_transcribe.py"

find_video() {
  local ep="$1" f picked=""
  for f in "$VIDEO_DIR/$ep"*.mp4 "$VIDEO_DIR/$ep"*.mkv; do
    [ -f "$f" ] || continue
    case "$f" in *"(1)"*) [ -n "$picked" ] || picked="$f" ;; *) echo "$f"; return 0 ;; esac
  done
  [ -n "$picked" ] && echo "$picked" && return 0
  return 1
}

echo "[$(date '+%F %T')] batch E$(printf '%02d' $START)-E$(printf '%02d' $END) start" | tee -a "$LOG"

for n in $(seq "$START" "$END"); do
  ep=$(printf "%02d" "$n")
  wav="${PREFIX}${ep}.wav"
  out="${PREFIX}${ep}.json"
  if [ -f "$out" ]; then
    echo "E$ep: 已存在跳过" | tee -a "$LOG"
    continue
  fi
  if [ ! -f "$wav" ]; then
    video=$(find_video "$ep") || { echo "E$ep: 无视频" | tee -a "$LOG"; continue; }
    echo "E$ep: 提取音频 $(date '+%H:%M:%S')" | tee -a "$LOG"
    ffmpeg -y -i "$video" -map 0:a:0 -ar 16000 -ac 1 "$wav" -loglevel error
  fi
  echo "E$ep: 开始转录 $(date '+%H:%M:%S')" >> "$LOG"
  if python3 "$FW" "$wav" "$out" 4 >> "$LOG" 2>&1; then
    echo "E$ep: OK $(date '+%H:%M:%S')" >> "$LOG"
  else
    echo "E$ep: FAIL exit=$? $(date '+%H:%M:%S')" >> "$LOG"
    rm -f "$out"
  fi
done

echo "[$(date '+%F %T')] batch done, json=$(ls -1 ${PREFIX}*.json 2>/dev/null | wc -l | tr -d ' ')/42" | tee -a "$LOG"
