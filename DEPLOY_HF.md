# Deploying AI Studio to HuggingFace Spaces

## Step-by-step

### 1. Create the Space
Go to https://huggingface.co/new-space and fill in:
- **Space name**: e.g. `ai-studio`
- **SDK**: Gradio
- **Hardware**:
  - Free CPU — TTS, Whisper, Subtitles, Translation work fine
  - T4-small ($0.60/hr) — adds F5-TTS, Kokoro, Demucs, RVC, ModelScope video
  - A10G ($1.05/hr) — adds CogVideoX, AnimateDiff, MusicGen large
- **Visibility**: Public or Private

### 2. Clone your new Space locally
```bash
git clone https://huggingface.co/spaces/YOUR_USERNAME/ai-studio hf-space
cd hf-space
```

### 3. Add this repo as a remote and push
```bash
# From inside the ai-studio project root:
git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/ai-studio
git push hf claude/ai-media-generation-ySbxe:main
```

Or copy the files into the cloned Space and push:
```bash
cp -r /path/to/ai-studio/* hf-space/
cd hf-space
git add .
git commit -m "initial deploy"
git push
```

### 4. Set Secrets (optional — for Azure services)
In Space Settings → Repository Secrets:
```
AZURE_SPEECH_KEY        = your-key
AZURE_SPEECH_REGION     = eastus
AZURE_TRANSLATOR_KEY    = your-key
HF_TOKEN                = hf_xxx   (avoids rate limits on model downloads)
```

### 5. Use the right requirements.txt
HF Spaces reads `requirements.txt` at the root automatically.
Rename the HF-specific one:
```bash
cp requirements-hf.txt requirements.txt
git add requirements.txt && git commit -m "use HF requirements" && git push hf
```

### 6. Wait for the build
First build takes ~10–20 minutes (model downloads).
Subsequent restarts are fast (models are cached).

---

## Hardware selection guide

| Space tier | Monthly cost | What works |
|-----------|-------------|-----------|
| Free CPU | $0 | Edge-TTS, Whisper (small), Translation, Subtitles |
| T4-small | ~$43 | + F5-TTS, Kokoro, Demucs, RVC, ModelScope video |
| T4-medium | ~$60 | + AnimateDiff, MusicGen medium |
| A10G small | ~$75 | + CogVideoX-2b, all features |
| A10G large | ~$110 | + CogVideoX-5b, MusicGen large |

For most users **T4-small** is the sweet spot.

---

## Troubleshooting

**Build times out**
- HF Spaces has a 30-min build limit. The `packages.txt` + `requirements.txt`
  approach should stay within that. If it fails, try removing `audiocraft`
  from requirements.txt (it's only needed for Music/SFX tabs).

**OOM on first inference**
- Lower the Whisper model in `config/settings.yaml`: `whisper_model: small`
- Use `--mode voice` to disable video generation

**ModuleNotFoundError for voice-pro modules**
- Make sure the submodule was cloned: `git submodule update --init --recursive`
- HF Spaces should handle this automatically via `.gitmodules`
