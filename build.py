#!/usr/bin/env python3
"""Build the Expressions françaises Anki deck.

Reads data/phrases.txt, data/listening_examples.txt and the templates in anki/,
generates the audio (see audio.py), then writes:
  dist/Expressions-francaises.apkg   the main deck (produce + recognise cards)
  dist/Ecoute.apkg                   the listening deck
  dist/phrases.tsv                   the same data as a spreadsheet-friendly table
  dist/phrases.json                  the same data as JSON (used by the preview page)

Usage:
  pip install genanki sherpa-onnx kokoro-onnx soundfile   (and ffmpeg)
  python3 audio.py --fetch      # once: download the voice models
  python3 build.py
"""
import csv
import json
import re
import sys
from pathlib import Path

import genanki

import audio

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "phrases.txt"
EXAMPLES = ROOT / "data" / "listening_examples.txt"
TEMPLATES = ROOT / "anki"
DIST = ROOT / "dist"

DECK_NAME = "Expressions françaises"
TIER_NAMES = {
    "1": "1 · Le noyau (core)",
    "2": "2 · La vie quotidienne (daily life)",
    "3": "3 · La fluidité (fluency)",
}
# Fixed IDs so re-importing a rebuilt deck updates cards instead of duplicating them.
MODEL_ID = 1_712_204_617
DECK_IDS = {"1": 2_059_400_111, "2": 2_059_400_112, "3": 2_059_400_113}
LISTEN_MODEL_ID = 1_712_204_618
LISTEN_DECK_ID = 2_059_400_200
LISTEN_DECK_NAME = "Expressions françaises — Écoute (listening)"

COLUMNS = ["French", "English", "Literal", "Spoken", "Register", "Notes", "Pattern", "Swaps"]
TEXT_FIELDS = COLUMNS + ["Theme", "Tier", "Heard", "HeardEnglish", "BuiltOn"]
NOTE_FIELDS = TEXT_FIELDS + list(audio.VARIANTS)
REGISTERS = {"N", "F", "Fam", "A"}


def speakable(french: str) -> str:
    """Text for text-to-speech: drop gender endings, quote marks and ellipses."""
    s = re.sub(r"\((?:e|le|ne|ière|se)\)", "", french)
    s = re.sub(r"\s*\((?:[^)]*)\)", "", s)
    s = s.replace("« … »", "").replace("…", "").replace("«", "").replace("»", "")
    s = re.sub(r"([.?!])\s*/\s*", r"\1 ", s)
    s = s.replace(" / ", ", ").replace(" — ", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return re.sub(r",\s*([?!.])", r" \1", s)


def parse(path: Path):
    phrases, errors = [], []
    tier = theme_id = theme = None
    seen = set()
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("@"):
            tier, theme_id, theme = [p.strip() for p in line[1:].split("|")]
            continue
        if theme is None:
            errors.append(f"line {n}: phrase before any @ section")
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) > len(COLUMNS):
            errors.append(f"line {n}: {len(parts)} fields (max {len(COLUMNS)})")
            continue
        parts += [""] * (len(COLUMNS) - len(parts))
        row = dict(zip(COLUMNS, parts))
        row["Register"] = row["Register"] or "N"
        if not row["French"] or not row["English"]:
            errors.append(f"line {n}: French and English are required")
        if row["Register"] not in REGISTERS:
            errors.append(f"line {n}: unknown register {row['Register']!r}")
        if row["Swaps"] and not row["Pattern"]:
            errors.append(f"line {n}: Swaps given without a Pattern")
        if row["French"] in seen:
            errors.append(f"line {n}: duplicate phrase {row['French']!r}")
        seen.add(row["French"])
        row.update(Theme=theme, Tier=tier, ThemeId=theme_id)
        phrases.append(row)
    if errors:
        sys.exit("phrases.txt has problems:\n  " + "\n  ".join(errors))
    return phrases


def add_examples(phrases):
    """Attach what the audio says. Fragments ("Je voudrais…") get a full example
    sentence from listening_examples.txt; every other phrase is spoken as written."""
    examples = {}
    for raw in EXAMPLES.read_text(encoding="utf-8").splitlines():
        if raw.strip() and not raw.startswith("#"):
            key, fr, en = [x.strip() for x in raw.split("|")]
            examples[key] = (fr, en)
    known = {p["French"] for p in phrases}
    unknown = [k for k in examples if k not in known]
    missing = [p["French"] for p in phrases if "…" in p["French"] and p["French"] not in examples]
    if unknown or missing:
        sys.exit(f"listening_examples.txt: unknown phrases {unknown}, fragments without an example {missing}")
    for p in phrases:
        fr, en = examples.get(p["French"], (p["French"], p["English"]))
        p.update(Heard=fr, HeardEnglish=en, BuiltOn=p["French"] if p["French"] in examples else "",
                 Speak=speakable(fr))


def template(name: str) -> str:
    html = (TEMPLATES / f"{name}.html").read_text(encoding="utf-8")
    voices = (TEMPLATES / "listen_voices.html").read_text(encoding="utf-8")
    html = html.replace("%%META%%", (TEMPLATES / "meta.html").read_text(encoding="utf-8"))
    html = html.replace("%%VOICES_COMPACT%%", voices.replace('class="voices"', 'class="voices compact"'))
    html = html.replace("%%VOICES%%", voices)
    html = html.replace("%%EXAMPLE%%", (TEMPLATES / "example.html").read_text(encoding="utf-8"))
    return html.replace("%%DETAILS%%", (TEMPLATES / "details.html").read_text(encoding="utf-8"))


def model(model_id, name, templates):
    return genanki.Model(
        model_id, name,
        fields=[{"name": f} for f in NOTE_FIELDS],
        templates=[{"name": n, "qfmt": template(q), "afmt": template(a)} for n, q, a in templates],
        css=(TEMPLATES / "style.css").read_text(encoding="utf-8"),
        sort_field_index=0,
    )


def note_fields(p, sounds):
    return [p[f] for f in TEXT_FIELDS] + [f"[sound:{sounds[f]}]" for f in audio.VARIANTS]


def build_main(phrases, media, out: Path):
    m = model(MODEL_ID, "Expressions françaises (phrase)", [
        ("1 · Produce (EN → FR)", "produce_front", "produce_back"),
        ("2 · Recognise (FR → EN)", "recognize_front", "recognize_back"),
    ])
    decks = {t: genanki.Deck(DECK_IDS[t], f"{DECK_NAME}::{name}") for t, name in TIER_NAMES.items()}
    for position, p in enumerate(phrases, 1):
        tags = [f"tier::{p['Tier']}", f"theme::{p['ThemeId']}", f"register::{p['Register']}"]
        if p["Pattern"]:
            tags.append("frame")
        decks[p["Tier"]].add_note(genanki.Note(
            model=m, fields=note_fields(p, media[p["French"]]), tags=tags,
            guid=genanki.guid_for("expressions-francaises", p["French"]),
            due=position,  # new cards are introduced in file order
        ))
    write_package(list(decks.values()), phrases, media, out)


def build_listening(phrases, media, out: Path):
    """One card per phrase: audio on the front, transcript and meaning on the back."""
    m = model(LISTEN_MODEL_ID, "Expressions françaises (listening)", [
        ("Listen (audio → FR + EN)", "listen_front", "listen_back"),
    ])
    deck = genanki.Deck(LISTEN_DECK_ID, LISTEN_DECK_NAME)
    for position, p in enumerate(phrases, 1):
        deck.add_note(genanki.Note(
            model=m, fields=note_fields(p, media[p["French"]]),
            tags=[f"tier::{p['Tier']}", f"theme::{p['ThemeId']}", "listening"],
            guid=genanki.guid_for("expressions-francaises-listening", p["French"]),
            due=position,
        ))
    write_package([deck], phrases, media, out)


def write_package(decks, phrases, media, out: Path):
    package = genanki.Package(decks)
    package.media_files = [str(audio.MEDIA / name) for p in phrases for name in media[p["French"]].values()]
    package.write_to_file(out)
    print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1e6:.0f} MB, {len(package.media_files)} audio files)")


def main():
    phrases = parse(DATA)
    add_examples(phrases)
    DIST.mkdir(exist_ok=True)
    if "--listening-sample" in sys.argv:
        french = sys.argv[sys.argv.index("--listening-sample") + 1]
        sample = [p for p in phrases if p["French"] == french]
        build_listening(sample, audio.generate(sample), DIST / "Ecoute-sample.apkg")
        return

    media = audio.generate(phrases)
    build_main(phrases, media, DIST / "Expressions-francaises.apkg")
    build_listening(phrases, media, DIST / "Ecoute.apkg")

    with open(DIST / "phrases.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Tier", "Theme"] + COLUMNS + ["Example", "Example (English)"])
        for p in phrases:
            w.writerow([p["Tier"], p["Theme"]] + [p[c] for c in COLUMNS]
                       + ([p["Heard"], p["HeardEnglish"]] if p["BuiltOn"] else ["", ""]))
    (DIST / "phrases.json").write_text(
        json.dumps(phrases, ensure_ascii=False, indent=1), encoding="utf-8")

    by_tier = {t: sum(p["Tier"] == t for p in phrases) for t in TIER_NAMES}
    frames = sum(bool(p["Pattern"]) for p in phrases)
    print(f"{len(phrases)} phrases ({', '.join(f'tier {t}: {c}' for t, c in by_tier.items())}), "
          f"{frames} reusable frames, {len(phrases) * 2} main cards + {len(phrases)} listening cards")


if __name__ == "__main__":
    main()
