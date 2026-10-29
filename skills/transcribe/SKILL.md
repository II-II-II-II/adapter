---
name: transcribe
description: Transcribe a voice recording locally on the Apple GPU with MLX Whisper, save the transcript where the user wants it, then read it into the conversation as context. Use whenever the user mentions a recording, a voice memo, an .m4a/.mp3/.wav/.mp4 file, says they recorded a call, interview, meeting or note, asks to transcribe something, drops a filename from ~/Desktop/recordings, or says "I recorded this" / "listen to this" / "check out this call." Nothing is uploaded — the model runs on-device, which is why this is safe for interviews, client calls and anything with a real person's voice in it.
---

# Transcribe a recording

Audio in, transcript on disk, contents in the conversation. Four steps, and the
last one is the point — the transcript exists so it can be *used*, not filed.

**The default inbox is `~/Desktop/recordings`.** The user drops recordings there.

---

## 1. Find the recording

If the user named a file, use it. Otherwise look in the inbox:

```bash
ls -lt ~/Desktop/recordings/*.{m4a,mp3,wav,mp4,aac,flac} 2>/dev/null
```

- **One file** → use it, say which one you picked.
- **Several** → list them newest first with size and modified time, and ask which. Don't guess.
- **None** → say the inbox is empty and ask where the file is. Don't go hunting across the disk.

Also check whether a transcript already exists next to it or in the likely output
directory, so you don't spend four minutes redoing work.

## 2. Transcribe

```bash
python3 ~/.claude/skills/transcribe/transcribe.py "<audio>" "<output.txt>"
```

**Run it with `run_in_background: true`.** Real recordings take minutes — roughly
1–3 minutes per 10 minutes of audio on an M-series GPU. Don't block on it, and
don't wrap it in a foreground timeout.

It writes two files:

| File | What it's for |
|---|---|
| `<output>.txt` | plain prose — what you read for context |
| `<output>.timed.txt` | `[hh:mm:ss]` per segment — for checking a disputed line against the audio |

**Model:** `medium` is the default and is proven on real interview audio. Pass
`--model turbo` when speed matters or the audio is rough — it's faster *and*
usually more accurate. First use of any model downloads it once.

**Language is pinned to `en` deliberately.** If the user needs another language
pass `--language <code>`. Avoid auto-detect: a quiet or noisy opening makes
Whisper guess wrong, and it then "translates" the whole file into the wrong
language and falls into repetition loops. This has actually happened.

## 3. Ask where to save it — default is the current directory

**Before transcribing**, confirm the destination. Default to the directory the
conversation is working in, with a name derived from the recording:

> "I'll save it as `./Acme_Prep.txt` — or somewhere else?"

If the project has an obvious transcripts directory (`transcripts/`,
`source/transcripts/`, `notes/`), offer that instead. One short question, then go.

## 4. Read it into the conversation — this is the whole point

Once it's written, **read the transcript** so it becomes usable context.

- **Under ~4,000 words** → read the whole file.
- **Longer** → read it in sections rather than one shot, and say what you're
  looking for as you go.
- **Looking for something specific** → grep the timed file and read around the
  hits, so you can cite `[00:14:22]` rather than paraphrase.

Then **report what's in it**, pitched at why they recorded it:

- A call or interview → what was said that they'd want to act on, direct quotes for anything important, and anything that contradicts what they believed going in.
- A voice memo or note → the substance, organized, not a transcript dump.
- A meeting → decisions, owners, open questions.

**Quote exactly when it matters.** The reason to transcribe rather than rely on
memory is that memory reshapes things — a number inverts, a constraint hardens,
a maybe becomes a yes. Verbatim quotes are the value being added.

---

## Notes and limits

**No speaker labels.** Whisper doesn't do diarization, so a two-person call comes
back as one stream. Usually you can infer who's talking from content, but say so
rather than attributing a line to the wrong person — and when it's genuinely
ambiguous, say it's ambiguous.

**Transcription errors cluster on proper nouns.** Names, companies, and products
get mangled — a four-letter company name came back as a common English word, and
a staffing firm's name as a different, larger company's.
When a name looks odd, flag it rather than repeating it confidently — and once
the real spelling is known, use it.

**Nothing is uploaded.** `mlx_whisper` runs the model on the local GPU. Say this
if the user hesitates about recordings of other people.

**Don't move or delete the original.** Leave it in the inbox; the user decides
when it's done.
