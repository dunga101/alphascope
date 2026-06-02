#!/usr/bin/env bash
set -Eeuo pipefail

REPO_DIR="/home/dmudalige/projects/alphascope"
PYTHON="$REPO_DIR/.venv/bin/python"
REMOTE="origin"
DEPLOY_BRANCH="web-launch"
SOURCE_BRANCH="feature/investor-dashboard-v2"
LOG_DIR="$REPO_DIR/logs"
RUN_LOG="$LOG_DIR/alphascope_refresh.log"
LOCK_FILE="$LOG_DIR/alphascope_refresh.lock"
DEPLOY_WORKTREE="$REPO_DIR/.deploy/web-launch"

GENERATED_FILES=(
  "web/data/latest-report.json"
  "web/data/full-report.json"
  "web/data/investor-rankings.json"
  "web/data/data-health.json"
)

mkdir -p "$LOG_DIR"

log() {
  printf '%s | %s\n' "$(date -Is)" "$*" | tee -a "$RUN_LOG"
}

on_error() {
  local status="$?"
  local line="${BASH_LINENO[0]:-unknown}"
  log "event=error status=$status line=$line command=${BASH_COMMAND}"
  exit "$status"
}

trap on_error ERR

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  log "event=lock status=skipped message=\"another AlphaScope refresh is already running\""
  exit 0
fi

absolute_path() {
  local relative_path="$1"
  printf '%s/%s' "$REPO_DIR" "$relative_path"
}

deploy_path() {
  local relative_path="$1"
  printf '%s/%s' "$DEPLOY_DIR" "$relative_path"
}

fail_validation() {
  log "event=validation status=failed message=\"$*\""
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
  log "event=validation status=started"

  validate_json_file "$(absolute_path "web/data/latest-report.json")"
  validate_json_file "$(absolute_path "web/data/full-report.json")"
  validate_json_file "$(absolute_path "web/data/investor-rankings.json")"
  validate_json_file "$(absolute_path "web/data/data-health.json")"

  if ! "$PYTHON" -c 'import json, sys; data=json.load(open(sys.argv[1], encoding="utf-8")); missing=[key for key in ("generated_at", "confidence") if key not in data]; raise SystemExit(1 if missing else 0)' "$(absolute_path "web/data/latest-report.json")"; then
    fail_validation "web/data/latest-report.json must contain generated_at and confidence"
  fi

  if ! "$PYTHON" -c 'import json, sys; data=json.load(open(sys.argv[1], encoding="utf-8")); rankings=data.get("rankings"); raise SystemExit(0 if isinstance(rankings, list) and len(rankings) > 0 else 1)' "$(absolute_path "web/data/investor-rankings.json")"; then
    fail_validation "web/data/investor-rankings.json must contain a non-empty rankings array"
  fi

  if ! "$PYTHON" -c 'import json, sys; data=json.load(open(sys.argv[1], encoding="utf-8")); summary=data.get("summary"); symbols=data.get("symbols"); raise SystemExit(0 if isinstance(summary, dict) and isinstance(symbols, list) else 1)' "$(absolute_path "web/data/data-health.json")"; then
    fail_validation "web/data/data-health.json must contain summary and symbols"
  fi

  "$PYTHON" - "$(absolute_path "web/data/data-health.json")" <<'PY' | while IFS= read -r warning; do
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file:
    data = json.load(file)

summary = data.get("summary", {})
total = int(summary.get("total_symbols") or 0)
fundamentals = int(summary.get("fundamentals_available") or 0)
scores = int(summary.get("scores_available") or 0)
coverage = float(summary.get("coverage_percentage") or 0)

if fundamentals < total:
    print(f"warning: fundamentals coverage below symbol count ({fundamentals}/{total})")
if scores < total:
    print(f"warning: investor score coverage below symbol count ({scores}/{total})")
if coverage < 95:
    print(f"warning: complete data coverage below 95% ({coverage}%)")
PY
    log "event=validation status=warning message=\"$warning\""
  done

  log "event=validation status=passed"
}

verify_repository_root() {
  cd "$REPO_DIR"

  local actual_root
  actual_root="$(git rev-parse --show-toplevel)"

  if [ "$actual_root" != "$REPO_DIR" ]; then
    log "event=repository status=failed expected=$REPO_DIR actual=$actual_root"
    exit 1
  fi
}

verify_source_branch() {
  current_branch="$(git -C "$REPO_DIR" branch --show-current)"

  case "$current_branch" in
    "$SOURCE_BRANCH"|"$DEPLOY_BRANCH")
      ;;
    *)
      log "event=branch status=failed allowed=\"$SOURCE_BRANCH,$DEPLOY_BRANCH\" actual=$current_branch"
      exit 1
      ;;
  esac
}

prepare_deploy_worktree() {
  if [ "$current_branch" = "$DEPLOY_BRANCH" ]; then
    DEPLOY_DIR="$REPO_DIR"
    return
  fi

  mkdir -p "$REPO_DIR/.deploy"

  if [ -d "$DEPLOY_WORKTREE/.git" ] || [ -f "$DEPLOY_WORKTREE/.git" ]; then
    DEPLOY_DIR="$DEPLOY_WORKTREE"
  else
    log "event=deploy_worktree status=creating path=$DEPLOY_WORKTREE branch=$DEPLOY_BRANCH"
    git -C "$REPO_DIR" worktree add "$DEPLOY_WORKTREE" "$DEPLOY_BRANCH" 2>&1 | tee -a "$RUN_LOG"
    DEPLOY_DIR="$DEPLOY_WORKTREE"
  fi

  git -C "$DEPLOY_DIR" checkout "$DEPLOY_BRANCH" 2>&1 | tee -a "$RUN_LOG"
}

sync_deploy_branch() {
  log "event=git_fetch status=started remote=$REMOTE branch=$DEPLOY_BRANCH"
  git -C "$DEPLOY_DIR" fetch "$REMOTE" "$DEPLOY_BRANCH" 2>&1 | tee -a "$RUN_LOG"

  log "event=git_pull status=started remote=$REMOTE branch=$DEPLOY_BRANCH"
  git -C "$DEPLOY_DIR" pull --ff-only "$REMOTE" "$DEPLOY_BRANCH" 2>&1 | tee -a "$RUN_LOG"
}

copy_generated_outputs_to_deploy_branch() {
  if [ "$DEPLOY_DIR" = "$REPO_DIR" ]; then
    return
  fi

  mkdir -p "$DEPLOY_DIR/web/data"

  for relative_file in "${GENERATED_FILES[@]}"; do
    cp "$(absolute_path "$relative_file")" "$(deploy_path "$relative_file")"
  done
}

commit_and_push_outputs() {
  log "event=git_stage status=started branch=$DEPLOY_BRANCH"

  for relative_file in "${GENERATED_FILES[@]}"; do
    git -C "$DEPLOY_DIR" add "$(deploy_path "$relative_file")"
  done

  if git -C "$DEPLOY_DIR" diff --cached --quiet -- "${GENERATED_FILES[@]}"; then
    log "event=git_commit status=skipped reason=\"no generated web output changes\""
    return
  fi

  local commit_message
  commit_message="refresh AlphaScope web data $(date -u +'%Y-%m-%d %H:%M UTC')"

  log "event=git_commit status=started branch=$DEPLOY_BRANCH"
  git -C "$DEPLOY_DIR" commit -m "$commit_message" -- "${GENERATED_FILES[@]}" 2>&1 | tee -a "$RUN_LOG"
  log "event=git_commit status=completed branch=$DEPLOY_BRANCH"

  log "event=git_push status=started remote=$REMOTE branch=$DEPLOY_BRANCH"
  git -C "$DEPLOY_DIR" push "$REMOTE" "$DEPLOY_BRANCH" 2>&1 | tee -a "$RUN_LOG"
  log "event=git_push status=completed remote=$REMOTE branch=$DEPLOY_BRANCH"
}

verify_repository_root

log "event=start user=$(id -un) repo=$REPO_DIR"

if [ ! -x "$PYTHON" ]; then
  log "event=python status=failed path=$PYTHON"
  exit 1
fi

verify_source_branch

log "event=context user=$(id -un) branch=$current_branch deploy_branch=$DEPLOY_BRANCH python=$PYTHON"
log "event=deployment_model source_branch=$current_branch target=$REMOTE/$DEPLOY_BRANCH mode=data_files_only"

log "event=pipeline status=started command=\"$PYTHON -m app.main full\""
"$PYTHON" -m app.main full 2>&1 | tee -a "$RUN_LOG"
log "event=pipeline status=completed"

validate_json_outputs

prepare_deploy_worktree
sync_deploy_branch
copy_generated_outputs_to_deploy_branch
commit_and_push_outputs

log "event=complete status=success"
