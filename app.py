"""
HuggingFace Spaces entry point for AI Studio.

HF Spaces looks for app.py at the repo root and calls launch().
Automatically detects GPU availability and enables features accordingly.
"""

from __future__ import annotations

import os
import sys
import types
import logging
import platform
from pathlib import Path

# ── path setup ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
VOICE_PRO = ROOT / "voice-pro"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(VOICE_PRO))
sys.path.insert(0, str(VOICE_PRO / "third_party" / "Matcha-TTS"))

# ── stub broken native libs BEFORE voice-pro imports them ───────────────────
# ctranslate2 requires executable-stack kernel permission which HF CPU
# containers block. Stub it so imports succeed; inference fails gracefully.
def _stub_module(name: str, **attrs):
    mod = types.ModuleType(name)
    mod.__dict__.update(attrs)
    sys.modules[name] = mod
    return mod

try:
    import ctranslate2  # noqa: F401
except (ImportError, OSError):
    _stub_module(
        "ctranslate2",
        Translator=None,
        Generator=None,
        StorageView=None,
        get_supported_compute_types=lambda *a, **kw: [],
    )

try:
    import winreg  # noqa: F401
except (ImportError, ModuleNotFoundError):
    _stub_module("winreg")

try:
    import modelscope  # noqa: F401
except (ImportError, OSError):
    _ms = _stub_module("modelscope", snapshot_download=lambda *a, **kw: None)
    _stub_module("modelscope.hub.snapshot_download", snapshot_download=lambda *a, **kw: None)

# cosyvoice lives inside voice-pro but depends on modelscope + heavy GPU libs.
# Stub the whole package so the import chain doesn't crash on CPU.
try:
    from cosyvoice.cli.cosyvoice import CosyVoice2  # noqa: F401
except Exception:
    _cv = _stub_module("cosyvoice")
    _stub_module("cosyvoice.cli")
    _stub_module("cosyvoice.cli.cosyvoice", CosyVoice2=None)
    _stub_module("cosyvoice.utils")
    _stub_module("cosyvoice.utils.file_utils", load_wav=lambda *a, **kw: None)
    _stub_module("cosyvoice.utils.common", set_all_random_seed=lambda *a, **kw: None)

# ── logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.WARNING)
for lib in ("httpx", "httpcore", "fairseq", "azure.core",
            "faster_whisper", "matplotlib", "transformers", "urllib3"):
    logging.getLogger(lib).setLevel(logging.WARNING)

# ── dotenv (local dev only — HF Spaces uses Secrets) ───────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# ── GPU detection ────────────────────────────────────────────────────────────
try:
    import torch
    HAS_GPU = torch.cuda.is_available()
    GPU_NAME = torch.cuda.get_device_name(0) if HAS_GPU else "none"
except Exception:
    HAS_GPU = False
    GPU_NAME = "none"

print(f"[AI Studio] GPU: {GPU_NAME if HAS_GPU else 'CPU-only mode'}")

# ── Gradio ───────────────────────────────────────────────────────────────────
import gradio as gr

# ── Studio extensions ────────────────────────────────────────────────────────
from extensions.video_generation import video_generation_tab
from extensions.audio_generation import audio_generation_tab

# ── Voice Pro tabs (graceful degradation per feature) ────────────────────────

def _safe_tab(fn, fallback_msg: str):
    """Wrap a tab builder so import/runtime errors show a friendly message."""
    def builder():
        try:
            fn()
        except Exception as exc:
            gr.Markdown(f"> **Unavailable:** {fallback_msg}\n>\n> `{exc}`")
    return builder


def _load_voice_pro(user_config):
    tabs = {}

    try:
        from app.tab_gulliver import gulliver_tab
        tabs["dubbing"] = lambda: gulliver_tab(user_config)
    except Exception as e:
        tabs["dubbing"] = lambda msg=str(e): gr.Markdown(f"Dubbing Studio unavailable on this hardware.\n\n`{msg}`")

    try:
        from app.tab_subtitle import subtitle_tab
        tabs["subtitle"] = lambda: subtitle_tab(user_config)
    except Exception as e:
        tabs["subtitle"] = lambda msg=str(e): gr.Markdown(f"Whisper subtitles unavailable.\n\n`{msg}`")

    try:
        from app.tab_translate import translate_tab
        tabs["translate"] = lambda: translate_tab(user_config)
    except Exception as e:
        tabs["translate"] = lambda msg=str(e): gr.Markdown(f"Translation unavailable.\n\n`{msg}`")

    try:
        from app.tab_tts_edge import tts_edge_tab
        tabs["edge_tts"] = lambda: tts_edge_tab(user_config)
    except Exception as e:
        tabs["edge_tts"] = lambda msg=str(e): gr.Markdown(f"Edge-TTS unavailable.\n\n`{msg}`")

    try:
        from app.tab_tts_f5_single import tts_f5_single_tab
        from app.tab_tts_f5_multi import tts_f5_multi_tab
        tabs["f5_single"] = lambda: tts_f5_single_tab(user_config)
        tabs["f5_multi"]  = lambda: tts_f5_multi_tab(user_config)
    except Exception as e:
        msg = str(e)
        tabs["f5_single"] = lambda msg=msg: gr.Markdown(f"F5-TTS requires GPU.\n\n`{msg}`")
        tabs["f5_multi"]  = lambda msg=msg: gr.Markdown(f"F5-TTS requires GPU.\n\n`{msg}`")

    try:
        from app.tab_tts_cosyvoice import tts_cosyvoice_tab
        tabs["cosyvoice"] = lambda: tts_cosyvoice_tab(user_config)
    except Exception as e:
        tabs["cosyvoice"] = lambda msg=str(e): gr.Markdown(f"CosyVoice requires GPU (8 GB VRAM).\n\n`{msg}`")

    try:
        from app.tab_tts_kokoro import tts_kokoro_tab
        tabs["kokoro"] = lambda: tts_kokoro_tab(user_config)
    except Exception as e:
        tabs["kokoro"] = lambda msg=str(e): gr.Markdown(f"Kokoro unavailable.\n\n`{msg}`")

    try:
        from app.tab_demixing import demixing_tab
        tabs["demixing"] = lambda: demixing_tab(user_config)
    except Exception as e:
        tabs["demixing"] = lambda msg=str(e): gr.Markdown(f"Audio separation unavailable.\n\n`{msg}`")

    try:
        from app.tab_rvc import rvc_tab
        tabs["rvc"] = lambda: rvc_tab(user_config)
    except Exception as e:
        tabs["rvc"] = lambda msg=str(e): gr.Markdown(f"RVC voice conversion unavailable.\n\n`{msg}`")

    return tabs


def _get_user_config():
    try:
        from src.config import UserConfig
        return UserConfig(str(VOICE_PRO / "app" / "config-user.json5"))
    except Exception:
        return None


# ── App ──────────────────────────────────────────────────────────────────────

THEME = gr.themes.Soft(primary_hue="indigo", secondary_hue="purple", neutral_hue="slate")

CSS = """
.studio-header { text-align:center; padding:16px 0 8px; }
.studio-header h1 { font-size:2rem; font-weight:700; margin:0; }
.studio-header p  { color:#888; margin:4px 0 0; font-size:.95rem; }
.gpu-badge { display:inline-block; padding:2px 10px; border-radius:12px;
             font-size:.8rem; font-weight:600; margin-top:6px; }
.gpu-on  { background:#d1fae5; color:#065f46; }
.gpu-off { background:#fef3c7; color:#92400e; }
"""

gpu_badge = (
    f'<span class="gpu-badge gpu-on">GPU: {GPU_NAME}</span>'
    if HAS_GPU else
    '<span class="gpu-badge gpu-off">CPU-only mode — video generation disabled</span>'
)

def _render(fn, label: str) -> None:
    """Call a tab builder, showing a friendly error card if it crashes."""
    try:
        fn()
    except Exception as exc:
        gr.Markdown(f"> **{label} unavailable**\n>\n> `{exc}`")


def build_app() -> gr.Blocks:
    user_config = _get_user_config()
    voice_tabs  = _load_voice_pro(user_config)

    # Initialise Voice Pro — only download what's needed for CPU tier
    try:
        os.chdir(VOICE_PRO)
        from app.abus_hf import AbusHuggingFace
        from app.abus_genuine import genuine_init
        from app.abus_path import path_workspace_folder, path_gradio_folder
        genuine_init()
        AbusHuggingFace.initialize(app_name="voice")
        AbusHuggingFace.hf_download_models(file_type="edge-tts", level=0)
        if HAS_GPU:
            AbusHuggingFace.hf_download_models(file_type="demucs",    level=0)
            AbusHuggingFace.hf_download_models(file_type="kokoro",    level=0)
            AbusHuggingFace.hf_download_models(file_type="cosyvoice", level=0)
        path_workspace_folder()
        path_gradio_folder()
        os.chdir(ROOT)
    except Exception as e:
        print(f"[WARN] Voice Pro model init: {e}")
        try:
            os.chdir(ROOT)
        except Exception:
            pass

    with gr.Blocks(title="AI Studio", theme=THEME, css=CSS) as demo:

        gr.HTML(f"""
        <div class="studio-header">
          <h1>🎬 AI Studio</h1>
          <p>Video Generation &bull; Voice Cloning &bull; TTS (100+ languages) &bull;
             Audio Generation &bull; Subtitles &bull; Translation</p>
          {gpu_badge}
        </div>
        """)

        # ── Voice & Speech ───────────────────────────────────────────────────
        with gr.Tab("🎙️ Dubbing Studio"):
            _render(voice_tabs["dubbing"], "Dubbing Studio")

        with gr.Tab("📝 Whisper Subtitles"):
            _render(voice_tabs["subtitle"], "Whisper Subtitles")

        with gr.Tab("🌐 Translation"):
            _render(voice_tabs["translate"], "Translation")

        with gr.Tab("🗣️ Speech Generation"):
            with gr.Tabs():
                with gr.Tab("Edge-TTS  (400+ voices, 100+ langs)"):
                    _render(voice_tabs["edge_tts"], "Edge-TTS")
                with gr.Tab("F5-TTS  (voice cloning · single)"):
                    _render(voice_tabs["f5_single"], "F5-TTS Single")
                with gr.Tab("F5-TTS  (voice cloning · multi)"):
                    _render(voice_tabs["f5_multi"], "F5-TTS Multi")
                with gr.Tab("CosyVoice  (zero-shot cloning)"):
                    _render(voice_tabs["cosyvoice"], "CosyVoice")
                with gr.Tab("Kokoro  (high-quality TTS)"):
                    _render(voice_tabs["kokoro"], "Kokoro")

        with gr.Tab("🎵 Audio Separation"):
            _render(voice_tabs["demixing"], "Audio Separation")

        with gr.Tab("🔄 RVC Voice Conversion"):
            _render(voice_tabs["rvc"], "RVC Voice Conversion")

        # ── Video Generation (GPU-gated) ─────────────────────────────────────
        with gr.Tab("🎬 Video Generation"):
            if HAS_GPU:
                video_generation_tab()
            else:
                gr.Markdown("""
## Video Generation — GPU Required

This Space is currently running in **CPU-only** mode.

To enable AI video generation:
- Upgrade this Space to a **GPU** tier in HuggingFace Space settings
  (T4-small is sufficient for ModelScope; A10G for CogVideoX)
- Or run the studio locally with a CUDA-capable GPU

**Supported models (when GPU available):**
| Model | VRAM | Quality |
|-------|------|---------|
| ModelScope-1.7b | 6 GB | Good |
| AnimateDiff | 6 GB | Stylised |
| CogVideoX-2b | 14 GB | Best |
""")

        # ── Music & SFX ──────────────────────────────────────────────────────
        with gr.Tab("🎶 Music & SFX"):
            if HAS_GPU:
                audio_generation_tab()
            else:
                gr.Markdown("""
## Music & SFX Generation — GPU Required

AudioCraft (MusicGen / AudioGen) requires a GPU to run in real time.

Enable by upgrading this Space to a GPU tier, or run locally.
""")

        # ── Info ─────────────────────────────────────────────────────────────
        with gr.Tab("ℹ️ About"):
            gr.Markdown(ABOUT_MD)

    return demo


ABOUT_MD = """
## AI Studio — Feature Reference

| Feature | Engine | Languages | GPU needed? |
|---------|--------|-----------|-------------|
| Text-to-Speech | Edge-TTS | 100+ | No (CPU OK) |
| High-quality TTS | Kokoro | EN JA ZH FR ES | 2 GB |
| Voice Cloning (single) | F5-TTS | Multilingual | 4 GB |
| Voice Cloning (multi) | F5-TTS multi | Multilingual | 4 GB |
| Advanced Cloning | CosyVoice | ZH EN JA KO | 8 GB |
| Voice Conversion | RVC v2 | — | 4 GB |
| Speech Recognition | Whisper / WhisperX | 90+ | Optional |
| Video Dubbing | Gulliver | 100+ | Optional |
| Translation | Deep Translator | 100+ | No |
| Subtitles | Whisper + NLP | 90+ | Optional |
| Audio Separation | Demucs | — | 4 GB |
| Text-to-Video | CogVideoX-2b | Any | 14 GB |
| Text-to-Video | AnimateDiff | Any | 6 GB |
| Text-to-Video | ModelScope | Any | 6 GB |
| Music | MusicGen (Meta) | Any | 4 GB |
| Sound Effects | AudioGen (Meta) | Any | 4 GB |

**Credits:**
[Voice-Pro](https://github.com/abus-aikorea/voice-pro) ·
[CogVideoX](https://github.com/THUDM/CogVideo) ·
[AnimateDiff](https://github.com/guoyww/AnimateDiff) ·
[MusicGen](https://github.com/facebookresearch/audiocraft) ·
[Whisper](https://github.com/openai/whisper) ·
[F5-TTS](https://github.com/SWivid/F5-TTS) ·
[Kokoro](https://huggingface.co/hexgrad/Kokoro-82M)
"""


# ── Launch ────────────────────────────────────────────────────────────────────
demo = build_app()
demo.queue(max_size=10)

if __name__ == "__main__":
    demo.launch()
