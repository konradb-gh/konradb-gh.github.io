# Post generator

`generate_post.py` researches a topic, drafts a post in this blog's voice, and
writes it to `../src/content/blog/<slug>.md` with frontmatter matching the
Astro content collection schema.

## Pipeline

1. **Research** (`claude-sonnet-5` + web search) — gathers sourced facts and stats.
2. **Outline** (`claude-haiku-4-5`) — turns research into a structured outline.
3. **Draft** (`claude-sonnet-5`) — writes the full post, using [`style_guide.md`](style_guide.md) as style context.
4. **Self-critique** (`claude-sonnet-5`) — a separate pass checking for unsourced
   numbers, generic filler phrases, and hedged (non-committal) claims.
5. **Revise** (`claude-sonnet-5`) — rewrites the draft based on the critique.
6. **SEO metadata** (`claude-haiku-4-5`) — generates title, meta description, and tags
   from the final draft.

The post is only written to disk once every step succeeds — a failed run never
leaves a partial file behind.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
python generate_post.py "why small businesses struggled during COVID"
```

Output: `src/content/blog/<slug>.md`, with frontmatter for `title`,
`description`, `pubDate`, `tags`, and `slug`.
