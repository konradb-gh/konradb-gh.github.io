---
title: "Quality-Stock Dip-Buying Simulation: Real, Measured, and Still Not Worth Trading"
description: "A dip-buying strategy on quality stocks passed a real sealed test on 8,877 trades. Then a data gap that's nobody's fault — old stock records quietly missing the companies that failed — shrank a third of the edge away."
pubDate: 2026-08-17
tags: ["trading-strategies", "backtesting", "quantitative-research", "risk-management", "markets"]
slug: "stock-dip-survivorship-bias-2026"
category: "experiments"
---

Most of the time, a backtest disappoints you because something was wrong with it — a bug, an assumption that didn't hold, a lucky trade doing all the work. This one is different, and that's exactly why it's worth walking through. Nothing was wrong with this test. The effect it found was real, it was measured carefully, and it survived a genuine, high-stakes check on thousands of trades it had never seen. It still isn't worth trading — not because anyone made a mistake, but because of something built into almost all free historical stock data: it quietly forgets the companies that failed.

Quick refresher if you're coming in cold: **expectancy** is the average result you make per trade, averaged across every trade — the one number that tells you whether a strategy makes or loses money over time. I define it fully, along with the related idea of R-multiples, in the [Experiment 05 post](/blog/stop-fill-assumption-backtest-2026). This paper, from my own [trading-research repo](https://github.com/konradb-gh/trading-research) — [Experiment 02](https://github.com/konradb-gh/trading-research/tree/main/experiments/02-quality-stock-dip-buying), specifically — reports its numbers a little differently: as a plain percentage return per trade rather than in R. That distinction won't matter for anything that follows; just don't go looking for R-multiples in the tables below.

## The idea, in plain terms

The strategy only buys **quality stocks** — and here "quality" is a specific, technical definition, not a fuzzy one: a stock already in a well-established uptrend, trading above its key moving averages, near its high for the year, and ranked among the market's strongest performers, regardless of what the underlying business actually does or how its balance sheet looks. Then it waits for one of those strong stocks to have a rough few days — a short-term dip — and buys it, betting the dip is temporary and the stock's underlying strength reasserts itself. It sells once the stock shows real strength again, not at the first small bounce.

The reasoning behind combining these two ideas is straightforward: over months, strong stocks tend to keep being strong (a well-documented pattern called momentum); over days, sharp drops tend to overreact and partly snap back (mean reversion). So the strategy uses the first pattern to pick *which* stocks to watch, and the second to pick *which day* to buy them.

## This one didn't look fragile from the start

Worth saying plainly before anything else: this result did not have the shape of something fragile. A related test on stock market indices (covered in this project's [first experiment](/blog/connors-dip-buying-indices-2026)) had the opposite problem — the signal was real but fired so rarely that only about 81 trades came out of a 13-year sealed test, nowhere near enough to trust either way. Individual stocks fix that on their own: instead of ten indices, you're watching hundreds of companies, so the same signal fires constantly.

The sealed test on this strategy — the real, one-shot test run on data the strategy had never seen — produced **8,877 completed trades**, and the exact rule and pass/fail bar had all been written down and locked before that data was ever touched. It cleared every bar:

| Requirement | Result |
|---|---|
| Positive expectancy after costs | **+0.276% per trade** |
| Profit factor ≥ 1.10 (total won ÷ total lost, above 1.0 means winners outweigh losers) | **1.26** |
| Positive in both halves of the test period | **+0.263% and +0.290%** |

The strategy was profitable in 11 of the 14 individual years tested, and the three losing years were all periods of broad market stress. One detail stands out: 2022, a genuinely bad year for stocks generally, barely dented the results, because the system has a built-in **market-health gate** — a rule that only allows new trades when the overall market itself (the S&P 500) is above its own long-term average — and that gate kept the strategy sitting in cash for most of 2022 instead of forcing trades into a falling market.

Here's what that looked like, tracking the value of one hypothetical unit invested through the entire sealed test:

![Out-of-sample equity curve for the pre-registered quality-stock dip-buying variant, 2013 onward](/charts/quality-stock-dip-oos-equity-2026.png)

*Source: [Trading Research, Experiment 02](https://github.com/konradb-gh/trading-research/tree/main/experiments/02-quality-stock-dip-buying), `stock_dip_v1_OOS_equity.png`. Growth of one unit on a log scale (equal spacing represents equal percentage moves, not equal dollar amounts) for the version with no stop-loss (blue) and the version with a stop-loss (orange), across roughly 9,000 trades between 2013 and 2026. This tracks each individual signal equally, not a real, capacity-limited portfolio — a caveat worth taking at face value, since the rest of this post is about to explain why the raw signal overstates what you'd actually capture. The dip around 2020 is visible on both lines; both trend upward overall.*

That's a large, genuinely well-powered result — more than a hundred times the trade count that sank the earlier index-level version. On the strength of this alone, it would be reasonable to call this a validated strategy and move on. That's exactly the point where this paper decides not to stop.

## The hidden problem with almost any test like this

Before getting to what happens next, one idea needs explaining, because it's the whole hinge of this story: **survivorship bias**.

Imagine you wanted to know what separates successful restaurants from failed ones, so you go interview the owners of every restaurant currently open in your city and ask what they did right. You'll get real, honest answers — but you've built in a silent flaw. Any restaurant that did exactly the same things right and still went out of business for some unrelated reason (bad location, bad timing, bad luck) never makes it into your interview list at all, because it's not open anymore to be interviewed. Whatever traits the survivors share will look more reliable than they really are, because you've quietly deleted every counterexample from your own dataset just by only talking to the businesses still standing.

The exact same thing happens with a stock backtest built on "today's S&P 500." The S&P 500 you can easily look up right now is not the same 500 companies it contained in, say, 1998 — companies get removed when they go bankrupt, get acquired in distress, or simply fail badly enough to be dropped, and new ones take their place. If you test "buy the dip on S&P 500 stocks" using today's list of 500 companies, you are only ever testing the ones healthy enough to still be on that list *now*. Every company that dipped and then went to zero has been quietly erased from the experiment — and those are precisely the cases where buying the dip would have hurt you the most. Testing dip-buying only on today's survivors is close to asking "did buying dips work, on the specific companies we already know went on to recover?" That's a rigged question, and the honest answer to it will always look better than it should.

## How much of the real picture is actually missing

This isn't just a theoretical worry here — it was measured directly. Using a dataset that records who was *actually* in the S&P 500 on any given historical day (delisted failures included, not just today's survivors), the researchers checked: for stocks that were genuinely in the index during each stretch of years, how many of them does today's free stock-price data still have usable history for?

| Years | Actually in the index | Still have usable data today | Coverage |
|---|---|---|---|
| 1996–2000 | 666 | 270 | **41%** |
| 2001–2005 | 587 | 307 | 52% |
| 2006–2010 | 644 | 392 | 61% |
| 2011–2012 | 533 | 372 | 70% |
| 2013–2016 | 593 | 437 | 74% |
| 2017–2020 | 604 | 494 | 82% |
| 2021–2026 | 621 | 565 | **91%** |

*(The paper's own summary table skips 2011–2012 — a short two-year bridge between the exploration and sealed windows that doesn't fit neatly alongside the other multi-year blocks — but the row exists in the published data, so it's included here for completeness.)*

Read that column from top to bottom and the shape of the problem becomes obvious. Back in 1996–2000, today's data can only see about **41%** of the companies that were genuinely eligible candidates at the time — the other 59% have vanished from the record, mostly because they failed. By 2021–2026, coverage climbs to **91%**, because far fewer of those companies have had the time to go bankrupt, get bought out, or otherwise disappear yet.

This is the important part to sit with: the bias isn't a flat tax applied evenly across the whole test. It's a gradient. The older the years being tested, the more of the real picture is missing, and what's missing is overwhelmingly the failures — exactly the stocks a dip-buying strategy would have gotten hurt on. That means older backtest results are inflated by more than recent ones, not by the same fixed amount throughout. A strategy that looks great across the full 1996–2026 span might really be two different things stitched together: genuinely good in the recent years, and artificially flattered in the older years, where the losers have been quietly deleted from the record.

## What correcting for it actually did to the number

So the researchers re-ran the exact same strategy, changing nothing about the rules — only the universe of stocks it was allowed to trade, swapping "today's 500 survivors" for the honest, point-in-time list of who was actually in the index on each historical day, failures included.

The headline number on the flattering, survivors-only version was **+0.276% expectancy per trade** across those 8,877 sealed trades — a genuine, clean pass against the pre-registered bar. Once corrected for survivorship, that fell to **+0.185% per trade**, a drop of −0.091 percentage points. Do that division and it's almost exactly **a third of the original edge** — gone, not because the effect wasn't real, but because roughly a third of the original number turned out to be an artifact of testing only companies that happened to still be around to test.

To be clear about what did and didn't survive this correction: the direction and persistence of the effect held up completely. It was still positive across the sealed period, still positive in both halves of it separately. What changed was only the *size*. And even +0.185% is still an overstatement, because the honest list is itself still missing about 19% of the real historical index members — Yahoo Finance simply doesn't have usable price history for some of the companies that failed badly enough or long enough ago — and the missing 19% skews toward exactly the worst outcomes, the same direction as before.

There's one more cost that hasn't entered the picture yet: financing. This strategy holds each position for several days at a time, and if you're trading it with borrowed money — the normal way to run a strategy like this at any real size — you pay overnight financing on that borrowed money for every day you hold the position. At typical rates, that runs about 0.09% per trade here.

Stack all of it together, starting from the flattering number and subtracting honestly:

- **+0.276%** — what it looked like on today's survivors
- **−0.091%** — remove the measured survivorship bias
- **+0.185%** — honest, but still an overstatement (19% of the worst-case losers are still missing from even the corrected data)
- **−0.09%** — subtract the cost of financing the position while you hold it
- **≈0% to +0.10%** — what's plausibly left, with a best guess of around **+0.05%** per trade

And the version with an actual stop-loss — the only version anyone sensible would run with real money — tells the same story with an extra step already baked in. On today's survivors it looked like +0.107% per trade; survivorship-corrected, that's already down to **+0.045% per trade**, and that's *before* financing is even subtracted. Take financing off that already-corrected number and it lands at break-even to slightly negative. A trading cost of roughly 0.10% per trade is the bar this strategy has to clear, and by the time every honest cost is on the table, the edge and the bar are almost exactly the same size.

## The verdict

The phenomenon is real. The tradeable edge is not. Those are two different claims, and mixing them up is the easiest way to misread this whole result.

It is genuinely true that quality stocks, when they dip inside an uptrend, tend to bounce back — that held up on nearly 9,000 trades in a real sealed test, and it kept holding up even after correcting for survivorship bias, in both direction and persistence. That's not nothing; a documented, real market behavior that survives honest scrutiny is rarer than most backtests you'll see online. But "real and measurable" is a different claim from "profitable enough to actually trade once you account for the trades' true costs and the honest, unflattering version of the historical data," and this strategy lands on the wrong side of that second line. The gap between the flattering number and the honest one wasn't a rounding error — it was about a third of the entire result, and what was left after that didn't clear the cost of running the strategy for real.

This one was not turned into a live trading strategy, and that's the correct call, not an overly cautious one. There's nothing being left on the table here — there's no solid edge underneath the survivorship inflation and the financing cost, just a real behavior that isn't, on its own, worth the price of capturing it. Finding that out took an afternoon of careful measurement. The alternative — trading it for real and finding out the same thing the expensive way — is exactly what this kind of test exists to prevent.

[The full paper, data, and reproduction steps](https://github.com/konradb-gh/trading-research/tree/main/experiments/02-quality-stock-dip-buying) are in the repo.
