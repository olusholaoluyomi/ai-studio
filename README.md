---
title: AI Studio
emoji: 🎬
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: 5.14.0
app_file: app.py
pinned: true
license: mit
short_description: Video generation · Voice cloning · TTS 100+ languages · Music
tags:
  - audio
  - video
  - speech
  - tts
  - voice-cloning
  - whisper
  - gradio
  - text-to-video
  - music-generation
---

# AI Studio

A unified, fully open-source AI media generation studio powered by
[Voice-Pro](https://github.com/abus-aikorea/voice-pro),
[CogVideoX](https://github.com/THUDM/CogVideo),
[AnimateDiff](https://github.com/guoyww/AnimateDiff),
[MusicGen](https://github.com/facebookresearch/audiocraft), and more.

**Everything is free and open-source. No API keys required for core features.**

---

## Features at a Glance

| Category | Capability | Engine | Languages |
|----------|-----------|--------|-----------|
| **TTS** | Text-to-speech | Edge-TTS | **100+ languages, 400+ voices** |
| **TTS** | High-quality TTS | Kokoro | EN, JA, ZH, FR, ES, PT, HI, IT |
| **Voice Cloning** | Zero-shot cloning (single) | F5-TTS / E2-TTS | Multilingual |
| **Voice Cloning** | Zero-shot cloning (multi) | F5-TTS multi-speaker | Multilingual |
| **Voice Cloning** | Advanced voice synthesis | CosyVoice | ZH, EN, JA, KO |
| **Voice Conversion** | Real-time voice style transfer | RVC v2 | — |
| **ASR** | Speech-to-text | Whisper / WhisperX / Faster-Whisper | **90+ languages** |
| **Dubbing** | Full dubbing pipeline | Voice-Pro Gulliver | 100+ |
| **Translation** | Text & audio translation | Deep Translator / Azure | 100+ |
| **Subtitles** | Auto subtitle generation | Whisper + NLP | 90+, ASS/SRT/SSA |
| **Audio separation** | Vocals, drums, bass, other | Demucs + MDX-Net | — |
| **Video generation** | Text-to-video | CogVideoX-2b/5b | Any (auto-translated) |
| **Video generation** | Animated scenes | AnimateDiff | Any (auto-translated) |
| **Video generation** | Lightweight t2v | ModelScope-1.7b | Any (auto-translated) |
| **Music** | Text-to-music | MusicGen (Meta) | Any (auto-translated) |
| **SFX** | Sound effect generation | AudioGen (Meta) | Any (auto-translated) |

---

## Quick Start

### 1. Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10 or 3.11 |
| NVIDIA GPU | CUDA 12.4 (recommended; CPU fallback available) |
| VRAM | 4 GB min, 8 GB+ recommended |
| Storage | 20 GB+ free |
| FFmpeg | any recent version |

### 2. Install

```bash
git clone --recurse-submodules https://github.com/olusholaoluyomi/ai-studio.git
cd ai-studio
make setup          # ~10–30 min on first run (downloads models)
```

### 3. Launch

```bash
make run            # Full studio — opens at http://localhost:7860
make run-voice      # Voice features only (faster startup)
make run-video      # Video & audio generation only
```

### 4. (Optional) Download large video models

```bash
make models         # Interactive downloader for CogVideoX, AnimateDiff, Whisper large-v3
```

---

## Studio Tabs

### Dubbing Studio
Upload any video or audio file (or paste a YouTube URL). The pipeline will:
1. Separate voice from background music (Demucs)
2. Transcribe speech (Whisper, 90+ languages)
3. Translate to your target language (Deep Translator)
4. Synthesise speech in the target language (Edge-TTS / Azure-TTS)
5. Merge back with original music and export

### Whisper Subtitles
Generate word-level subtitles in 90+ languages. Exports ASS, SSA, and SRT.
Word-level highlighting supported for karaoke-style display.

### Translation
Real-time and batch translation. Supports VOD files and live microphone input (Windows).

### Speech Generation

#### Edge-TTS — 100+ languages, 400+ voices
Microsoft's neural TTS engine. No API key needed.
Select any language and voice, adjust speed/pitch/volume.

#### F5-TTS — Zero-shot voice cloning
Upload 5–10 seconds of reference audio. The model clones that voice and speaks any text.
Supports both single-speaker and multi-speaker generation.

#### CosyVoice — Advanced multilingual cloning
9 GB model with superior naturalness for Chinese, English, Japanese, and Korean.

#### Kokoro — Top-ranked open-source TTS
Ranked #1 on HuggingFace TTS leaderboard. Supports EN, JA, ZH, FR, ES, PT, HI, IT.

### Audio Separation
Remove vocals, isolate instruments, or extract individual stems using
Demucs (MDX-Net enhanced). Works on any audio or video file.

### RVC Voice Conversion
Real-time voice style transfer. Upload an RVC model and convert any voice recording
to a different timbre or character.

### Video Generation

#### CogVideoX-2b / 5b
State-of-the-art open-source text-to-video. Generates 6-second clips at 480×720.
- Model: `THUDM/CogVideoX-2b` (Apache 2.0)
- VRAM: ~14 GB
- Prompts: any language (auto-translated to English)

#### AnimateDiff
Animate any text description using Stable Diffusion + a motion adapter.
- VRAM: ~6 GB
- Prompts: any language

#### ModelScope-1.7b
Lightweight, fast text-to-video. Good for quick previews.
- VRAM: ~6 GB
- Prompts: any language

### Music & SFX Generation

#### MusicGen (Meta)
Generate royalty-free background music from text.
Models: `small` (300M), `medium` (1.5B), `large` (3.3B), `melody`.

#### AudioGen (Meta)
Generate sound effects and ambient audio from text.

---

## Configuration

### Environment variables

Copy `config/.env.example` to `.env` in the project root:

```bash
cp config/.env.example .env
```

Key variables:

```env
STUDIO_PORT=7860          # Web UI port
LOG_LEVEL=WARNING         # DEBUG | INFO | WARNING | ERROR
HF_TOKEN=hf_xxx           # HuggingFace token (avoids rate limits)

# Optional Azure services (premium quality)
AZURE_SPEECH_KEY=
AZURE_SPEECH_REGION=eastus
AZURE_TRANSLATOR_KEY=
```

### settings.yaml

Edit `config/settings.yaml` for detailed model and feature configuration:

```yaml
voice_pro:
  whisper_model: large-v3      # tiny | base | small | medium | large-v3
  compute_type: float16        # float16 | int8 | float32
  default_tts: edge-tts        # edge-tts | f5-tts | cosyvoice | kokoro

video_generation:
  default_model: modelscope    # cogvideox | animatediff | modelscope
```

---

## GPU Requirements by Feature

| Feature | Minimum VRAM | Notes |
|---------|-------------|-------|
| Edge-TTS / Whisper tiny | 0 (CPU) | Fully CPU-capable |
| Whisper base/small | 2 GB | |
| Whisper large-v3 | 6 GB | |
| F5-TTS | 4 GB | |
| CosyVoice | 8 GB | 9 GB model |
| Kokoro | 2 GB | |
| Demucs (MDX-Net) | 4 GB | |
| RVC | 4 GB | |
| ModelScope-1.7b | 6 GB | |
| AnimateDiff | 6 GB | |
| CogVideoX-2b | 14 GB | |
| CogVideoX-5b | 24 GB | |
| MusicGen small | 4 GB | |
| MusicGen large | 8 GB | |

CPU-only machines can still use: Edge-TTS, Whisper (tiny/base), Deep Translator,
Subtitle generation, and ModelScope/AnimateDiff with patience (~10 min/clip).

---

## Project Structure

```
ai-studio/
├── voice-pro/              ← Voice-Pro submodule (speech, ASR, dubbing, RVC)
│   ├── app/                ← Gradio tabs and processing modules
│   ├── src/                ← Core config, VAD, utilities
│   ├── cosyvoice/          ← CosyVoice TTS integration
│   ├── rvc/                ← RVC voice conversion
│   └── third_party/        ← Matcha-TTS dependency
│
├── src/
│   ├── studio_app.py       ← Unified Gradio application entry point
│   └── extensions/
│       ├── video_generation.py   ← CogVideoX, AnimateDiff, ModelScope
│       └── audio_generation.py   ← MusicGen, AudioGen
│
├── config/
│   ├── .env.example        ← Environment variable template
│   └── settings.yaml       ← Master configuration
│
├── scripts/
│   ├── setup.sh            ← One-time installation script
│   ├── start.sh            ← Launcher (wraps studio_app.py)
│   └── download_models.sh  ← Interactive model downloader
│
├── models/                 ← Downloaded model weights (gitignored)
├── requirements.txt        ← Extra Python dependencies
├── Makefile                ← Developer commands
└── README.md
```

---

## Updating

```bash
make update     # Pulls latest Voice-Pro and upgrades Python packages
```

---

## License

- **AI Studio wrapper code**: MIT
- **Voice-Pro**: LGPL-2.1
- **CogVideoX**: Apache 2.0
- **AnimateDiff**: Apache 2.0
- **MusicGen / AudioGen**: MIT
- **Whisper**: MIT
- **F5-TTS**: MIT
- **Kokoro**: Apache 2.0
- **Demucs**: MIT
- **Edge-TTS**: MIT (client library; Microsoft service ToS applies)

---

## Credits

- [Voice-Pro](https://github.com/abus-aikorea/voice-pro) — abus-aikorea
- [CogVideoX](https://github.com/THUDM/CogVideo) — THUDM / Tsinghua
- [AnimateDiff](https://github.com/guoyww/AnimateDiff) — Yuwei Guo et al.
- [ModelScope text-to-video](https://huggingface.co/damo-vilab/text-to-video-ms-1.7b) — Alibaba DAMO
- [AudioCraft (MusicGen/AudioGen)](https://github.com/facebookresearch/audiocraft) — Meta
- [Whisper](https://github.com/openai/whisper) — OpenAI
- [F5-TTS](https://github.com/SWivid/F5-TTS) — SWivid
- [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M) — hexgrad
- [Demucs](https://github.com/facebookresearch/demucs) — Meta
- [RVC](https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI)
