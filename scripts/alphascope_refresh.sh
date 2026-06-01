#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="/home/dmudalige/projects/alphascope"
PYTHON="$REPO_DIR/.venv/bin/python"
BRANCH="web-launch"
REMOTE="origin"
LOCK_FILE="/tmp/alphascope-refresh.lock"
LOG_DIR="$REPO_DIR/logs"
RUN_LOG="$LOG_DIR/alphascope-automation.log"

GENERATED_FILES=(
  "web/data/latest-report.json"
  "web/data/full-report.json"
  "web/data/investor-rankings.json"
)

mkdir -p "$LOG_DIR"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "$(date -Is) | another AlphaScope refresh is already running" | tee -a "$RUN_LOG"
  exit 0
fi

log() {
  echo "$(date -Is) | $*" | tee -a "$RUN_LOG"
}

fail_validation() {
  log "validation failed: $*"
  exit 1
}

validate_json_file() {
  local file="$1"

  if [ ! -f "$file" ]; then
    fail_validation "$file does not exist"
  fi

  if ! "$PYTHON" -m json.tool "$file" >/dev/null 2>>"$RUN_LOG"; then
    fail_validation "$file is not valid JSON"
  fi
}

validate_json_outputs() {
  log "validating generated JSON outputs"

  validate_json_file "web/data/latest-report.json"
  validate_json_file "web/data/full-report.json"
  validate_json_file "web/data/investor-rankings.json"

  if ! "$PYTHON" -c 'import json, sys; data=json.load(open(sys.argv[1], encoding="utf-8")); missing=[key for key in ("generated_at", "confidence") if key not in data]; raise SystemExit(1 if missing else 0)' web/data/latest-report.json; then
    fail_validation "web/data/latest-report.json must contain generated_at and confidence"
  fi

  if ! "$PYTHON" -c 'import json, sys; data=json.load(open(sys.argv[1], encoding="utf-8")); rankings=data.get("rankings"); raise SystemExit(0 if isinstance(rankings, list) and len(rankings) > 0 else 1)' web/data/investor-rankings.json; then
    fail_validation "web/data/investor-rankings.json must contain a non-empty rankings array"
  fi
}

cd "$REPO_DIR"

log "AlphaScope automation started"

if [ ! -x "$PYTHON" ]; then
  log "Python executable not found or not executable: $PYTHON"
  exit 1
fi

current_branch="$(git branch --show-current)"
if [ "$current_branch" != "$BRANCH" ]; then
  log "wrong branch: expected $BRANCH, got $current_branch"
  exit 1
fi

log "running AlphaScope pipeline"
"$PYTHON" -m app.main full 2>&1 | tee -a "$RUN_LOG"

validate_json_outputs

log "staging generated web outputs only"
git add "${GENERATED_FILES[@]}"

if git diff --cached --quiet -- "${GENERATED_FILES[@]}"; then
  log "no generated web output changes; skipping commit and push"
  exit 0
fi

commit_message="refresh AlphaScope web data $(date -u +'%Y-%m-%d %H:%M UTC')"

log "committing generated web outputs"
git commit -m "$commit_message" -- "${GENERATED_FILES[@]}"

log "pushing generated web outputs to $REMOTE $BRANCH"
git push "$REMOTE" "$BRANCH"

log "AlphaScope automation completed"
