---
title: "Corporate Actions, Explained"
description: "A corporate action is anything a public company does that directly affects its shareholders or its shares — mandatory vs. voluntary, a real stock split worked out in full, and why they quietly complicate historical price data."
pubDate: 2026-08-26
tags: ["corporate-actions", "stock-splits", "mergers", "glossary", "market-microstructure"]
slug: "corporate-action"
category: "glossary"
---

A corporate action is any event a public company initiates that directly affects its shareholders or its securities. The key word is *initiates* — it's something the company does, on purpose, not something that happens to it because the market moved.

## The analogy

Say a landlord owns an apartment building. One year she knocks two small units into one larger one. Another year she splits a big unit into two smaller ones. Another year she credits every tenant a month's rent for renewing early. None of these change what the building as a whole is worth — it's the same building, the same total square footage, the same rent roll. What changes is each tenant's specific situation: how many units exist, how big each one is, what shows up on this month's statement.

A corporate action is a company doing the equivalent to its own shares. The company's total value doesn't move because of the action alone — what changes is how that value is sliced up and delivered to the people who own it.

## Mandatory vs. voluntary

This is the distinction that actually organizes the whole topic, so it's worth sitting with.

A **mandatory** corporate action happens to every shareholder automatically, with no choice involved. A stock split, a merger where your shares get converted into cash or acquirer stock, a regular cash dividend — you don't elect into any of these. You wake up owning whatever the company decided you now own, or holding whatever cash landed in your account. There's nothing to fill out and nothing to opt into.

A **voluntary** corporate action requires the shareholder to actively make a choice, and if you don't, you get a default outcome that isn't necessarily the best one available. A **tender offer** — where a company or an outside bidder offers to buy shares directly from shareholders at a set price — only pays out to the shareholders who actually tender their shares; ignore it, and you simply keep holding what you had. A **rights issue** — where a company offers existing shareholders the right to buy new shares, usually below the current market price, in proportion to what they already own — dilutes everyone's stake by adding new shares to the total, but only shareholders who exercise the right get to buy in at the discount; shareholders who do nothing just end up owning a smaller slice of a now-larger company. Voluntary actions are where paying attention actually pays off, because the default is rarely the best of the available outcomes.

## A split, in real numbers

The clearest mandatory action to picture is a stock split, so it's worth working through an actual one rather than an invented example.

CrowdStrike's board approved a 4-for-1 stock split in June 2026. Every shareholder of record as of June 25 received three additional shares for each one they already held, distributed after the close on July 1, with the stock trading on a split-adjusted basis starting July 2. Shares that had closed at $767 the day before opened the next day around $194 — not exactly a fourth of $767, since ordinary trading still moves the price a little, but functionally the same money split four ways ([The Motley Fool](https://www.fool.com/investing/2026/07/06/should-buy-crowdstrike-stock-split-answer-surprise/)).

Own 10 shares before the split, worth roughly $7,670 total. After it, you own 40 shares worth roughly $194 each — still about $7,760, the small difference being ordinary price movement, not anything the split itself did. Nothing about CrowdStrike's business, revenue, or earnings changed between those two days. Companies split their stock mainly to keep the per-share price at a level that feels more accessible to ordinary investors and easier to use for employee equity compensation — a psychological and practical adjustment, not a financial one.

![A stock split: 1 share at $767 becomes 4 shares at roughly $194 each](/charts/stock-split-crowdstrike-2026.png)

*Illustrates CrowdStrike's real 4-for-1 split and price levels described above — the exact post-split price is approximate, since ordinary trading moved it slightly from a precise quarter of $767.*

## A few others, briefly

A **merger or acquisition** converts your shares into cash, shares of the acquiring company, or some mix of both, once the deal closes — you're no longer a shareholder of the original company either way. A **spin-off** does the opposite of a merger: the company separates a division into its own independently traded stock and distributes shares of it to existing shareholders, so you end up holding two companies where you used to hold one. Rights issues, covered above, round out the common voluntary category.

## The most common one, and its fixed-income cousin

The single most common corporate action by far is the plain cash dividend — I've already covered the mechanics of ex-dividend and record dates in full [here](/blog/dividend), so there's no need to repeat them. On the fixed-income side, a **bond call** or redemption — the issuer paying bondholders back before the [maturity date](/blog/bond) they signed up for — is the closest parallel: also mandatory, also something the issuer initiates on its own timeline rather than the holder's.

## Why this matters beyond the definition

Every one of these events changes the actual numbers behind a stock's price history. A chart of CrowdStrike's price before July 2, 2026 has to be divided by four to line up sensibly with everything after it — otherwise the split shows up as a stock that fell 75% overnight, which isn't what happened at all. Getting that adjustment right, consistently, across every split, spin-off, and special dividend a company has ever done, is one of the unglamorous reasons building an accurate historical price series is genuinely harder than just downloading a column of numbers.

None of this tells you whether a corporate action is good or bad news for the stock. It just explains what actually happened to your position, and why.
