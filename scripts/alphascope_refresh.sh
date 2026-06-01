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

log "validating generated JSON outputs"
"$PYTHON" -m json.tool web/data/latest-report.json >/dev/null
"$PYTHON" -m json.tool web/data/full-report.json >/dev/null
"$PYTHON" -m json.tool web/data/investor-rankings.json >/dev/null

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
