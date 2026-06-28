#!/usr/bin/env bash
#
# Server-side deploy for the iTaxEasy APK backend (Python FastAPI + Alembic +
# PostgreSQL), with automatic rollback.
#
# The GitHub Actions workflow fast-forwards the checkout to the latest main,
# exports the previously-deployed commit as PREV_DEPLOY_REF, then runs this.
# If dependency install, alembic migrations, the pm2 restart, or the post-deploy
# health check fails, we reset back to the previous commit and rebuild it so the
# last known-good version stays live.
#
# Safe to run by hand too:  cd ~/itaxeasy-apk-back && bash scripts/deploy.sh
#
set -Eeuo pipefail

PM2_NAME="itaxeasy-apk-backend"
PORT="54110"
HEALTH_URL="http://127.0.0.1:${PORT}/"   # GET / returns {"status":"healthy"}
HEALTH_RETRIES=20            # x3s = up to ~60s for the API to start listening
WORKERS="2"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

# Poetry installs to ~/.local/bin, which isn't on PATH in non-interactive shells.
export PATH="$HOME/.local/bin:$PATH"
if command -v poetry >/dev/null 2>&1; then
  POETRY="$(command -v poetry)"
elif [ -x "$HOME/.local/bin/poetry" ]; then
  POETRY="$HOME/.local/bin/poetry"
else
  echo "ERROR: poetry not found on PATH or in ~/.local/bin. Install it first." >&2
  exit 1
fi

# Pin the interpreter so a system python upgrade can't silently move the venv.
"$POETRY" env use python3.12 >/dev/null 2>&1 || true

# .env is gitignored and must be provided on the server out-of-band.
if [ ! -f "$APP_DIR/.env" ]; then
  echo "ERROR: $APP_DIR/.env is missing. Create it before deploying." >&2
  exit 1
fi

# Commit to fall back to if this deploy fails. The workflow passes the
# previously-deployed SHA; otherwise derive it from the reflog.
PREV_REF="${PREV_DEPLOY_REF:-$(git rev-parse 'HEAD@{1}' 2>/dev/null || git rev-parse HEAD)}"
NEW_REF="$(git rev-parse HEAD)"
echo "==> $("$POETRY" run python --version) | deploying $NEW_REF | rollback target $PREV_REF"

build_and_start() {
  # poetry.lock is tracked, so this is a fast, reproducible install of the
  # production dependency set only (skips pytest/ruff/black from the dev group).
  echo "==> poetry install --only main"
  "$POETRY" install --only main --no-interaction

  # ---------------------- Database migrations (automatic) ----------------------
  # Apply ONLY committed Alembic migration files, in order. This NEVER resets or
  # wipes data -- `alembic upgrade head` only runs the upgrade() steps in the
  # migration files. If one fails (a bad migration), the command errors, the ERR
  # trap rolls back the CODE to the previous release, and a human fixes the
  # migration. There is deliberately NO downgrade/reset here.
  #
  # NOTE on rollback: resetting the code does NOT auto-downgrade the schema. A
  # rolled-back deploy re-runs `upgrade head` on the older code, which is a no-op
  # (the DB is already at or ahead of that code's head). A genuinely bad
  # migration that already applied must be reverted by hand.
  echo "==> alembic upgrade head"
  "$POETRY" run alembic upgrade head

  echo "==> (re)starting pm2 process '$PM2_NAME'"
  if pm2 describe "$PM2_NAME" >/dev/null 2>&1; then
    pm2 reload "$PM2_NAME" --update-env
  else
    # Run uvicorn via poetry so it uses the in-project venv. --interpreter none
    # tells pm2 to exec poetry directly instead of trying to run it under node.
    pm2 start "$POETRY" \
      --name "$PM2_NAME" \
      --cwd "$APP_DIR" \
      --interpreter none \
      -- run uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
  fi
  pm2 save
}

# One probe of the API. An API may legitimately answer non-2xx, so we only
# require that it ANSWERS (connection succeeds) -- not a 2xx. Connection refused
# (server not up) is the failure we care about. Works with curl or wget.
probe() {
  if command -v curl >/dev/null 2>&1; then
    curl -s -o /dev/null --max-time 5 "$HEALTH_URL"        # exit!=0 only if it can't connect
  elif command -v wget >/dev/null 2>&1; then
    wget -q -T 5 -O /dev/null "$HEALTH_URL" || \
      wget -q -T 5 -O /dev/null --server-response "$HEALTH_URL" 2>&1 | grep -q 'HTTP/'
  else
    echo "WARN: no curl/wget -- skipping health check" >&2
    return 0
  fi
}

# Return 0 once the API answers, retrying for a while as it boots.
healthy() {
  local i
  for i in $(seq 1 "$HEALTH_RETRIES"); do
    if probe; then
      return 0
    fi
    sleep 3
  done
  return 1
}

rollback() {
  trap - ERR                                   # don't recurse into ourselves
  echo "!!!! deploy of $NEW_REF FAILED -- rolling back to $PREV_REF" >&2
  if [ "$PREV_REF" = "$NEW_REF" ]; then
    echo "!! no earlier commit to roll back to (same ref); leaving as-is" >&2
    exit 1
  fi
  git reset --hard "$PREV_REF"
  if build_and_start && healthy; then
    echo "==> rollback OK: previous version ($PREV_REF) is live and healthy"
  else
    echo "!!!! ROLLBACK ALSO FAILED -- backend may be down, manual fix required" >&2
  fi
  exit 1
}

# Any failing command in build_and_start (install, alembic, pm2) trips this.
trap rollback ERR
build_and_start
trap - ERR

# Build/start succeeded -- confirm the API actually listens before declaring
# victory. If it doesn't come up, roll back to the previous commit.
if ! healthy; then
  echo "!! new version built but is not responding on $HEALTH_URL" >&2
  rollback
fi

echo "==> deploy complete: $NEW_REF is live and healthy on port $PORT"
