#!/usr/bin/env bash
# AI Studio — unified launcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ROOT_DIR/.venv"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
log() { echo -e "${CYAN}[STUDIO]${NC} $*"; }
err() { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

# Activate venv
if [[ -d "$VENV_DIR" ]]; then
    source "$VENV_DIR/bin/activate"
else
    err "Virtual environment not found. Run: make setup"
fi

# Load .env
if [[ -f "$ROOT_DIR/.env" ]]; then
    set -o allexport
    source "$ROOT_DIR/.env"
    set +o allexport
fi

log "Starting AI Studio ..."
cd "$ROOT_DIR"

# Parse mode flag
MODE="${1:-studio}"
case "$MODE" in
    voice)
        log "Mode: Voice-Pro (all speech features)"
        python3 src/studio_app.py --mode voice
        ;;
    video)
        log "Mode: Video Generation"
        python3 src/studio_app.py --mode video
        ;;
    studio|*)
        log "Mode: Full AI Studio (voice + video + audio)"
        python3 src/studio_app.py --mode studio
        ;;
esac
