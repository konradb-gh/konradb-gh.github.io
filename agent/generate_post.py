#!/usr/bin/env python3
"""CLI that researches a topic, drafts a blog post, and writes it to
src/content/blog/<slug>.md with frontmatter matching the Astro content
collection schema (title, description, pubDate, tags, slug).

Usage:
    python generate_post.py "topic to write about"
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import anthropic
import yaml

RESEARCH_MODEL = "claude-sonnet-5"
OUTLINE_MODEL = "claude-haiku-4-5"
DRAFT_MODEL = "claude-sonnet-5"
CRITIQUE_MODEL = "claude-sonnet-5"
SEO_MODEL = "claude-haiku-4-5"

AGENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = AGENT_DIR.parent
STYLE_GUIDE_PATH = AGENT_DIR / "style_guide.md"
BLOG_DIR = REPO_ROOT / "src" / "content" / "blog"

SEO_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "SEO-friendly post title, under 60 characters"},
        "meta_description": {"type": "string", "description": "Meta description, under 160 characters"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-6 lowercase topic tags",
        },
    },
    "required": ["title", "meta_description", "tags"],
    "additionalProperties": False,
}


class GenerationError(RuntimeError):
    """Raised when a pipeline step fails; carries the step name for context."""


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def extract_text(content_blocks) -> str:
    return "\n".join(block.text for block in content_blocks if block.type == "text").strip()


def research_topic(client: anthropic.Anthropic, topic: str) -> str:
    system = (
        "You are a research assistant gathering material for a blog post. "
        "Use web search to find current, sourced facts and statistics about the topic. "
        "For every number or claim, note where it came from (publication/source name). "
        "Output a plain-text list of sourced facts and stats, not prose — this is "
        "internal research material, not the final article."
    )
    messages = [{"role": "user", "content": f"Research this topic: {topic}"}]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]

    for _ in range(10):
        response = client.messages.create(
            model=RESEARCH_MODEL,
            max_tokens=4096,
            system=system,
            tools=tools,
            messages=messages,
        )
        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        if response.stop_reason == "refusal":
            raise GenerationError("research: model declined the request")
        return extract_text(response.content)

    raise GenerationError("research: exceeded server-tool continuation limit")


def build_outline(client: anthropic.Anthropic, topic: str, research_notes: str) -> str:
    response = client.messages.create(
        model=OUTLINE_MODEL,
        max_tokens=1024,
        system=(
            "You turn research notes into a structured blog post outline. "
            "Output a Markdown outline: a working title, then H2/H3 section headings "
            "with a one-line note on what each section covers. No prose, just the outline."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Topic: {topic}\n\nResearch notes:\n{research_notes}",
            }
        ],
    )
    if response.stop_reason == "refusal":
        raise GenerationError("outline: model declined the request")
    text = extract_text(response.content)
    if not text:
        raise GenerationError("outline: model returned no content")
    return text


def draft_post(client: anthropic.Anthropic, topic: str, research_notes: str, outline: str, style_guide: str) -> str:
    response = client.messages.create(
        model=DRAFT_MODEL,
        max_tokens=8192,
        system=(
            "You write blog posts for this Markdown-based blog. Follow the style "
            "guide below exactly for voice, register, and banned phrases.\n\n"
            f"{style_guide}\n\n"
            "Write the full post in Markdown, using the outline and research notes "
            "as source material. Ground every number or statistic in the research "
            "notes — do not invent figures. Start directly with the post content "
            "(no frontmatter, no title heading duplication beyond a single H1)."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\nOutline:\n{outline}\n\n"
                    f"Research notes:\n{research_notes}"
                ),
            }
        ],
    )
    if response.stop_reason == "refusal":
        raise GenerationError("draft: model declined the request")
    text = extract_text(response.content)
    if not text:
        raise GenerationError("draft: model returned no content")
    return text


def critique_draft(client: anthropic.Anthropic, draft: str, style_guide: str) -> str:
    response = client.messages.create(
        model=CRITIQUE_MODEL,
        max_tokens=2048,
        system=(
            "You are a tough editor reviewing a blog post draft before publication. "
            "Check specifically for:\n"
            "1. Unsourced numbers or statistics — any figure not clearly grounded in "
            "the research it was given.\n"
            "2. Generic filler phrases, including anything on this banned list:\n"
            f"{style_guide}\n"
            "3. Whether the post states an actual position, rather than hedging "
            "every claim into mush.\n\n"
            "Output a specific, actionable list of problems found. If something is "
            "fine, don't mention it. Be concrete — quote the offending phrase or "
            "sentence."
        ),
        messages=[{"role": "user", "content": f"Draft:\n\n{draft}"}],
    )
    if response.stop_reason == "refusal":
        raise GenerationError("critique: model declined the request")
    return extract_text(response.content)


def revise_draft(client: anthropic.Anthropic, draft: str, critique: str, style_guide: str) -> str:
    response = client.messages.create(
        model=DRAFT_MODEL,
        max_tokens=8192,
        system=(
            "You revise blog post drafts based on editorial critique. Follow the "
            "style guide below.\n\n"
            f"{style_guide}\n\n"
            "Apply the critique's feedback directly: cut or re-source unsourced "
            "numbers, remove filler phrases, sharpen hedged claims into a clear "
            "position where the critique flags hedging. Output the full revised "
            "post in Markdown — no commentary about what changed, just the post."
        ),
        messages=[
            {
                "role": "user",
                "content": f"Draft:\n\n{draft}\n\nEditorial critique:\n\n{critique}",
            }
        ],
    )
    if response.stop_reason == "refusal":
        raise GenerationError("revision: model declined the request")
    text = extract_text(response.content)
    if not text:
        raise GenerationError("revision: model returned no content")
    return text


def generate_seo_metadata(client: anthropic.Anthropic, final_draft: str) -> dict:
    response = client.messages.create(
        model=SEO_MODEL,
        max_tokens=512,
        system=(
            "You generate SEO metadata for a blog post from its final text. "
            "Return a title, meta description, and tags that accurately reflect "
            "the post's content."
        ),
        output_config={"format": {"type": "json_schema", "schema": SEO_SCHEMA}},
        messages=[{"role": "user", "content": f"Post:\n\n{final_draft}"}],
    )
    if response.stop_reason == "refusal":
        raise GenerationError("seo: model declined the request")
    text = extract_text(response.content)
    if not text:
        raise GenerationError("seo: model returned no content")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GenerationError(f"seo: could not parse model output as JSON: {exc}") from exc


def write_post(slug: str, frontmatter: dict, body: str) -> Path:
    BLOG_DIR.mkdir(parents=True, exist_ok=True)
    target = BLOG_DIR / f"{slug}.md"

    front_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True)
    content = f"---\n{front_yaml}---\n\n{body.strip()}\n"

    fd, tmp_path = tempfile.mkstemp(dir=BLOG_DIR, prefix=f".{slug}-", suffix=".md.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp_path, target)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a blog post from a topic.")
    parser.add_argument("topic", help="The topic to research and write about")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set in the environment.", file=sys.stderr)
        return 1

    if not STYLE_GUIDE_PATH.exists():
        print(f"Error: style guide not found at {STYLE_GUIDE_PATH}", file=sys.stderr)
        return 1
    style_guide = STYLE_GUIDE_PATH.read_text(encoding="utf-8")

    client = anthropic.Anthropic(api_key=api_key)

    try:
        print(f"Researching: {args.topic}", file=sys.stderr)
        research_notes = research_topic(client, args.topic)

        print("Building outline...", file=sys.stderr)
        outline = build_outline(client, args.topic, research_notes)

        print("Drafting post...", file=sys.stderr)
        draft = draft_post(client, args.topic, research_notes, outline, style_guide)

        print("Running self-critique...", file=sys.stderr)
        critique = critique_draft(client, draft, style_guide)

        print("Revising based on critique...", file=sys.stderr)
        final_draft = revise_draft(client, draft, critique, style_guide)

        print("Generating SEO metadata...", file=sys.stderr)
        seo = generate_seo_metadata(client, final_draft)

    except GenerationError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except anthropic.APIError as exc:
        print(f"Error: Anthropic API request failed: {exc}", file=sys.stderr)
        return 1

    slug = slugify(seo["title"])
    if not slug:
        slug = slugify(args.topic)

    frontmatter = {
        "title": seo["title"],
        "description": seo["meta_description"],
        "pubDate": datetime.date.today().isoformat(),
        "tags": seo["tags"],
        "slug": slug,
    }

    try:
        target = write_post(slug, frontmatter, final_draft)
    except OSError as exc:
        print(f"Error: failed to write post file: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {target.relative_to(REPO_ROOT)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
