---
title: "Order Books, Explained"
description: "An order book is the live list of every buy and sell order waiting to be matched for a stock. What bid, ask, spread, and depth actually mean, how a trade actually happens, and market orders vs. limit orders."
pubDate: 2026-08-25
tags: ["order-book", "market-microstructure", "trading", "liquidity", "glossary"]
slug: "order-book"
category: "glossary"
---

An order book is a live, running list of every buy and sell order currently waiting to be matched for a stock — everyone who wants to buy, and at what price, and everyone who wants to sell, and at what price, all sitting in the open at once. Nothing about it is hidden or estimated. It's the actual queue of intent behind the single price a stock quote shows you.

## The analogy

Picture a crowded farmers market for tomatoes. Buyers are calling out the price they'll pay — "I'll give you $2 a pound" — and sellers are calling out their own asking price — "I won't take less than $2.20." Nobody trades until one side moves to meet the other: a buyer raises to $2.20, or a seller drops to $2. The instant those two numbers match, tomatoes change hands.

An order book is that exact negotiation, organized into an actual visible list instead of shouted chaos across a market square — every current offer and every current ask, ranked by price, waiting for someone to meet it.

## What's actually on the book

The **bid** is the highest price a buyer is currently offering. The **ask** (or "offer") is the lowest price a seller is currently willing to take. Those two are almost never the same — if they were, a trade would have already happened — and the gap between them is the **bid-ask spread**. A tight spread means a lot of active interest crowded right around the current price; a wide spread means thin trading, with real disagreement about what the thing is worth.

Neither number tells the whole story on its own, though. **Depth** is how many shares are stacked up waiting at each price level, not just the single best bid and best ask. A stock can have a tight one-cent spread and still have almost nothing behind it — a handful of shares at the best price and then a big gap to the next level.

Here's what a book with real depth on both sides looks like, laid out as a price ladder:

![A live order book: three ask levels above the spread, three bid levels below it](/charts/order-book-ladder-2026.png)

*Illustrates the mechanics described below — not a real stock, no external data.*

## Watching a trade happen

Take the book above as the starting point: best ask $42.05 (300 shares), best bid $41.95 (400 shares), a $0.10 spread.

1. A trader places a **market order** to buy 300 shares. It takes whatever's sitting at the best ask right now, no negotiating — so it matches instantly against the $42.05 level and clears it entirely.
2. The $42.05 level is gone, so the best ask on the book is now $42.15 (250 shares).
3. A trader places a **limit order** to buy 150 shares at $41.90 — below the current best ask, so there's nothing for it to match. It doesn't trade; it just joins the bid side as a new level below $41.95, waiting for a seller to come down to it.
4. A trader places a limit order to buy 100 shares at $42.15, matching the current best ask exactly. That crosses, so it executes immediately: 100 shares trade at $42.15, leaving 150 shares of that level still resting on the book.

Same book, four orders, two different outcomes: match now, or wait on the book. That's the entire mechanism.

## What depth and spread actually tell you

Picture the book back at its original starting point, before any of those four orders hit it. Now say you need to buy 600 shares, not 100. The ask side only has 300 shares at $42.05 and another 250 at $42.15 — a market order for 600 shares clears both levels and starts eating into $42.30 too, so your *average* fill price ends up worse than the $42.05 you saw quoted. That gap between the price you expected and the price you actually got is called **slippage** — a direct consequence of running out of depth at the price you wanted.

A thin book — few orders, a wide spread — means even a moderately sized order can move the price against you just by showing up. A deep, tight book means you can push real size through without shifting the price much, because there's enough depth stacked at each level to absorb it. That's why the same order can behave completely differently depending on what you're trading: a few hundred shares of a heavily-traded stock barely dents the book, while the same order in a thin, low-volume name can walk the price up several levels before it's filled.

## Market order vs. limit order

The two order types from the example above are the entire practical choice you're making every time you trade. A **market order** takes whatever's currently on the book immediately — you're guaranteed to get filled, but you're accepting the spread and whatever depth is actually there, for better or worse. A **limit order** adds your own price to the book and waits — you control exactly what you're willing to pay or accept, but there's no guarantee it ever gets filled at all, especially if the market moves away from your price instead of toward it.

## Why this matters beyond the definition

I wrote earlier about a [backtest whose entire result flipped on one buried assumption](/blog/stop-fill-assumption-backtest-2026) — what price a stop-loss order actually filled at overnight. That's this exact mechanism, moved out of a live market and into a spreadsheet: a backtest has to *assume* a fill price, while a real order book simply hands you one, shaped by whatever depth and spread happened to be sitting there. A strategy that looks fine on paper can quietly fall apart the moment it has to actually cross a thin, wide book to get filled.

None of this tells you when to place an order or which stock to trade. It just explains why the price you click on and the price you actually get aren't always the same number.
