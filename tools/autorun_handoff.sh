#!/usr/bin/env bash
# claude-opus-4-7
# Slice docs/handoff.md by "## BATCH N" markers, run multi_agent per batch.
# Usage: bash tools/autorun_handoff.sh [--start-from N] [--only N] [--timeout SECONDS]
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/docs/handoff.md"
ACTIVE="$ROOT/docs/handoff.md"
BACKUP="$ROOT/docs/handoff.full.md"
LOGDIR="$ROOT/docs/autorun_logs"
TMPDIR="${TMPDIR:-/tmp}/aras-autorun-$$"
mkdir -p "$TMPDIR" "$LOGDIR"

START_FROM=1
ONLY=""
TIMEOUT_SEC=1800
while [[ $# -gt 0 ]]; do
  case "$1" in
    --start-from) START_FROM="$2"; shift 2;;
    --only)       ONLY="$2"; shift 2;;
    --timeout)    TIMEOUT_SEC="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 2;;
  esac
done

# Preserve full spec only if not already backed up (don't overwrite on rerun)
if [[ ! -f "$BACKUP" ]]; then cp "$SRC" "$BACKUP"; fi
trap 'cp "$BACKUP" "$ACTIVE"; echo "[autorun] restored handoff.md from full backup"; rm -rf "$TMPDIR"' EXIT

HEADER=$(awk '/^## BATCH 1/ {exit} {print}' "$BACKUP")

awk '
  /^## BATCH [0-9]+/ {
    n = $3; sub(/[^0-9]/, "", n)
    file = "'"$TMPDIR"'/batch_" n ".md"
    printing = 1
  }
  /^## Autorun protocol/ { printing = 0 }
  printing { print > file }
' "$BACKUP"

BATCHES=()
while IFS= read -r line; do BATCHES+=("$line"); done < <(ls "$TMPDIR"/batch_*.md 2>/dev/null | sort -t_ -k2 -n)
TOTAL=${#BATCHES[@]}
if [[ "$TOTAL" -eq 0 ]]; then
  echo "[autorun] no batches sliced — check '## BATCH N' markers in $BACKUP"
  exit 1
fi
echo "[autorun] $TOTAL batches detected, start_from=$START_FROM only=${ONLY:-none} timeout=${TIMEOUT_SEC}s"

run_batch() {
  local N=$1 B=$2
  local LOG="$LOGDIR/batch_${N}.log"
  echo ""
  echo "════════════════════════════════════════"
  echo "[autorun] BATCH $N / $TOTAL  →  log: $LOG"
  echo "════════════════════════════════════════"

  { echo "$HEADER"; echo ""; cat "$B"; } > "$ACTIVE"

  if command -v gtimeout >/dev/null 2>&1; then
    TO=gtimeout
  elif command -v timeout >/dev/null 2>&1; then
    TO=timeout
  else
    TO=""
  fi

  set +e
  if [[ -n "$TO" ]]; then
    $TO "${TIMEOUT_SEC}s" python "$ROOT/tools/multi_agent.py" 2>&1 | tee "$LOG"
    rc=${PIPESTATUS[0]}
  else
    python "$ROOT/tools/multi_agent.py" 2>&1 | tee "$LOG"
    rc=${PIPESTATUS[0]}
  fi
  set -e

  if [[ "$rc" == "124" ]]; then
    echo "[autorun] BATCH $N TIMEOUT after ${TIMEOUT_SEC}s — kill and resume: bash tools/autorun_handoff.sh --start-from $((N+1))"
    return 124
  elif [[ "$rc" != "0" ]]; then
    echo "[autorun] BATCH $N failed (rc=$rc) — resume: bash tools/autorun_handoff.sh --start-from $N"
    return $rc
  fi
  echo "[autorun] BATCH $N complete."
  return 0
}

for i in "${!BATCHES[@]}"; do
  N=$((i+1))
  [[ -n "$ONLY" && "$N" != "$ONLY" ]] && continue
  [[ "$N" -lt "$START_FROM" ]] && continue
  run_batch "$N" "${BATCHES[$i]}" || exit $?
  sleep 2
done

echo ""
echo "[autorun] DONE. Run 'rhf' to review."
