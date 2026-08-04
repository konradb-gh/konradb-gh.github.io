# Blog

A minimal Astro blog. No component library — plain semantic HTML/CSS.

## Structure

```text
/
├── src/
│   ├── content/blog/       # posts (.md), one file per post
│   ├── content.config.ts   # content collection schema
│   ├── layouts/
│   │   └── BaseLayout.astro
│   ├── pages/
│   │   ├── index.astro     # post list
│   │   └── blog/[slug].astro
│   └── styles/global.css
└── .github/workflows/deploy.yml
```

## Writing a post

Add a Markdown file to `src/content/blog/` with this frontmatter:

```yaml
---
title: "Post title"
description: "One-line summary"
pubDate: 2026-08-04
tags: ["tag1", "tag2"]
slug: "post-title"
---
```

`slug` controls the URL (`/blog/<slug>/`) — it doesn't have to match the filename.

## Commands

| Command           | Action                                      |
| :----------------- | :------------------------------------------ |
| `npm install`       | Install dependencies                        |
| `npm run dev`       | Start local dev server at `localhost:4321`  |
| `npm run build`     | Build production site to `./dist/`          |
| `npm run preview`   | Preview the build locally                   |

## Deploying

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds the
site and deploys it to GitHub Pages via GitHub Actions.

In your repo settings, under **Pages**, set the source to **GitHub Actions**.

`astro.config.mjs` currently sets `site: 'https://kondzio1289.github.io'`,
which assumes this repo is named `kondzio1289.github.io` (a user/org page
served at the domain root). If you rename the repo or deploy it as a project
page instead (`username.github.io/repo-name`), update `site` and add a
matching `base` in `astro.config.mjs`.
