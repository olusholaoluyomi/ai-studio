#!/usr/bin/env bash
# Download optional AI models for video generation
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$ROOT_DIR/models"
VENV_DIR="$ROOT_DIR/.venv"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
log()  { echo -e "${CYAN}[MODELS]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

[[ -d "$VENV_DIR" ]] && source "$VENV_DIR/bin/activate"

mkdir -p "$MODELS_DIR"/{video,whisper,f5-tts,rvc}

download_cogvideox() {
    log "Downloading CogVideoX-2b (text-to-video, ~14GB) ..."
    python3 - <<'EOF'
from huggingface_hub import snapshot_download
import os
snapshot_download(
    repo_id="THUDM/CogVideoX-2b",
    local_dir=os.path.join(os.environ.get("MODELS_DIR", "models"), "video", "CogVideoX-2b"),
    ignore_patterns=["*.pt"],   # prefer safetensors
)
print("CogVideoX-2b downloaded.")
EOF
    ok "CogVideoX-2b ready"
}

download_animatediff() {
    log "Downloading AnimateDiff motion adapter ..."
    python3 - <<'EOF'
from huggingface_hub import hf_hub_download
import os
models_dir = os.path.join(os.environ.get("MODELS_DIR", "models"), "video", "animatediff")
os.makedirs(models_dir, exist_ok=True)
hf_hub_download(
    repo_id="guoyww/animatediff-motion-adapter-v1-5-2",
    filename="diffusion_pytorch_model.safetensors",
    local_dir=models_dir,
)
print("AnimateDiff motion adapter downloaded.")
EOF
    ok "AnimateDiff motion adapter ready"
}

download_whisper() {
    log "Downloading Whisper large-v3 ..."
    python3 - <<'EOF'
import whisper, os
os.makedirs(os.path.join(os.environ.get("MODELS_DIR", "models"), "whisper"), exist_ok=True)
whisper.load_model("large-v3", download_root=os.path.join(os.environ.get("MODELS_DIR","models"),"whisper"))
print("Whisper large-v3 downloaded.")
EOF
    ok "Whisper large-v3 ready"
}

echo ""
echo "Select models to download:"
echo "  1) CogVideoX-2b        (text-to-video, ~14 GB, GPU required)"
echo "  2) AnimateDiff         (image animation, ~3 GB)"
echo "  3) Whisper large-v3    (speech recognition, ~3 GB)"
echo "  4) All of the above"
echo "  q) Quit"
echo ""
read -rp "Choice [1-4/q]: " CHOICE

export MODELS_DIR="$MODELS_DIR"

case "$CHOICE" in
    1) download_cogvideox ;;
    2) download_animatediff ;;
    3) download_whisper ;;
    4) download_cogvideox; download_animatediff; download_whisper ;;
    q|Q) echo "Aborted."; exit 0 ;;
    *) warn "Invalid choice."; exit 1 ;;
esac

echo ""
ok "Done. Models stored in $MODELS_DIR"
