"""Transcribe an audio recording locally — Apple GPU, NVIDIA GPU, or CPU.

Usage:
    python3 transcribe.py <audio> <output.txt> [--model NAME] [--language CODE]

Writes two files:
    <output.txt>            plain prose
    <output>.timed.txt      the same text with [hh:mm:ss] markers per segment

The timestamped file exists because a disputed line in a transcript needs to be
checkable against the recording rather than argued about. Whisper returns these
timings for free; discarding them is a waste.

NOTHING LEAVES THE MACHINE on any backend. No API, no upload. That matters when
the recording is an interview, a client call, or anything with a real person's
voice in it.

BACKENDS, chosen automatically:
    mlx    Apple Silicon GPU, via mlx-whisper
    cuda   NVIDIA GPU, via faster-whisper
    cpu    anything else, via faster-whisper (5-15x slower; still works)

setup.sh writes its choice to .adapter_backend. Override with --backend.

LANGUAGE IS PASSED EXPLICITLY ON PURPOSE. Whisper auto-detects from the opening
seconds, and a quiet or noisy start can make it guess wrong. When that happens
it doesn't just mislabel the output — it "translates" the entire file into the
wrong language and falls into repetition loops. Pass --language none only if you
actually want auto-detect.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Same short names across backends so the docs and skills don't have to branch.
MLX_MODELS = {
    "tiny": "mlx-community/whisper-tiny-mlx",
    "base": "mlx-community/whisper-base-mlx",
    "small": "mlx-community/whisper-small-mlx",
    "medium": "mlx-community/whisper-medium-mlx",
    "large": "mlx-community/whisper-large-v3-mlx",
    "turbo": "mlx-community/whisper-large-v3-turbo",
}

FW_MODELS = {
    "tiny": "tiny",
    "base": "base",
    "small": "small",
    "medium": "medium",
    "large": "large-v3",
    "turbo": "large-v3-turbo",  # needs faster-whisper >= 1.0.3
}

MODEL_NAMES = sorted(MLX_MODELS)


def stamp(seconds):
    s = int(seconds)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def detect_backend():
    """What setup.sh decided, or a live guess if it never ran."""
    marker = ROOT / ".adapter_backend"
    if marker.exists():
        name = marker.read_text().strip()
        if name in {"mlx", "cuda", "cpu"}:
            return name

    try:
        import mlx_whisper  # noqa: F401
        return "mlx"
    except ImportError:
        pass

    try:
        import torch  # noqa: F401
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass

    try:
        import faster_whisper  # noqa: F401
        return "cpu"
    except ImportError:
        sys.exit(
            "No transcription backend installed.\n"
            "Run ./setup.sh, or install one by hand:\n"
            "  Apple Silicon:  pip install mlx-whisper\n"
            "  everything else: pip install faster-whisper"
        )


def missing(package):
    sys.exit(
        f"\n{package} isn't installed in the Python you're running.\n"
        f"  Interpreter: {sys.executable}\n\n"
        "Almost always this means the virtualenv isn't active. Try:\n"
        "  source .venv/bin/activate\n"
        "  ./.venv/bin/python source/transcribe.py ...   # or call it directly\n\n"
        "If you've never run setup:  ./setup.sh"
    )


def transcribe_mlx(audio, model, language):
    try:
        import mlx_whisper
    except ImportError:
        missing("mlx-whisper")

    result = mlx_whisper.transcribe(
        str(audio),
        path_or_hf_repo=MLX_MODELS[model],
        language=language,
        condition_on_previous_text=False,  # stops one bad segment cascading into a loop
        verbose=True,
    )
    segments = [(s["start"], s["text"].strip()) for s in result.get("segments", [])]
    return result["text"].strip(), segments


def transcribe_faster(audio, model, language, device):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        missing("faster-whisper")

    compute_type = "float16" if device == "cuda" else "int8"
    try:
        wm = WhisperModel(FW_MODELS[model], device=device, compute_type=compute_type)
    except Exception as e:
        if device != "cuda":
            raise
        print(f"\nCUDA failed to initialise ({e}).\nFalling back to CPU.\n", file=sys.stderr)
        wm = WhisperModel(FW_MODELS[model], device="cpu", compute_type="int8")

    stream, _info = wm.transcribe(
        str(audio),
        language=language,
        condition_on_previous_text=False,  # see note in transcribe_mlx
        vad_filter=True,                   # drops long silences; keeps timings honest
    )

    segments, parts = [], []
    for seg in stream:  # a generator — work happens as we iterate
        text = seg.text.strip()
        segments.append((seg.start, text))
        parts.append(text)
        print(f"[{stamp(seg.start)}] {text}")

    return " ".join(parts).strip(), segments


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("output")
    ap.add_argument(
        "--model",
        default="medium",
        choices=MODEL_NAMES,
        help="medium is the proven default. turbo is faster and often more "
        "accurate; large is slowest. First use of a model downloads it.",
    )
    ap.add_argument(
        "--language",
        default="en",
        help='ISO code, or "none" for auto-detect (read the module docstring '
        "before you do that).",
    )
    ap.add_argument(
        "--backend",
        choices=["mlx", "cuda", "cpu"],
        help="Override hardware detection.",
    )
    args = ap.parse_args()

    audio = Path(args.audio).expanduser()
    if not audio.exists():
        sys.exit(f"No such file: {audio}")

    out = Path(args.output).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)

    language = None if args.language.lower() in {"none", "auto"} else args.language
    backend = args.backend or detect_backend()

    print(f"Backend: {backend}   Model: {args.model}   Language: {language or 'auto-detect'}")
    if backend == "cpu":
        print("CPU transcription is slow — roughly real-time or worse. Go make coffee.")

    if backend == "mlx":
        text, segments = transcribe_mlx(audio, args.model, language)
    else:
        text, segments = transcribe_faster(audio, args.model, language, backend)

    out.write_text(text + "\n")

    timed = out.with_suffix(".timed.txt")
    with open(timed, "w") as f:
        for start, line in segments:
            f.write(f"[{stamp(start)}] {line}\n")

    print(f"\nWrote {out}  ({len(text.split()):,} words)")
    print(f"Wrote {timed}")


if __name__ == "__main__":
    main()
