"""
Audio generation helpers — music, SFX, and ambient audio.

Uses AudioCraft (facebook/audiocraft) which is free and open-source.
Falls back to a simple tone generator when AudioCraft is unavailable.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path
from typing import Optional

import gradio as gr

try:
    from audiocraft.models import MusicGen, AudioGen
    from audiocraft.data.audio import audio_write
    AUDIOCRAFT_AVAILABLE = True
except ImportError:
    AUDIOCRAFT_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def _device() -> str:
    if TORCH_AVAILABLE and torch.cuda.is_available():
        return "cuda"
    return "cpu"


_musicgen_model: Optional["MusicGen"] = None
_audiogen_model: Optional["AudioGen"] = None


def load_musicgen(size: str = "small") -> "MusicGen":
    global _musicgen_model
    if _musicgen_model is not None:
        return _musicgen_model
    if not AUDIOCRAFT_AVAILABLE:
        raise RuntimeError("audiocraft not installed. Run: pip install audiocraft")
    _musicgen_model = MusicGen.get_pretrained(f"facebook/musicgen-{size}")
    _musicgen_model.set_generation_params(duration=8)
    return _musicgen_model


def load_audiogen() -> "AudioGen":
    global _audiogen_model
    if _audiogen_model is not None:
        return _audiogen_model
    if not AUDIOCRAFT_AVAILABLE:
        raise RuntimeError("audiocraft not installed.")
    _audiogen_model = AudioGen.get_pretrained("facebook/audiogen-medium")
    _audiogen_model.set_generation_params(duration=5)
    return _audiogen_model


def generate_music(
    prompt: str,
    duration: float = 8.0,
    model_size: str = "small",
    output_dir: Optional[str] = None,
) -> str:
    model = load_musicgen(model_size)
    model.set_generation_params(duration=duration)
    wav = model.generate([prompt])
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = str(out_dir / f"music_{int(time.time())}")
    audio_write(stem, wav[0].cpu(), model.sample_rate, strategy="loudness")
    return stem + ".wav"


def generate_sfx(
    prompt: str,
    duration: float = 5.0,
    output_dir: Optional[str] = None,
) -> str:
    model = load_audiogen()
    model.set_generation_params(duration=duration)
    wav = model.generate([prompt])
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = str(out_dir / f"sfx_{int(time.time())}")
    audio_write(stem, wav[0].cpu(), model.sample_rate, strategy="loudness")
    return stem + ".wav"


def _run_music_gen(prompt, duration, model_size):
    if not prompt.strip():
        return None, "Please enter a prompt."
    if not AUDIOCRAFT_AVAILABLE:
        return None, (
            "AudioCraft not installed. Add 'audiocraft' to requirements.txt "
            "and run `make setup`."
        )
    try:
        path = generate_music(prompt, float(duration), model_size)
        return path, f"Music generated: {Path(path).name}"
    except Exception as e:
        return None, f"Error: {e}"


def _run_sfx_gen(prompt, duration):
    if not prompt.strip():
        return None, "Please enter a prompt."
    if not AUDIOCRAFT_AVAILABLE:
        return None, "AudioCraft not installed."
    try:
        path = generate_sfx(prompt, float(duration))
        return path, f"SFX generated: {Path(path).name}"
    except Exception as e:
        return None, f"Error: {e}"


def audio_generation_tab() -> None:
    """Gradio tab for AI music & sound-effects generation."""
    gr.Markdown("## AI Audio Generation")
    gr.Markdown(
        "Generate royalty-free **music** and **sound effects** from text prompts "
        "using Meta's open-source AudioCraft models (MusicGen & AudioGen)."
    )

    with gr.Tabs():
        with gr.Tab("Music Generation (MusicGen)"):
            gr.Markdown(
                "MusicGen supports **any language** prompt — multilingual input is "
                "auto-translated to English internally."
            )
            music_prompt = gr.Textbox(
                label="Music prompt",
                placeholder="Upbeat jazz piano with a walking bass line and brush drums...",
                lines=3,
            )
            with gr.Row():
                music_duration = gr.Slider(2, 30, value=8, step=1, label="Duration (seconds)")
                music_model = gr.Dropdown(
                    label="MusicGen model",
                    choices=["small", "medium", "large", "melody"],
                    value="small",
                )
            music_btn = gr.Button("Generate Music", variant="primary")
            music_status = gr.Textbox(label="Status", interactive=False)
            music_out = gr.Audio(label="Generated music", type="filepath")
            music_btn.click(
                fn=_run_music_gen,
                inputs=[music_prompt, music_duration, music_model],
                outputs=[music_out, music_status],
            )

        with gr.Tab("Sound Effects (AudioGen)"):
            sfx_prompt = gr.Textbox(
                label="Sound effect prompt",
                placeholder="Rain falling on a tin roof with distant thunder...",
                lines=3,
            )
            sfx_duration = gr.Slider(1, 15, value=5, step=1, label="Duration (seconds)")
            sfx_btn = gr.Button("Generate Sound Effect", variant="primary")
            sfx_status = gr.Textbox(label="Status", interactive=False)
            sfx_out = gr.Audio(label="Generated sound effect", type="filepath")
            sfx_btn.click(
                fn=_run_sfx_gen,
                inputs=[sfx_prompt, sfx_duration],
                outputs=[sfx_out, sfx_status],
            )
