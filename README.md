# Expressions françaises

Two Anki decks built from the same 463 French phrases, the smallest set I could put together that covers what you need to hold a real conversation. They teach whole phrases rather than single words, and 75 of the phrases are **reusable frames** (`Je voudrais + [nom]`, `J'ai envie de + [infinitif]`, `Ça fait + [durée] + que…`) that you can fill with other words to make new sentences.

| Deck | Download | Cards |
|---|---|---|
| **Expressions françaises**: speaking and meaning | [`dist/Expressions-francaises.apkg`](dist/Expressions-francaises.apkg) | 926 (two per phrase) |
| **Écoute**: listening | [`dist/Ecoute.apkg`](dist/Ecoute.apkg) | 463 (one per phrase) |

Every phrase has recorded audio in two neural voices, male and female, each at normal speed and at 75% speed. The recordings are stored inside the decks, so they sound the same on your Mac, your phone, or anywhere else you use Anki.

## What's in it

| Tier | Subdeck | Phrases | What it gets you |
|---|---|---|---|
| 1 | Le noyau (core) | 205 | Greetings, politeness, asking someone to repeat or slow down, introducing yourself, the core frames, questions, reactions and fillers, feelings, opinions |
| 2 | La vie quotidienne (daily life) | 131 | Cafés and restaurants, shopping, directions and transport, making plans, hotels, emergencies and health, small talk, the phone |
| 3 | La fluidité (fluency) | 127 | Storytelling connectors, nuance and hedging, everyday idioms, invitations and empathy, disagreeing politely |

Each phrase has:

- **French** and **English**
- **Heard as**: how people actually say it out loud (`Je ne sais pas` → *Chais pas*, `Il y a` → *Y'a*)
- **Word for word**: a literal gloss that shows how the French is built (`J'ai faim` = *I have hunger*)
- **Register**: neutral, formal, casual or slang, so you don't say *Salut* to your landlord
- **Reusable frame** with ready-made fillers for the generative phrases
- **Notes** on traps, false friends and culture (`Je suis chaud` doesn't mean you're hot; `Finalement` doesn't mean "finally")
- **In a sentence**: phrases that are fragments (`Je voudrais…`) come with a complete example sentence (*Je voudrais un café, s'il vous plaît.*), and the audio speaks that sentence

## The cards

**Expressions françaises** (main deck), two cards per phrase:

1. **Produce (EN → FR)**: see the English and say the French aloud. This is the card that builds speaking, and the front has an optional word-for-word hint.
2. **Recognise (FR → EN)**: see and hear the French, and recall what it means.

**Écoute** (listening deck), one card per phrase. The front has only play buttons: a male and a female voice, each with **Play** and **Slow**. Work out what was said and what it means, then flip to see the sentence, its English, and the notes.

New cards come in the order of `data/phrases.txt`, with the most useful first. If you do the first ~100 you can already get through a polite conversation.

## Setup on Mac

1. Install [Anki](https://apps.ankiweb.net) for desktop.
2. Double-click each `.apkg` file, or use **File → Import** in Anki.
3. Click the gear next to each deck → **Options** and set:
   - **Don't play audio automatically**: on. Otherwise Anki plays all four recordings in a row as each card appears. With it on, you press the voice you want.
   - **New cards/day**: 15–20 for the main deck (8–10 phrases), about 10 for Écoute.
   - **Bury new siblings**: on, if you want a phrase's two main-deck cards on different days.

If you imported an earlier version of the main deck, delete it before importing this one. The card layout has changed to add the recorded voices.

## How to study

- **Say every answer out loud** before you flip the card. You learn to speak by speaking.
- When a card has a frame, make one new sentence of your own with it before moving on.
- In Écoute, start with the normal speed. Use **Slow** only after you've tried, and switch voices to train your ear on both.
- Mark a card *Again* if you hesitated. Speed counts in conversation.

## Editing and rebuilding

- [`data/phrases.txt`](data/phrases.txt): the phrases, one per line, fields separated by `|`
- [`data/listening_examples.txt`](data/listening_examples.txt): the complete sentences spoken for fragment phrases
- [`anki/`](anki/): the card design (`style.css` and the `*.html` layouts)
- [`audio.py`](audio.py): the voices. Male: Piper *fr_FR-tom-medium*. Female: Kokoro *ff_siwis*. Both are open-source and run locally.

```sh
pip install genanki sherpa-onnx kokoro-onnx soundfile   # and install ffmpeg
python3 audio.py --fetch    # once: downloads the voice models (~450 MB) into models/
python3 build.py
```

Audio is cached in `media/`, so a rebuild only records phrases that are new or changed. The build writes both decks, plus `dist/phrases.tsv` and `dist/phrases.json` with the same data. Notes keep stable IDs, so if you re-import a rebuilt deck, Anki updates your existing cards and keeps your review history.
