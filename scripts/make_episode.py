#!/usr/bin/env python3
"""Produce everything needed for one YouTube episode upload, in one run.

Reads the post's frontmatter + body straight from
src/content/blog/<slug>.md, then generates:
  - {slug}.mp4              (make_podcast_video.py logic)
  - {slug}_thumbnail.png    (make_thumbnail.py logic)
  - {slug}_youtube.txt      (TITLE / DESCRIPTION / TAGS upload text)
all written to ~/Desktop/podcast/<slug>/.

Standalone tool — not part of the Astro build. It only *reads* post
content from src/content/blog/; it never writes there.

Usage:
    python3 scripts/make_episode.py AUDIO.mp3 <post-slug>
    python3 scripts/make_episode.py AUDIO.mp3 <post-slug> --hook "Override Hook Text"
    python3 scripts/make_episode.py AUDIO.mp3 <post-slug> --cues cues.txt
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

import make_podcast_video as video
import make_thumbnail as thumb

SCRIPT_DIR = Path(__file__).resolve().parent
BLOG_DIR = SCRIPT_DIR.parent / "src" / "content" / "blog"
ASTRO_CONFIG = SCRIPT_DIR.parent / "astro.config.mjs"
OUTPUT_ROOT = Path.home() / "Desktop" / "podcast"

TRADING_REPO_RE = re.compile(r"https://github\.com/konradb-gh/trading-research[^\s)\]]*")

DISCLAIMER = (
    "This is research, not financial advice. Nothing in this video is a "
    "recommendation to buy or sell anything, and I'm not a financial "
    "advisor. Informational purposes only."
)

CHANNEL_TAGS = [
    "finance explained", "markets explained", "personal finance",
    "investing basics", "financial markets",
]


# --- reading the post ---------------------------------------------------

def load_post(slug: str):
    path = BLOG_DIR / f"{slug}.md"
    if not path.exists():
        available = sorted(p.stem for p in BLOG_DIR.glob("*.md"))
        raise SystemExit(
            f"No post found at {path}\n\n"
            f"Available slugs in {BLOG_DIR}:\n  " + "\n  ".join(available)
        )
    raw = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.DOTALL)
    if not m:
        raise SystemExit(f"Couldn't parse frontmatter (expected leading --- block) in {path}")
    frontmatter = yaml.safe_load(m.group(1))
    body = m.group(2).strip()
    return frontmatter, body


def get_site_url() -> str:
    text = ASTRO_CONFIG.read_text()
    m = re.search(r"site:\s*['\"]([^'\"]+)['\"]", text)
    if not m:
        raise SystemExit(f"Couldn't find `site:` in {ASTRO_CONFIG}")
    return m.group(1).rstrip("/")


# --- pulling real text out of the post body, verbatim -------------------

def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # [text](url) -> text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)        # **bold** -> bold
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)  # *italic* -> italic
    text = re.sub(r"`([^`]+)`", r"\1", text)              # `code` -> code
    return text.strip()


def first_body_paragraph(body: str) -> str:
    for para in body.split("\n\n"):
        para = para.strip()
        if not para or para.startswith("#"):
            continue
        return strip_markdown(para)
    return ""


def find_trading_research_link(body: str):
    """Only return a link if the post itself actually links to the repo —
    never fabricate one for posts that don't (e.g. glossary explainers)."""
    links = TRADING_REPO_RE.findall(body)
    if not links:
        return None
    return max(links, key=len)  # prefer the most specific (deepest) link


# --- thumbnail hook-line candidates --------------------------------------

def truncate_words(text: str, max_words: int = 6) -> str:
    return " ".join(text.split()[:max_words])


def split_title_clauses(title: str):
    for delim in [":", " — ", " - ", ","]:
        if delim in title:
            parts = [p.strip(" .") for p in title.split(delim, 1)]
            if len(parts) == 2 and parts[0] and parts[1]:
                return parts
    return [title, None]


# Words a hook line shouldn't dangle on when it's been cut short — leaving
# one of these as the last word reads as an unfinished sentence rather than
# a punchy phrase (e.g. "A bond is a loan you").
_BAD_TRAILING_WORDS = {
    "a", "an", "the", "to", "of", "in", "on", "for", "and", "or", "with",
    "by", "from", "is", "are", "you", "your", "it", "its", "that", "which",
    "who", "this", "these", "those", "as", "at", "be",
}


def natural_truncate(text: str, max_words: int = 6, min_words: int = 2):
    """Truncate to at most max_words, but only at a word boundary that
    doesn't strand a dangling filler word — and never below min_words.
    Returns None rather than emitting an awkward mid-clause cutoff."""
    words = [w for w in text.strip().split() if w]
    if len(words) < min_words:
        return None
    if len(words) <= max_words:
        return " ".join(words).rstrip(".,;:")
    for n in range(max_words, min_words - 1, -1):
        last = words[n - 1].lower().strip(".,;:")
        if last not in _BAD_TRAILING_WORDS:
            return " ".join(words[:n]).rstrip(".,;:")
    return None


def sentence_candidate(sentence: str, max_words: int = 6, min_words: int = 3):
    sentence = sentence.strip()
    if not sentence:
        return None
    # Prefer the first comma-delimited clause if it's a usable length —
    # it's usually the most self-contained natural phrase in the sentence.
    first_clause = sentence.split(",")[0].strip()
    cand = natural_truncate(first_clause, max_words, min_words)
    if cand:
        return cand
    return natural_truncate(sentence, max_words, min_words)


def generate_hook_candidates(title: str, description: str):
    """Rule-based extraction only — every candidate is a verbatim slice of
    the post's own title/description, never an invented claim."""
    candidates = []

    clause1, clause2 = split_title_clauses(title)
    for clause in (clause1, clause2):
        if clause:
            cand = natural_truncate(clause, max_words=6, min_words=2)
            if cand:
                candidates.append(cand)

    sentences = re.split(r"(?<=[.!?])\s+", description.strip())
    for sentence in sentences[:2]:
        cand = sentence_candidate(sentence)
        if cand:
            candidates.append(cand)

    # Always-available fallback: the bare title, punctuation stripped. Uses
    # a relaxed floor so even a short title ("Bonds Explained") still counts.
    bare_title = re.sub(r"[:,—-]", "", title).strip()
    cand = natural_truncate(bare_title, max_words=6, min_words=1)
    if cand:
        candidates.append(cand)

    seen, unique = set(), []
    for c in candidates:
        key = c.lower()
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique[:3]


# --- youtube upload text -------------------------------------------------

def build_tags(frontmatter):
    base = [t.replace("-", " ") for t in frontmatter.get("tags", [])]
    tags = list(base)
    for extra in CHANNEL_TAGS:
        if len(tags) >= 10:
            break
        if extra.lower() not in [t.lower() for t in tags]:
            tags.append(extra)
    return tags[:10]


def build_youtube_text(frontmatter, body, slug, site_url) -> str:
    title = frontmatter["title"]
    description = frontmatter["description"]

    intro = first_body_paragraph(body)
    post_url = f"{site_url}/blog/{frontmatter.get('slug', slug)}/"
    repo_link = find_trading_research_link(body)

    desc_parts = [description]
    if intro and intro.strip().lower() != description.strip().lower():
        desc_parts.append(intro)

    links_block = [f"Full post:\n{post_url}"]
    if repo_link:
        links_block.append(f"Full published research:\n{repo_link}")
    desc_parts.append("\n\n".join(links_block))

    desc_parts.append(DISCLAIMER)
    description_text = "\n\n".join(desc_parts)

    tags_text = ", ".join(build_tags(frontmatter))

    return (
        f"TITLE\n=====\n{title}\n\n\n"
        f"DESCRIPTION\n===========\n{description_text}\n\n\n"
        f"TAGS\n====\n{tags_text}\n"
    )


# --- orchestration --------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                      formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("audio", type=Path, help="Path to the episode's spoken-word audio file")
    parser.add_argument("slug", help="Blog post slug (matches src/content/blog/<slug>.md)")
    parser.add_argument("--hook", default=None,
                         help="Override the auto-picked thumbnail hook line")
    parser.add_argument("--cues", type=Path, default=None,
                         help="Optional cues file passed through to make_podcast_video.py "
                              "('MM:SS path/to/image.png' or 'MM:SS waveform' per line)")
    args = parser.parse_args()

    if not args.audio.exists():
        raise SystemExit(f"Audio file not found: {args.audio}")
    if args.cues is not None and not args.cues.exists():
        raise SystemExit(f"Cues file not found: {args.cues}")

    frontmatter, body = load_post(args.slug)
    site_url = get_site_url()

    out_dir = OUTPUT_ROOT / args.slug
    out_dir.mkdir(parents=True, exist_ok=True)

    title = frontmatter["title"]
    description = frontmatter["description"]

    print(f"Post: {title}")
    print(f"  tags: {frontmatter.get('tags')}")
    print(f"  category: {frontmatter.get('category')}")
    print()

    # 1. Video
    video.FFMPEG = video._tool("ffmpeg")
    video.FFPROBE = video._tool("ffprobe")
    video_path = out_dir / f"{args.slug}.mp4"
    print(f"Encoding video -> {video_path}")
    video.make_video(args.audio, title, video_path, cues_path=args.cues)
    duration = video.ffprobe_duration(args.audio)
    frame_path = out_dir / f"{args.slug}.preview.png"
    video.extract_frame(video_path, frame_path, duration * 0.1)
    print(f"Done: {video_path}  (preview frame: {frame_path})")
    print()

    # 2. Thumbnail
    candidates = generate_hook_candidates(title, description)
    if not candidates:
        candidates = [truncate_words(title, 6)]
    chosen = args.hook if args.hook else candidates[0]

    print("Hook line candidates (pulled from the post's own title/description):")
    for c in candidates:
        marker = " <- picked (default)" if c == chosen and not args.hook else ""
        marker = " <- override" if args.hook and c == args.hook else marker
        print(f"  - \"{c}\"{marker}")
    if args.hook and args.hook not in candidates:
        print(f"  - \"{args.hook}\" <- override (not auto-generated)")
    print(f"Using: \"{chosen}\"")
    print("(Re-run with --hook \"...\" to use a different one.)")

    thumbnail_path = out_dir / f"{args.slug}_thumbnail.png"
    thumb.make_thumbnail(chosen, thumbnail_path)
    print(f"Thumbnail: {thumbnail_path}")
    print()

    # 3. YouTube upload text
    youtube_text = build_youtube_text(frontmatter, body, args.slug, site_url)
    youtube_path = out_dir / f"{args.slug}_youtube.txt"
    youtube_path.write_text(youtube_text)
    print(f"YouTube upload text: {youtube_path}")
    print()

    print(f"All episode assets in: {out_dir}")


if __name__ == "__main__":
    main()
