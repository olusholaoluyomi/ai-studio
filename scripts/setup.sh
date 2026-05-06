#!/usr/bin/env bash
# AI Studio — full environment setup
# Run once before first launch.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_MIN="3.10"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[SETUP]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

# ── 1. Python ────────────────────────────────────────────────────────────────
log "Checking Python >= $PYTHON_MIN ..."
if ! command -v python3 &>/dev/null; then
    err "python3 not found. Install Python 3.10+ and retry."
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" \
    || err "Python $PY_VER found but 3.10+ is required."
ok "Python $PY_VER"

# ── 2. System packages ───────────────────────────────────────────────────────
log "Checking system dependencies ..."
MISSING=()
for cmd in git ffmpeg; do
    command -v "$cmd" &>/dev/null || MISSING+=("$cmd")
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    warn "Missing system packages: ${MISSING[*]}"
    if command -v apt-get &>/dev/null; then
        log "Installing via apt-get ..."
        sudo apt-get update -qq
        sudo apt-get install -y ffmpeg git curl wget
    elif command -v brew &>/dev/null; then
        brew install ffmpeg git
    else
        err "Please install manually: ${MISSING[*]}"
    fi
fi
ok "System dependencies satisfied"

# ── 3. CUDA check ────────────────────────────────────────────────────────────
if command -v nvidia-smi &>/dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | head -1)
    ok "GPU detected: $GPU_INFO"
    GPU_AVAILABLE=true
else
    warn "No NVIDIA GPU detected — will install CPU build of PyTorch (slower inference)."
    GPU_AVAILABLE=false
fi

# ── 4. Virtual environment ───────────────────────────────────────────────────
log "Setting up virtual environment at $VENV_DIR ..."
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    ok "Created venv"
else
    ok "Venv already exists"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel -q

# ── 5. Voice Pro dependencies ────────────────────────────────────────────────
log "Installing Voice Pro dependencies ..."
if [[ "$GPU_AVAILABLE" == true ]]; then
    REQ="$ROOT_DIR/voice-pro/requirements-voice-gpu.txt"
else
    REQ="$ROOT_DIR/voice-pro/requirements-voice-cpu.txt"
fi

pip install -r "$REQ" --extra-index-url https://download.pytorch.org/whl/cu124 -q \
    || err "Failed installing Voice Pro requirements from $REQ"
ok "Voice Pro dependencies installed"

# ── 6. AI Studio extra dependencies ─────────────────────────────────────────
log "Installing AI Studio extra dependencies ..."
pip install -r "$ROOT_DIR/requirements.txt" -q \
    || err "Failed installing AI Studio requirements"
ok "AI Studio extras installed"

# ── 7. spaCy language models ─────────────────────────────────────────────────
log "Downloading spaCy models ..."
python3 -m spacy download en_core_web_sm -q 2>/dev/null || true
python3 -m spacy download zh_core_web_sm -q 2>/dev/null || true
ok "spaCy models ready"

# ── 8. Copy env template ─────────────────────────────────────────────────────
if [[ ! -f "$ROOT_DIR/.env" ]]; then
    cp "$ROOT_DIR/config/.env.example" "$ROOT_DIR/.env"
    ok "Created .env from template — edit it to add API keys"
else
    ok ".env already exists"
fi

# ── 9. Git submodules ────────────────────────────────────────────────────────
log "Updating git submodules ..."
cd "$ROOT_DIR"
git submodule update --init --recursive -q
ok "Submodules up to date"

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  AI Studio setup complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════${NC}"
echo ""
echo "  Launch with:  make run"
echo "  Or directly:  ./scripts/start.sh"
echo ""
