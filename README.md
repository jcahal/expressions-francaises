# Expressions françaises

An Anki deck of 472 French phrases, the smallest set I could put together that covers what you need to hold a real conversation. It teaches whole phrases rather than single words, and 75 of them are **reusable frames** (`Je voudrais + [nom]`, `J'ai envie de + [infinitif]`, `Ça fait + [durée] + que…`) that you can fill with other words to make new sentences.

**Download the deck:** [`dist/Expressions-francaises.apkg`](dist/Expressions-francaises.apkg)

## What's in it

| Tier | Subdeck | Phrases | What it gets you |
|---|---|---|---|
| 1 | Le noyau (core) | 209 | Greetings, politeness, asking someone to repeat or slow down, introducing yourself, the core frames, questions, reactions and fillers, feelings, opinions |
| 2 | La vie quotidienne (daily life) | 132 | Cafés and restaurants, shopping, directions and transport, making plans, hotels, emergencies and health, small talk, the phone |
| 3 | La fluidité (fluency) | 131 | Storytelling connectors, nuance and hedging, everyday idioms, invitations and empathy, disagreeing politely |

Each phrase has:

- **French** and **English**
- **Heard as**: how people actually say it out loud (`Je ne sais pas` → *Chais pas*, `Il y a` → *Y'a*)
- **Word for word**: a literal gloss that shows how the French is built (`J'ai faim` = *I have hunger*)
- **Register**: neutral, formal, casual or slang, so you don't say *Salut* to your landlord
- **Reusable frame** with ready-made fillers for the generative phrases
- **Notes** on traps, false friends and culture (`Je suis chaud` doesn't mean you're hot; `Finalement` doesn't mean "finally")
- **Audio** from your Mac's French voice, via Anki's built-in text-to-speech

Each phrase makes two cards:

1. **Produce (EN → FR)**: see the English and say the French aloud. This is the card that builds speaking, and the front has an optional word-for-word hint.
2. **Recognise (FR → EN)**: see and hear the French, and recall what it means.

New cards come in the order of `data/phrases.txt`, with the most useful first. If you do the first ~100 you can already get through a polite conversation.

## Setup on Mac

1. Install [Anki](https://apps.ankiweb.net) for desktop.
2. Double-click `Expressions-francaises.apkg`, or use **File → Import** in Anki.
3. **Get a good French voice** (this matters): open **System Settings → Accessibility → Spoken Content → System Voice → Manage Voices…**, go to **French (France)** and download **Thomas** or **Amélie**. Pick the *Premium* or *Enhanced* version if it's offered. Anki then uses it automatically.
4. Click the gear next to **Expressions françaises → Options** and set:
   - **New cards/day**: 15–20 (that's 8–10 phrases, since each phrase makes two cards)
   - **Bury new siblings**: on, if you want a phrase's two cards on different days

## How to study

- **Say every answer out loud** before you flip the card. You learn to speak by speaking.
- When a card has a frame, make one new sentence of your own with it before moving on.
- On recognition cards, try to understand the audio before you read the text.
- Mark a card *Again* if you hesitated. Speed counts in conversation.

## Editing and rebuilding

All the content is in [`data/phrases.txt`](data/phrases.txt): one phrase per line, fields separated by `|`. The card design is in [`anki/`](anki/), with `style.css` for the look and the `*.html` files for the card layouts.

```sh
pip install genanki
python3 build.py
```

This writes `dist/Expressions-francaises.apkg`, plus `dist/phrases.tsv` and `dist/phrases.json` with the same data. Notes keep stable IDs, so if you re-import a rebuilt deck Anki updates your existing cards and keeps your review history.
