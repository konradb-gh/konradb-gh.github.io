#!/usr/bin/env python3
"""Turn a spoken-word audio file into a YouTube-ready waveform video.

Standalone tool — wraps ffmpeg directly. Not part of the Astro build or the
charts/ pipeline; only borrows the site's JetBrains Mono font files and
color tokens (copied into scripts/assets/fonts/) to visually match the blog.

Usage:
    python3 scripts/make_podcast_video.py AUDIO.mp3 "Episode Title" [-o OUTPUT.mp4]
    python3 scripts/make_podcast_video.py AUDIO.mp3 "Episode Title" --cues cues.txt

Cues file (optional, --cues): one cue per line, each either
    MM:SS path/to/image.png
    MM:SS waveform
The visual in the waveform band switches at exactly that timestamp and
holds until the next cue (or the end of the audio, for the last cue) —
no implicit gaps or inferred behavior. An image cue switches to and holds
that diagram; a "waveform" cue switches back to the waveform. Every cue
line must specify one or the other explicitly. Blank lines and lines
starting with # are ignored. Without --cues, output is identical to the
plain waveform-for-the-whole-runtime behavior.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
FONT_BOLD = SCRIPT_DIR / "assets" / "fonts" / "JetBrainsMono-Bold.ttf"
FONT_REGULAR = SCRIPT_DIR / "assets" / "fonts" / "JetBrainsMono-Regular.ttf"

# drawtext needs an ffmpeg build with libfreetype. Homebrew's default
# `ffmpeg` formula omits it; `ffmpeg-full` (keg-only) has it. Prefer that
# build if present, without requiring it on PATH.
_FFMPEG_FULL_BIN = Path("/opt/homebrew/opt/ffmpeg-full/bin")


def _tool(name: str) -> str:
    full = _FFMPEG_FULL_BIN / name
    if full.exists():
        return str(full)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(
        f"{name} not found. Install a build with libfreetype, e.g.:\n"
        f"  brew install ffmpeg-full"
    )


FFMPEG = None  # resolved lazily in main()
FFPROBE = None

# Site design tokens (src/styles/global.css). Canonical #hex values live
# here so other scripts (e.g. make_thumbnail.py) can import and reuse them.
COLOR_BG_HEX = "#f6f3ec"       # --color-bg (paper)
COLOR_ACCENT_HEX = "#8a5e19"   # --color-accent (muted amber)
COLOR_HEADING_HEX = "#0f0e0c"  # --color-heading (ink)
COLOR_MUTED_HEX = "#5c5648"    # --color-muted
COLOR_BORDER_HEX = "#ddd6c4"   # --color-border

# ffmpeg filter syntax wants 0xRRGGBB rather than #RRGGBB.
COLOR_BG = "0x" + COLOR_BG_HEX[1:]
COLOR_ACCENT = "0x" + COLOR_ACCENT_HEX[1:]
COLOR_HEADING = "0x" + COLOR_HEADING_HEX[1:]
COLOR_MUTED = "0x" + COLOR_MUTED_HEX[1:]
COLOR_BORDER = "0x" + COLOR_BORDER_HEX[1:]

WIDTH, HEIGHT = 1920, 1080
FPS = 30
WAVE_HEIGHT = HEIGHT // 3          # middle third band
WAVE_Y = (HEIGHT - WAVE_HEIGHT) // 2


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"Command failed: {' '.join(cmd)}")
    return result.stdout


def ffprobe_duration(audio_path: Path) -> float:
    out = run([
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path),
    ])
    return float(out.strip())


def format_mmss(seconds: float) -> str:
    seconds = int(round(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def track_text(s: str) -> str:
    """Uppercase and letter-space monospace text for a 'tracked' video look."""
    words = s.upper().split()
    return "   ".join(" ".join(list(w)) for w in words)


def escape_drawtext(s: str) -> str:
    s = s.replace("\\", "\\\\\\\\")
    s = s.replace(":", "\\:")
    # Neither documented escape for a literal ' inside an ffmpeg filtergraph
    # '...'-wrapped value — backslash-escaping it in place (\'), or closing
    # and reopening the quote ('\'') — actually works with this ffmpeg
    # build's drawtext parser; both silently corrupt everything after them
    # in the graph (verified empirically). Sidestep the delimiter entirely
    # by swapping in a typographic curly apostrophe, which isn't special to
    # the filtergraph parser and needs no escaping at all.
    s = s.replace("'", "’")
    s = s.replace("%", "\\%")
    return s


def fit_fontsize(line_len: int, max_width: int, min_size: int, max_size: int,
                  char_width_ratio: float = 0.68) -> int:
    n = max(line_len, 1)
    size = int(max_width / (n * char_width_ratio))
    return max(min_size, min(max_size, size))


def parse_mmss(ts: str) -> float:
    m = re.match(r"^(\d+):(\d+(?:\.\d+)?)$", ts.strip())
    if not m:
        raise SystemExit(f"Invalid cue timestamp {ts!r} (expected MM:SS)")
    minutes, seconds = m.groups()
    return int(minutes) * 60 + float(seconds)


def resolve_cue_image(path_str: str, cues_file: Path) -> Path:
    """Resolve a cue's image path relative to (in order): as given, the
    cues file's own directory, the current working directory, and the
    repo root — so a cues file can use whichever form reads naturally."""
    p = Path(path_str)
    candidates = [p, cues_file.parent / p, Path.cwd() / p, SCRIPT_DIR.parent / p]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise SystemExit(f"Cue image not found: {path_str} (tried {[str(c) for c in candidates]})")


def parse_cues(cues_file: Path):
    """Returns a sorted list of (seconds, image_path_or_None). Each line must
    explicitly say "waveform" or give an image path — no implicit meaning
    for an omitted second field, so a malformed line fails loudly instead
    of silently doing something unintended."""
    cues = []
    for raw_line in cues_file.read_text().splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise SystemExit(
                f"Invalid cue line {raw_line!r} — expected 'MM:SS path/to/image.png' "
                f"or 'MM:SS waveform'"
            )
        seconds = parse_mmss(parts[0])
        token = parts[1].strip()
        image = None if token.lower() == "waveform" else resolve_cue_image(token, cues_file)
        cues.append((seconds, image))
    cues.sort(key=lambda c: c[0])
    return cues


def build_visual_segments(cues, duration: float):
    """Turn parsed cues into (start, end, mode) segments covering [0, duration],
    mode is "wave" or ("image", Path). No cues -> a single wave segment,
    identical to the pre-cues behavior."""
    if not cues:
        return [(0.0, duration, "wave")]

    segments = []
    if cues[0][0] > 0:
        segments.append((0.0, cues[0][0], "wave"))

    for i, (start, image) in enumerate(cues):
        end = cues[i + 1][0] if i + 1 < len(cues) else duration
        end = min(end, duration)
        if end <= start:
            continue
        mode = ("image", image) if image is not None else "wave"
        segments.append((start, end, mode))

    return segments


def compose_title(title: str, max_width: int = 1680,
                   min_single_line_size: int = 34,
                   absolute_min: int = 24, max_size: int = 56):
    """Uppercase + letter-space the title, wrapping to two lines if a single
    tracked line would otherwise force the font below a readable size."""
    words = title.upper().split()
    tracked_words = [" ".join(list(w)) for w in words]
    single_line = "   ".join(tracked_words)

    size_single = fit_fontsize(len(single_line), max_width, absolute_min, max_size)
    if size_single >= min_single_line_size or len(tracked_words) <= 3:
        return single_line, size_single

    best = None
    for split in range(1, len(tracked_words)):
        line1 = "   ".join(tracked_words[:split])
        line2 = "   ".join(tracked_words[split:])
        worst = max(len(line1), len(line2))
        if best is None or worst < best[0]:
            best = (worst, line1, line2)
    worst, line1, line2 = best
    size = fit_fontsize(worst, max_width, absolute_min, max_size)
    return line1 + "\n" + line2, size


def build_filter_complex(duration: float, title: str, image_segments=None) -> str:
    """image_segments: list of (start, end, ffmpeg_input_index) for cue
    diagrams, each input already an image loaded via -loop 1 -i. Empty/None
    means the waveform runs for the entire video — the pre-cues behavior."""
    image_segments = image_segments or []

    display_title, title_fontsize = compose_title(title)
    title_text = escape_drawtext(display_title)

    wordmark_text = escape_drawtext(track_text("Tick & Tale"))

    total_mmss = format_mmss(duration)

    filters = []

    filters.append(
        f"color=c={COLOR_BG}:s={WIDTH}x{HEIGHT}:d={duration}:r={FPS}[bg]"
    )

    filters.append(
        f"[0:a]aformat=channel_layouts=mono,"
        f"showwaves=s={WIDTH}x{WAVE_HEIGHT}:mode=cline:colors={COLOR_ACCENT}:"
        f"scale=lin:draw=full:rate={FPS}[wave]"
    )

    filters.append(f"[bg][wave]overlay=x=0:y={WAVE_Y}[bgw]")

    # Each cue diagram is scaled to fit the same band the waveform occupies,
    # letterboxed with the paper background so it fully covers that band
    # (no waveform peeking through), then overlaid only during its window —
    # a clean, glitch-free cut with no cross-fade or partial frames.
    current = "bgw"
    for i, (start, end, input_idx) in enumerate(image_segments):
        padded = f"imgpad{i}"
        filters.append(
            f"[{input_idx}:v]scale={WIDTH}:{WAVE_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={WIDTH}:{WAVE_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color={COLOR_BG}[{padded}]"
        )
        nxt = f"bgi{i}"
        filters.append(
            f"[{current}][{padded}]overlay=x=0:y={WAVE_Y}:"
            f"enable='between(t,{start},{end})'[{nxt}]"
        )
        current = nxt

    filters.append(
        f"[{current}]drawbox=x=0:y=0:w=iw:h=ih:color={COLOR_BORDER}:t=1[bg2]"
    )

    filters.append(
        f"[bg2]drawtext=fontfile={FONT_BOLD}:text='{wordmark_text}':"
        f"fontsize=30:fontcolor={COLOR_HEADING}:x=80:y=64[bg3]"
    )

    filters.append(
        f"[bg3]drawtext=fontfile={FONT_BOLD}:text='{title_text}':"
        f"fontsize={title_fontsize}:fontcolor={COLOR_HEADING}:"
        f"line_spacing=14:x=(w-text_w)/2:y=130[bg4]"
    )

    elapsed_expr = (
        r"%{eif\:trunc(t/60)\:d\:2}\:%{eif\:mod(t\,60)\:d\:2}"
        f" / {total_mmss.replace(':', chr(92) + ':')}"
    )
    filters.append(
        f"[bg4]drawtext=fontfile={FONT_REGULAR}:text='{elapsed_expr}':"
        f"fontsize=26:fontcolor={COLOR_MUTED}:x=w-text_w-80:y=h-70[outv]"
    )

    return ";".join(filters)


def make_video(audio_path: Path, title: str, output_path: Path, cues_path: Path = None):
    duration = ffprobe_duration(audio_path)

    image_inputs = []       # image paths, in ffmpeg -i order (index 1, 2, ...)
    image_segments = []     # (start, end, ffmpeg_input_index)
    if cues_path is not None:
        cues = parse_cues(cues_path)
        for start, end, mode in build_visual_segments(cues, duration):
            if mode == "wave":
                continue
            _, image_path = mode
            image_inputs.append(image_path)
            image_segments.append((start, end, len(image_inputs)))  # input 0 is audio

    filter_complex = build_filter_complex(duration, title, image_segments)

    cmd = [FFMPEG, "-y", "-i", str(audio_path)]
    for image_path in image_inputs:
        cmd += ["-loop", "1", "-i", str(image_path)]
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(output_path),
    ]
    run(cmd)


def extract_frame(video_path: Path, frame_path: Path, at_seconds: float):
    run([
        FFMPEG, "-y",
        "-ss", str(at_seconds),
        "-i", str(video_path),
        "-frames:v", "1",
        str(frame_path),
    ])


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return s or "episode"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path, help="Path to the spoken-word audio file")
    parser.add_argument("title", help="Episode title (overlaid on the video)")
    parser.add_argument("-o", "--output", type=Path, default=None,
                         help="Output .mp4 path (default: <audio dir>/<slug>.mp4)")
    parser.add_argument("--cues", type=Path, default=None,
                         help="Optional cues file: 'MM:SS path/to/image.png' per "
                              "line, switching the waveform band to that image "
                              "at MM:SS. Omit for plain waveform-only output.")
    parser.add_argument("--frame-at", type=float, default=None,
                         help="Seconds into the video to grab a preview frame "
                              "(default: 10%% into the audio)")
    args = parser.parse_args()

    global FFMPEG, FFPROBE
    FFMPEG = _tool("ffmpeg")
    FFPROBE = _tool("ffprobe")

    if not args.audio.exists():
        raise SystemExit(f"Audio file not found: {args.audio}")
    if not FONT_BOLD.exists() or not FONT_REGULAR.exists():
        raise SystemExit(f"Missing font assets in {FONT_BOLD.parent}")
    if args.cues is not None and not args.cues.exists():
        raise SystemExit(f"Cues file not found: {args.cues}")

    output_path = args.output or args.audio.with_name(f"{slugify(args.title)}.mp4")

    print(f"Encoding video for '{args.title}' -> {output_path}")
    make_video(args.audio, args.title, output_path, cues_path=args.cues)
    print(f"Done: {output_path}")

    duration = ffprobe_duration(args.audio)
    frame_at = args.frame_at if args.frame_at is not None else duration * 0.1
    frame_path = output_path.with_suffix(".preview.png")
    extract_frame(output_path, frame_path, frame_at)
    print(f"Preview frame: {frame_path}")


if __name__ == "__main__":
    main()
