#!/usr/bin/env python3
"""Generate the listening deck's audio: a male and a female neural voice, each at
normal and slow speed, for every phrase. Files are cached in media/ and only
generated when missing.

Voices (open-source, run locally):
  male    Piper "fr_FR-tom-medium" via sherpa-onnx
  female  Kokoro v1.0 "ff_siwis"

Setup (models download from GitHub releases into models/):
  pip install sherpa-onnx kokoro-onnx soundfile
  python3 audio.py --fetch
"""
import argparse
import hashlib
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "models"
MEDIA = ROOT / "media"
PIPER = "vits-piper-fr_FR-tom-medium"
DOWNLOADS = {
    f"{PIPER}.tar.bz2": f"https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/{PIPER}.tar.bz2",
    "kokoro-v1.0.onnx": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx",
    "voices-v1.0.bin": "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin",
}
SLOW = 0.75
VARIANTS = {  # field name -> (voice, speed)
    "AudioMale": ("male", 1.0),
    "AudioMaleSlow": ("male", SLOW),
    "AudioFemale": ("female", 1.0),
    "AudioFemaleSlow": ("female", SLOW),
}


def fetch():
    MODELS.mkdir(exist_ok=True)
    for name, url in DOWNLOADS.items():
        dest = MODELS / name
        if not dest.exists():
            print(f"downloading {name}")
            urllib.request.urlretrieve(url, dest)
    if not (MODELS / PIPER).exists():
        with tarfile.open(MODELS / f"{PIPER}.tar.bz2") as t:
            t.extractall(MODELS)


def filename(text: str, field: str) -> str:
    digest = hashlib.sha1(f"{field}|{text}".encode()).hexdigest()[:12]
    return f"ef_{field.lower()}_{digest}.mp3"


class Voices:
    def __init__(self):
        import sherpa_onnx
        from kokoro_onnx import Kokoro
        d = MODELS / PIPER
        self.piper = sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(d / "fr_FR-tom-medium.onnx"), tokens=str(d / "tokens.txt"),
                    data_dir=str(d / "espeak-ng-data")),
                num_threads=4)))
        self.kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))

    def synth(self, text: str, voice: str, speed: float):
        if voice == "male":
            r = self.piper.generate(text, sid=0, speed=speed)
            return r.samples, r.sample_rate
        return self.kokoro.create(text, voice="ff_siwis", speed=speed, lang="fr-fr")


def write_mp3(samples, rate, dest: Path):
    import numpy as np
    import soundfile as sf
    wav = dest.with_suffix(".wav")
    pad = np.zeros(int(rate * 0.15), dtype=np.float32)
    sf.write(wav, np.concatenate([pad, np.asarray(samples, dtype=np.float32), pad]), rate)
    # Even out loudness between the two voices, then encode.
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "1",
                    "-b:a", "64k", str(dest)], check=True)
    wav.unlink()


def generate(phrases, voices=None):
    """Make sure every phrase has all four audio files; return {French: {field: filename}}."""
    MEDIA.mkdir(exist_ok=True)
    out = {}
    for i, p in enumerate(phrases, 1):
        files = {}
        for field, (voice, speed) in VARIANTS.items():
            name = filename(p["Speak"], field)
            dest = MEDIA / name
            if not dest.exists():
                voices = voices or Voices()
                samples, rate = voices.synth(p["Speak"], voice, speed)
                write_mp3(samples, rate, dest)
            files[field] = name
        out[p["French"]] = files
        if i % 25 == 0:
            print(f"  audio {i}/{len(phrases)}", file=sys.stderr)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="download the voice models")
    if ap.parse_args().fetch:
        fetch()
