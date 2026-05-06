"""
AI Studio — unified Gradio application.

Modes:
  --mode studio   Full studio: voice + video + audio (default)
  --mode voice    Voice-Pro features only (faster startup)
  --mode video    Video generation only

Run:
  python src/studio_app.py
  python src/studio_app.py --mode voice
"""

from __future__ import annotations

import argparse
import os
import sys
import platform
import logging
from pathlib import Path

# ── path setup ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
VOICE_PRO = ROOT / "voice-pro"

# Add Voice Pro paths
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(VOICE_PRO))
sys.path.insert(0, str(VOICE_PRO / "third_party" / "Matcha-TTS"))

# ── logging ────────────────────────────────────────────────────────────────
LOG_LEVEL = os.environ.get("LOG_LEVEL", "WARNING").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.WARNING))
for noisy in ("httpx", "httpcore", "fairseq", "azure.core",
              "faster_whisper", "matplotlib", "transformers"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

# ── dotenv ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# ── gradio ─────────────────────────────────────────────────────────────────
import gradio as gr

# ── studio extensions ──────────────────────────────────────────────────────
from extensions.video_generation import video_generation_tab
from extensions.audio_generation import audio_generation_tab


# ── Voice Pro integration ──────────────────────────────────────────────────

def _load_voice_pro_tabs(user_config):
    """Return a dict of Voice Pro tab render functions, handling import errors gracefully."""
    tabs = {}
    try:
        from app.tab_gulliver import gulliver_tab
        tabs["dubbing"] = lambda: gulliver_tab(user_config)
    except Exception as e:
        tabs["dubbing"] = lambda: gr.Markdown(f"Dubbing Studio unavailable: {e}")

    try:
        from app.tab_subtitle import subtitle_tab
        tabs["subtitle"] = lambda: subtitle_tab(user_config)
    except Exception as e:
        tabs["subtitle"] = lambda: gr.Markdown(f"Whisper Subtitles unavailable: {e}")

    try:
        from app.tab_translate import translate_tab
        tabs["translate"] = lambda: translate_tab(user_config)
    except Exception as e:
        tabs["translate"] = lambda: gr.Markdown(f"Translation unavailable: {e}")

    try:
        from app.tab_tts_edge import tts_edge_tab
        tabs["edge_tts"] = lambda: tts_edge_tab(user_config)
    except Exception as e:
        tabs["edge_tts"] = lambda: gr.Markdown(f"Edge-TTS unavailable: {e}")

    try:
        from app.tab_tts_f5_single import tts_f5_single_tab
        from app.tab_tts_f5_multi import tts_f5_multi_tab
        tabs["f5_single"] = lambda: tts_f5_single_tab(user_config)
        tabs["f5_multi"] = lambda: tts_f5_multi_tab(user_config)
    except Exception as e:
        tabs["f5_single"] = lambda: gr.Markdown(f"F5-TTS unavailable: {e}")
        tabs["f5_multi"] = lambda: gr.Markdown(f"F5-TTS unavailable: {e}")

    try:
        from app.tab_tts_cosyvoice import tts_cosyvoice_tab
        tabs["cosyvoice"] = lambda: tts_cosyvoice_tab(user_config)
    except Exception as e:
        tabs["cosyvoice"] = lambda: gr.Markdown(f"CosyVoice unavailable: {e}")

    try:
        from app.tab_tts_kokoro import tts_kokoro_tab
        tabs["kokoro"] = lambda: tts_kokoro_tab(user_config)
    except Exception as e:
        tabs["kokoro"] = lambda: gr.Markdown(f"Kokoro TTS unavailable: {e}")

    try:
        from app.tab_demixing import demixing_tab
        tabs["demixing"] = lambda: demixing_tab(user_config)
    except Exception as e:
        tabs["demixing"] = lambda: gr.Markdown(f"Audio Demixing unavailable: {e}")

    try:
        from app.tab_rvc import rvc_tab
        tabs["rvc"] = lambda: rvc_tab(user_config)
    except Exception as e:
        tabs["rvc"] = lambda: gr.Markdown(f"RVC Voice Conversion unavailable: {e}")

    try:
        from app.tab_live_translate import live_translate_tab
        tabs["live"] = lambda: live_translate_tab(user_config)
    except Exception as e:
        tabs["live"] = None

    return tabs


def _get_user_config():
    try:
        from src.config import UserConfig
        cfg_path = VOICE_PRO / "app" / "config-user.json5"
        return UserConfig(str(cfg_path))
    except Exception:
        return None


# ── App builders ───────────────────────────────────────────────────────────

THEME = gr.themes.Soft(
    primary_hue="indigo",
    secondary_hue="purple",
    neutral_hue="slate",
)

STUDIO_CSS = """
.studio-header { text-align: center; padding: 12px 0 4px; }
.studio-header h1 { font-size: 2rem; font-weight: 700; margin: 0; }
.studio-header p  { color: #888; margin: 4px 0 0; }
"""


def build_studio_app(mode: str = "studio") -> gr.Blocks:
    user_config = _get_user_config()
    voice_tabs = _load_voice_pro_tabs(user_config) if mode != "video" else {}

    with gr.Blocks(
        title="AI Studio",
        theme=THEME,
        css=STUDIO_CSS,
    ) as app:

        gr.HTML("""
        <div class="studio-header">
          <h1>🎬 AI Studio</h1>
          <p>Video Generation &bull; Voice Cloning &bull; TTS (100+ languages) &bull;
             Audio Generation &bull; Subtitles &bull; Translation</p>
        </div>
        """)

        # ── Voice & Speech ─────────────────────────────────────────────────
        if mode in ("studio", "voice") and voice_tabs:
            with gr.Tab("🎙️ Dubbing Studio"):
                voice_tabs["dubbing"]()

            with gr.Tab("📝 Whisper Subtitles"):
                voice_tabs["subtitle"]()

            with gr.Tab("🌐 Translation"):
                if platform.system() == "Windows" and voice_tabs.get("live"):
                    with gr.Tabs():
                        with gr.Tab("VOD"):
                            voice_tabs["translate"]()
                        with gr.Tab("Live"):
                            voice_tabs["live"]()
                else:
                    voice_tabs["translate"]()

            with gr.Tab("🗣️ Speech Generation"):
                with gr.Tabs():
                    with gr.Tab("Edge-TTS  (400+ voices, 100+ langs)"):
                        voice_tabs["edge_tts"]()
                    with gr.Tab("F5-TTS  (voice cloning, single)"):
                        voice_tabs["f5_single"]()
                    with gr.Tab("F5-TTS  (voice cloning, multi-speaker)"):
                        voice_tabs["f5_multi"]()
                    with gr.Tab("CosyVoice  (zero-shot cloning)"):
                        voice_tabs["cosyvoice"]()
                    with gr.Tab("Kokoro  (high-quality TTS)"):
                        voice_tabs["kokoro"]()

            with gr.Tab("🎵 Audio Separation"):
                voice_tabs["demixing"]()

            with gr.Tab("🔄 RVC Voice Conversion"):
                voice_tabs["rvc"]()

        # ── Video Generation ────────────────────────────────────────────────
        if mode in ("studio", "video"):
            with gr.Tab("🎬 Video Generation"):
                video_generation_tab()

        # ── Audio / Music Generation ────────────────────────────────────────
        if mode in ("studio", "video"):
            with gr.Tab("🎶 Music & SFX"):
                audio_generation_tab()

        # ── Info tab ────────────────────────────────────────────────────────
        with gr.Tab("ℹ️ Info"):
            gr.Markdown(INFO_MARKDOWN)

    return app


INFO_MARKDOWN = """
## AI Studio — Feature Guide

| Feature | Engine | Languages | Notes |
|---------|--------|-----------|-------|
| Text-to-Speech | Edge-TTS | **100+ languages, 400+ voices** | Neural voices, SSML support |
| Voice Cloning (zero-shot) | F5-TTS / E2-TTS | Multilingual | Requires 5–10s reference audio |
| Voice Cloning (advanced) | CosyVoice | Chinese, English, Japanese, Korean | 9 GB model |
| High-quality TTS | Kokoro | EN, JA, ZH, FR, ES, PT, HI, IT | Top HuggingFace TTS ranking |
| Speech Recognition | Whisper / WhisperX | **90+ languages** | Word-level timestamps |
| Video Dubbing | Gulliver (VP) | 100+ | Full pipeline: ASR → translate → TTS → sync |
| Translation | Deep/Azure Translator | 100+ | Free tier available |
| Subtitle generation | Whisper + NLP | 90+ | ASS/SRT/SSA output |
| Audio separation | Demucs + MDX-Net | — | Vocals, drums, bass, other |
| RVC Voice Conversion | RVC v2 | — | Real-time voice style transfer |
| Text-to-Video | CogVideoX-2b | Any (auto-translated) | ~14 GB VRAM; Apache 2.0 |
| Text-to-Video | AnimateDiff | Any (auto-translated) | ~6 GB VRAM; animate any style |
| Text-to-Video | ModelScope-1.7b | Any (auto-translated) | Lightweight fallback |
| Music Generation | MusicGen (Meta) | Any (auto-translated) | Free, open-source |
| Sound Effects | AudioGen (Meta) | Any (auto-translated) | Free, open-source |

### Language Coverage
- **TTS:** 100+ languages via Edge-TTS (Microsoft neural voices)
- **Speech recognition:** 90+ languages via OpenAI Whisper
- **Translation:** 100+ languages via Deep Translator / Azure
- **Video prompts:** Any language — auto-translated to English before generation
- **Music/SFX prompts:** Any language — auto-translated before generation

### Quick Start
```bash
make setup       # Install everything
make run         # Launch full studio
make run-voice   # Voice features only
make run-video   # Video generation only
make models      # Download optional models
```

### GPU Requirements
| Feature | Minimum VRAM |
|---------|-------------|
| Edge-TTS / Whisper (CPU) | 0 GB (CPU OK) |
| Whisper large-v3 | 6 GB |
| F5-TTS / CosyVoice | 4 GB |
| CogVideoX-2b | 14 GB |
| AnimateDiff | 6 GB |
| ModelScope-1.7b | 6 GB |
| MusicGen small | 4 GB |

### Credits
- **Voice-Pro** by [abus-aikorea](https://github.com/abus-aikorea/voice-pro) — LGPL
- **CogVideoX** by THUDM — Apache 2.0
- **AnimateDiff** by guoyww — Apache 2.0
- **MusicGen / AudioGen** by Meta — MIT
- **Whisper** by OpenAI — MIT
- **F5-TTS** — MIT
- **Kokoro** — Apache 2.0
"""


# ── Entry point ────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI Studio launcher")
    p.add_argument("--mode", choices=["studio", "voice", "video"], default="studio")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=int(os.environ.get("STUDIO_PORT", 7860)))
    p.add_argument("--share", action="store_true", help="Create public Gradio link")
    p.add_argument("--no-browser", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Initialize Voice Pro model downloads when in voice/studio mode
    if args.mode in ("studio", "voice"):
        try:
            os.chdir(VOICE_PRO)
            from app.abus_hf import AbusHuggingFace
            from app.abus_genuine import genuine_init
            from app.abus_path import path_workspace_folder, path_gradio_folder
            genuine_init()
            AbusHuggingFace.initialize(app_name="voice")
            AbusHuggingFace.hf_download_models(file_type="demucs", level=0)
            AbusHuggingFace.hf_download_models(file_type="edge-tts", level=0)
            AbusHuggingFace.hf_download_models(file_type="kokoro", level=0)
            AbusHuggingFace.hf_download_models(file_type="cosyvoice", level=0)
            path_workspace_folder()
            path_gradio_folder()
            os.chdir(ROOT)
        except Exception as e:
            print(f"[WARN] Voice Pro model init skipped: {e}")
            os.chdir(ROOT)

    app = build_studio_app(mode=args.mode)
    app.queue()
    app.launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        inbrowser=not args.no_browser,
    )
