#!/bin/bash
# 单集后处理：content JSON 已存在时，跑 Step 5–9（抽帧/朗读/HTML/校验/index）
# 用法: bash scripts/process-episode.sh wo-de-qian-ban-sheng 我的前半生 03 我的前半生（2017）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DRAMA_SLUG="${1:?drama slug}"
DRAMA_NAME="${2:?drama display name}"
EP="${3:?episode NN}"
VIDEO_DIR="${4:-}"
EP=$(printf '%02d' "$((10#$EP))")
CONTENT="content/${DRAMA_SLUG}/content-e${EP}.json"
[ -f "$CONTENT" ] || { echo "missing $CONTENT"; exit 1; }

echo "=== process $DRAMA_SLUG e$EP ==="
python3 scripts/validate-content.py --file "$CONTENT"

if [ -n "$VIDEO_DIR" ]; then
  python3 scripts/extract-frames.py --drama "$DRAMA_SLUG" --ep "$EP" --video "$VIDEO_DIR"
else
  python3 scripts/extract-frames.py --drama "$DRAMA_SLUG" --ep "$EP"
fi

python3 scripts/generate-quote-audio.py --dir "content/${DRAMA_SLUG}"

HTML="docs/${DRAMA_NAME}-第${EP}集-剧情总结.html"
node render-recap.mjs "$CONTENT" "$HTML"
python3 scripts/check-audio-refs.py --drama "$DRAMA_NAME"

OUT="/tmp/${DRAMA_SLUG}-entries.json"
if [ -n "$VIDEO_DIR" ]; then
  python3 scripts/gen-index.py --drama "$DRAMA_SLUG" --drama-name "$DRAMA_NAME" --date "$(date +%F)" --video "$VIDEO_DIR" --out "$OUT"
else
  python3 scripts/gen-index.py --drama "$DRAMA_SLUG" --drama-name "$DRAMA_NAME" --date "$(date +%F)" --out "$OUT"
fi

python3 - "$OUT" <<'PY'
import json, sys
path = sys.argv[1]
idx = json.load(open("docs/index.json"))
entries = json.load(open(path))
by = {e["slug"]: i for i, e in enumerate(idx)}
for e in entries:
    if e["slug"] in by:
        idx[by[e["slug"]]] = e
    else:
        idx.append(e)
json.dump(idx, open("docs/index.json", "w"), ensure_ascii=False, indent=2)
print("index", len(idx))
PY

python3 scripts/gen-search-index.py >/dev/null
echo "=== DONE e$EP -> $HTML ==="
