#!/usr/bin/env python3
"""Build the Expressions françaises Anki deck.

Reads data/phrases.txt and the templates in anki/, then writes:
  dist/Expressions-francaises.apkg   the deck to import into Anki
  dist/phrases.tsv                   the same data as a spreadsheet-friendly table
  dist/phrases.json                  the same data as JSON (used by the preview page)

Usage: python3 build.py          (requires: pip install genanki)
"""
import csv
import json
import re
import sys
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "phrases.txt"
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

FIELDS = ["French", "English", "Literal", "Spoken", "Register", "Notes",
          "Pattern", "Swaps", "Theme", "Tier", "Speak"]
COLUMNS = FIELDS[:8]  # the columns written in phrases.txt
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
        row.update(Theme=theme, Tier=tier, ThemeId=theme_id, Speak=speakable(row["French"]))
        phrases.append(row)
    if errors:
        sys.exit("phrases.txt has problems:\n  " + "\n  ".join(errors))
    return phrases


def template(name: str) -> str:
    html = (TEMPLATES / f"{name}.html").read_text(encoding="utf-8")
    html = html.replace("%%META%%", (TEMPLATES / "meta.html").read_text(encoding="utf-8"))
    html = html.replace("%%VOICES%%", (TEMPLATES / "listen_voices.html").read_text(encoding="utf-8"))
    return html.replace("%%DETAILS%%", (TEMPLATES / "details.html").read_text(encoding="utf-8"))


def build_model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Expressions françaises (phrase)",
        fields=[{"name": f} for f in FIELDS],
        templates=[
            {"name": "1 · Produce (EN → FR)",
             "qfmt": template("produce_front"), "afmt": template("produce_back")},
            {"name": "2 · Recognise (FR → EN)",
             "qfmt": template("recognize_front"), "afmt": template("recognize_back")},
        ],
        css=(TEMPLATES / "style.css").read_text(encoding="utf-8"),
        sort_field_index=0,
    )


def build_listening(phrases, out: Path):
    """The listening deck: one card per phrase, audio only on the front."""
    import audio

    examples = {}
    for n, raw in enumerate((ROOT / "data" / "listening_examples.txt").read_text(encoding="utf-8").splitlines(), 1):
        if raw.strip() and not raw.startswith("#"):
            key, fr, en = [x.strip() for x in raw.split("|")]
            examples[key] = (fr, en)
    known = {p["French"] for p in parse(DATA)}
    unknown = [k for k in examples if k not in known]
    missing = [p["French"] for p in phrases if "…" in p["French"] and p["French"] not in examples]
    if unknown or missing:
        sys.exit(f"listening_examples.txt: unknown phrases {unknown}, fragments without an example {missing}")

    heard = []
    for p in phrases:
        fr, en = examples.get(p["French"], (p["French"], p["English"]))
        built_on = p["French"] if p["French"] in examples else ""
        heard.append(dict(p, Heard=fr, HeardEnglish=en, BuiltOn=built_on, Speak=speakable(fr)))
    phrases = heard

    media = audio.generate(phrases)
    fields = FIELDS + ["Heard", "HeardEnglish", "BuiltOn"] + list(audio.VARIANTS)
    model = genanki.Model(
        LISTEN_MODEL_ID,
        "Expressions françaises (listening)",
        fields=[{"name": f} for f in fields],
        templates=[{"name": "Listen (audio → FR + EN)",
                    "qfmt": template("listen_front"), "afmt": template("listen_back")}],
        css=(TEMPLATES / "style.css").read_text(encoding="utf-8"),
        sort_field_index=0,
    )
    deck = genanki.Deck(LISTEN_DECK_ID, LISTEN_DECK_NAME)
    files = []
    for position, p in enumerate(phrases, 1):
        sounds = media[p["French"]]
        files += [audio.MEDIA / name for name in sounds.values()]
        deck.add_note(genanki.Note(
            model=model,
            fields=[p[f] for f in fields[:len(FIELDS) + 3]] + [f"[sound:{sounds[f]}]" for f in audio.VARIANTS],
            tags=[f"tier::{p['Tier']}", f"theme::{p['ThemeId']}", "listening"],
            guid=genanki.guid_for("expressions-francaises-listening", p["French"]),
            due=position,
        ))
    package = genanki.Package(deck)
    package.media_files = [str(f) for f in files]
    package.write_to_file(out)
    print(f"{len(phrases)} listening cards, {len(files)} audio files")
    print(f"wrote {out}")


def main():
    phrases = parse(DATA)
    if "--listening-sample" in sys.argv:
        french = sys.argv[sys.argv.index("--listening-sample") + 1]
        DIST.mkdir(exist_ok=True)
        build_listening([p for p in phrases if p["French"] == french], DIST / "Ecoute-sample.apkg")
        return
    if "--listening" in sys.argv:
        DIST.mkdir(exist_ok=True)
        build_listening(phrases, DIST / "Ecoute.apkg")
        return

    model = build_model()
    decks = {t: genanki.Deck(DECK_IDS[t], f"{DECK_NAME}::{name}") for t, name in TIER_NAMES.items()}

    for position, p in enumerate(phrases, 1):
        tags = [f"tier::{p['Tier']}", f"theme::{p['ThemeId']}", f"register::{p['Register']}"]
        if p["Pattern"]:
            tags.append("frame")
        note = genanki.Note(
            model=model,
            fields=[p[f] for f in FIELDS],
            tags=tags,
            guid=genanki.guid_for("expressions-francaises", p["French"]),
            due=position,  # new cards are introduced in file order
        )
        decks[p["Tier"]].add_note(note)

    DIST.mkdir(exist_ok=True)
    genanki.Package(list(decks.values())).write_to_file(DIST / "Expressions-francaises.apkg")

    with open(DIST / "phrases.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["Tier", "Theme"] + COLUMNS)
        for p in phrases:
            w.writerow([p["Tier"], p["Theme"]] + [p[c] for c in COLUMNS])

    (DIST / "phrases.json").write_text(
        json.dumps(phrases, ensure_ascii=False, indent=1), encoding="utf-8")

    by_tier = {t: sum(p["Tier"] == t for p in phrases) for t in TIER_NAMES}
    frames = sum(bool(p["Pattern"]) for p in phrases)
    print(f"{len(phrases)} phrases ({', '.join(f'tier {t}: {c}' for t, c in by_tier.items())}), "
          f"{frames} reusable frames, {len(phrases) * 2} cards")
    print(f"wrote {DIST / 'Expressions-francaises.apkg'}")


if __name__ == "__main__":
    main()
