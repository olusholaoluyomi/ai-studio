"""
AI Video Generation extension.

Supports:
  - CogVideoX-2b / CogVideoX-5b   — text-to-video (THUDM, Apache 2.0)
  - AnimateDiff                    — image-to-animated-video
  - ModelScope text-to-video       — lightweight t2v

All models are downloaded on first use from Hugging Face Hub (free, open-source).
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import gradio as gr

# ── optional heavy imports ─────────────────────────────────────────────────
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from diffusers import (
        CogVideoXPipeline,
        AnimateDiffPipeline,
        MotionAdapter,
        DDIMScheduler,
        DiffusionPipeline,
    )
    from diffusers.utils import export_to_video
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False

try:
    from huggingface_hub import snapshot_download
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False


# ── helpers ────────────────────────────────────────────────────────────────

def _device() -> str:
    if TORCH_AVAILABLE and torch.cuda.is_available():
        return "cuda"
    if TORCH_AVAILABLE and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _dtype():
    if not TORCH_AVAILABLE:
        return None
    import torch
    return torch.float16 if _device() in ("cuda", "mps") else torch.float32


def _models_root() -> Path:
    root = Path(os.environ.get("MODELS_DIR", Path(__file__).resolve().parents[2] / "models"))
    return root / "video"


# ── CogVideoX ─────────────────────────────────────────────────────────────

_cogvideox_pipe: Optional["CogVideoXPipeline"] = None


def load_cogvideox(model_id: str = "THUDM/CogVideoX-2b") -> "CogVideoXPipeline":
    global _cogvideox_pipe
    if _cogvideox_pipe is not None:
        return _cogvideox_pipe
    if not DIFFUSERS_AVAILABLE:
        raise RuntimeError("diffusers not installed. Run: pip install diffusers")
    import torch
    device = _device()
    dtype = _dtype()
    local_dir = _models_root() / model_id.split("/")[-1]
    pipe = CogVideoXPipeline.from_pretrained(
        str(local_dir) if local_dir.exists() else model_id,
        torch_dtype=dtype,
    )
    pipe.enable_model_cpu_offload()
    pipe.vae.enable_slicing()
    pipe.vae.enable_tiling()
    _cogvideox_pipe = pipe
    return pipe


def generate_video_cogvideox(
    prompt: str,
    negative_prompt: str = "low quality, blurry, distorted",
    num_frames: int = 49,
    fps: int = 8,
    guidance_scale: float = 6.0,
    num_inference_steps: int = 50,
    seed: int = -1,
    model_id: str = "THUDM/CogVideoX-2b",
    output_dir: Optional[str] = None,
) -> str:
    """Generate a video from a text prompt using CogVideoX."""
    import torch
    pipe = load_cogvideox(model_id)
    generator = torch.Generator(device=_device())
    if seed >= 0:
        generator.manual_seed(seed)
    else:
        generator.manual_seed(int(time.time()) % 2**31)

    result = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_frames=num_frames,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        generator=generator,
    )
    frames = result.frames[0]
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"cogvideox_{int(time.time())}.mp4")
    export_to_video(frames, out_path, fps=fps)
    return out_path


# ── AnimateDiff ────────────────────────────────────────────────────────────

_animatediff_pipe: Optional["AnimateDiffPipeline"] = None


def load_animatediff(
    base_model: str = "stable-diffusion-v1-5/stable-diffusion-v1-5",
    adapter_id: str = "guoyww/animatediff-motion-adapter-v1-5-2",
) -> "AnimateDiffPipeline":
    global _animatediff_pipe
    if _animatediff_pipe is not None:
        return _animatediff_pipe
    if not DIFFUSERS_AVAILABLE:
        raise RuntimeError("diffusers not installed. Run: pip install diffusers")
    import torch
    device = _device()
    dtype = _dtype()
    adapter = MotionAdapter.from_pretrained(adapter_id, torch_dtype=dtype)
    pipe = AnimateDiffPipeline.from_pretrained(
        base_model, motion_adapter=adapter, torch_dtype=dtype
    )
    pipe.scheduler = DDIMScheduler.from_pretrained(
        base_model,
        subfolder="scheduler",
        clip_sample=False,
        timestep_spacing="linspace",
        beta_schedule="linear",
        steps_offset=1,
    )
    pipe.enable_vae_slicing()
    pipe.enable_model_cpu_offload()
    _animatediff_pipe = pipe
    return pipe


def generate_video_animatediff(
    prompt: str,
    negative_prompt: str = "bad quality, worse quality, low resolution",
    num_frames: int = 16,
    fps: int = 8,
    guidance_scale: float = 7.5,
    num_inference_steps: int = 25,
    seed: int = -1,
    output_dir: Optional[str] = None,
) -> str:
    """Animate a scene described by prompt using AnimateDiff."""
    import torch
    pipe = load_animatediff()
    generator = torch.Generator(device=_device())
    generator.manual_seed(seed if seed >= 0 else int(time.time()) % 2**31)
    result = pipe(
        prompt,
        negative_prompt=negative_prompt,
        num_frames=num_frames,
        guidance_scale=guidance_scale,
        num_inference_steps=num_inference_steps,
        generator=generator,
    )
    frames = result.frames[0]
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"animatediff_{int(time.time())}.mp4")
    export_to_video(frames, out_path, fps=fps)
    return out_path


# ── ModelScope text-to-video (lightweight) ─────────────────────────────────

_modelscope_pipe = None


def generate_video_modelscope(
    prompt: str,
    num_inference_steps: int = 40,
    seed: int = -1,
    output_dir: Optional[str] = None,
) -> str:
    """Lightweight text-to-video via ModelScope (damo-vilab/text-to-video-ms-1.7b)."""
    global _modelscope_pipe
    if not DIFFUSERS_AVAILABLE:
        raise RuntimeError("diffusers not installed.")
    import torch
    from diffusers.utils import export_to_video as _export
    if _modelscope_pipe is None:
        _modelscope_pipe = DiffusionPipeline.from_pretrained(
            "damo-vilab/text-to-video-ms-1.7b",
            torch_dtype=_dtype(),
            variant="fp16",
        )
        _modelscope_pipe.enable_model_cpu_offload()
        _modelscope_pipe.enable_vae_slicing()
    generator = torch.Generator(device=_device())
    generator.manual_seed(seed if seed >= 0 else int(time.time()) % 2**31)
    result = _modelscope_pipe(
        prompt,
        num_inference_steps=num_inference_steps,
        generator=generator,
    )
    frames = result.frames[0]
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp())
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(out_dir / f"modelscope_{int(time.time())}.mp4")
    _export(frames, out_path, fps=8)
    return out_path


# ── Gradio UI tab ──────────────────────────────────────────────────────────

MODELS = {
    "CogVideoX-2b  (best quality, ~14 GB VRAM)": "cogvideox",
    "AnimateDiff   (stylised animation, ~6 GB VRAM)": "animatediff",
    "ModelScope-1.7b (fastest, ~6 GB VRAM)": "modelscope",
}

LANGUAGES_INFO = (
    "Prompts can be written in **any language** — the generator accepts "
    "English prompts natively. For best results with non-English prompts, "
    "the studio automatically translates them to English via the built-in "
    "deep-translator pipeline (100+ languages supported)."
)


def _translate_prompt_if_needed(prompt: str) -> str:
    try:
        from lingua import Language, LanguageDetectorBuilder
        detector = LanguageDetectorBuilder.from_all_languages().build()
        lang = detector.detect_language_of(prompt)
        if lang and lang != Language.ENGLISH:
            from deep_translator import GoogleTranslator
            return GoogleTranslator(source="auto", target="en").translate(prompt)
    except Exception:
        pass
    return prompt


def _run_generation(
    prompt: str,
    negative_prompt: str,
    model_choice: str,
    num_frames: int,
    fps: int,
    guidance_scale: float,
    num_steps: int,
    seed: int,
) -> tuple[str | None, str]:
    if not prompt.strip():
        return None, "Please enter a prompt."
    if not TORCH_AVAILABLE:
        return None, "PyTorch is not installed. Run `make setup` first."
    if not DIFFUSERS_AVAILABLE:
        return None, "diffusers is not installed. Run `make setup` first."

    eng_prompt = _translate_prompt_if_needed(prompt)
    mode = MODELS.get(model_choice, "modelscope")
    try:
        if mode == "cogvideox":
            path = generate_video_cogvideox(
                eng_prompt, negative_prompt, num_frames, fps,
                guidance_scale, num_steps, seed,
            )
        elif mode == "animatediff":
            path = generate_video_animatediff(
                eng_prompt, negative_prompt, num_frames, fps,
                guidance_scale, num_steps, seed,
            )
        else:
            path = generate_video_modelscope(eng_prompt, num_steps, seed)
        return path, f"Video generated: {Path(path).name}"
    except Exception as exc:
        return None, f"Error: {exc}"


def video_generation_tab() -> None:
    """Render the AI Video Generation Gradio tab."""
    gr.Markdown("## AI Video Generation")
    gr.Markdown(LANGUAGES_INFO)

    with gr.Row():
        with gr.Column(scale=2):
            prompt = gr.Textbox(
                label="Prompt (any language)",
                placeholder="A golden retriever running on a sunny beach at sunset...",
                lines=3,
            )
            negative_prompt = gr.Textbox(
                label="Negative prompt",
                value="low quality, blurry, distorted, watermark, text",
                lines=2,
            )
            model_choice = gr.Dropdown(
                label="Video generation model",
                choices=list(MODELS.keys()),
                value=list(MODELS.keys())[2],
            )
        with gr.Column(scale=1):
            num_frames = gr.Slider(8, 96, value=16, step=8, label="Frames")
            fps = gr.Slider(4, 30, value=8, step=1, label="FPS")
            guidance = gr.Slider(1.0, 20.0, value=7.5, step=0.5, label="Guidance scale")
            steps = gr.Slider(10, 100, value=30, step=5, label="Inference steps")
            seed = gr.Number(value=-1, label="Seed (-1 = random)", precision=0)

    generate_btn = gr.Button("Generate Video", variant="primary")
    status = gr.Textbox(label="Status", interactive=False)
    video_out = gr.Video(label="Generated video")

    generate_btn.click(
        fn=_run_generation,
        inputs=[prompt, negative_prompt, model_choice, num_frames, fps, guidance, steps, seed],
        outputs=[video_out, status],
    )
