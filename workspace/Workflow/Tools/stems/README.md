# Stem splitting (Demucs)

Splits a music track into `drums`, `bass`, `other` (melody/harmony) and `vocals`, so explanations can run with the drums down and payoffs bring them back. Optional. Install once into a local venv: `python3 -m venv Workflow/Tools/stems/.venv && Workflow/Tools/stems/.venv/bin/pip install demucs` (Demucs is MIT-licensed; PyTorch is pulled in, so it is a large download). The model weights (htdemucs, ~80 MB) are cached in `~/.cache/torch/hub/` on first run.

```bash
Workflow/Tools/stems/.venv/bin/python -m demucs -n htdemucs -o Videos/<video>/11-Work/scratch/stems <track.wav|mp3>
```

Speed on a laptop CPU in the author's test: ~0.5× real time (a 4-minute track took about 2 minutes); a GPU is faster. The four stems sum back to the mix. Listen to each one solo for separation artefacts before using it under narration. Keep the music's licence and credit rules: splitting doesn't change them.
