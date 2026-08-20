---
title: "Connors Dip-Buying Simulation: A Real Signal You Still Can't Trade"
description: "The classic Connors dip-buying rule failed a real sealed test across 10 indices — except for one variant that passed, then ran into a different problem entirely."
pubDate: 2026-08-10
tags: ["trading-strategies", "backtesting", "technical-analysis", "quantitative-research", "markets"]
slug: "connors-dip-buying-indices-2026"
category: "experiments"
audioUrl: "/audio/Connors_dip_buying.mp3"
---

"Buy the dip" gets repeated so often in trading circles that it's stopped sounding like a strategy and started sounding like a personality trait. Almost nobody tests it properly — no out-of-sample wall, no costs charged, no pass/fail line written down in advance, just a backtest run until it looks good and then posted as a rule. My [trading-research repo](https://github.com/konradb-gh/trading-research) ran the disciplined version of that test on the specific formulation most people actually mean when they say it: the Connors RSI dip-buying rule, across ten global stock indices, tested against 120 parameter combinations, with a hard wall between the data used to search and the data used to grade the result ([full paper](https://github.com/konradb-gh/trading-research/blob/main/experiments/01-index-dip-buying/README.md)).

Short version, stated up front instead of buried at the bottom: the textbook version of the strategy loses money on every combination tested, on every index, after costs. A milder version of the same idea did survive a genuinely sealed test — and then failed anyway, for a reason that has nothing to do with whether the effect is real.

## The rule, and why it deserves a real test

The strategy is four lines. Only buy when the index is above its 200-day moving average — the long-term trend has to already be up. Wait for a very short-term RSI reading to hit an extreme, typically a 2-day RSI dropping below 10. Buy at that day's close. Sell when the index closes back above its 5-day moving average, usually two to five trading days later.

The logic underneath it holds up. Over a few-day horizon, a lot of selling isn't driven by new information — it's margin calls, stop-losses triggering each other, funds forced to raise cash, people panicking. That kind of selling pushes prices below where they'd otherwise sit, and once the forced sellers are done, prices tend to snap back. The 200-day filter is what keeps this from being "catch a falling knife": it only buys weakness inside an otherwise healthy uptrend, not every leg of a bear market.

It's also not a fringe idea. The most cited version comes from Larry Connors and Cesar Alvarez's *Short Term Trading Strategies That Work* (2008), built on a study of more than eight million trades between 1995 and 2007 — a large enough sample that dismissing it outright would be lazy. The finding was consistent: after a very short-term RSI reading hit an extreme, the following days produced above-average returns, and the effect got stronger the lower the reading went. The book also found something that cuts against how most traders actually use RSI: the standard 14-period reading carries no statistical edge at this horizon. Only the very short lookbacks do.

So the question isn't "is Connors wrong." A study finding an effect existed on individual stocks between 1995 and 2007, published in 2008, isn't the same claim as "this specific rule, run on index-level data today, clears its own trading costs." Four gaps sit between those two claims: costs (published backtests are usually quoted gross, before slippage and commission — fatal for a strategy built on many small, fast profits), publication decay (anything this simply described and this profitable attracts capital, which competes the edge away), instrument type (the original study leaned heavily on individual stocks, not the broad-index version everyone actually trades), and geography (if the mechanism is genuinely human panic-selling, it should show up in Frankfurt and Tokyo too, not just the US). Closing those four gaps is the whole point of running this again.

## The wall that makes this worth taking seriously

Testing 120 parameter combinations across 10 indices is 1,200 individual experiments. Some of those will look great by pure chance — that's arithmetic, not luck. The standard defense against that, borrowed from clinical trial design, is to split the data cleanly in two: an exploration period you're free to search, and a sealed period you commit to never touching until you've written down, in advance, exactly what result would count as a pass.

What makes this worth citing instead of another backtest thread is that the wall isn't a promise — it's enforced in software. The tooling physically refuses to run a full grid search against the sealed 2013-onward data. It only accepts one, explicitly named strategy version, typed out character-for-character in advance. You can't quietly widen the definition of "success" after seeing the number, because the system won't let you run anything except what you already committed to.

That discipline caught something worth mentioning on its own. The first exploration run showed near-total rejection everywhere, including on the S&P 500 — the deepest, cleanest dataset in the panel, where you'd expect at least some signal to show up if the effect is real at all. It also produced one cell claiming a 6,425% return on a single trade, which is the kind of number that should make you stop and check your code rather than write it up. The cause was a reused RSI function from a live trading system that reported a period with no down days as neutral (50) instead of maximum strength (100) — which meant the "sell when RSI recovers" exit could never fire for the shortest lookback, and a position bought in 1927 was never sold until 2012. An 85-year accidental buy-and-hold, dressed up as a fast trade. It's a small story, but it's the right kind: the process caught its own bug instead of publishing a fluke.

## What actually happened

After the fix, across all 120 combinations and all ten indices using the textbook exit rule, expectancy after costs came out between −0.23% and −0.29% per trade — every combination, every index, a loss. Costs, not decay, are the dominant explanation: the exploration window runs through 2012, which includes Connors' own 1995–2007 sample period, and the strategy still loses money inside that window. It's a strategy built on many small, fast wins, and the cost model here — 0.1% slippage on each side plus 0.2% round-trip commission, about 0.4% total — is on its own enough to erase what little gross edge is left.

One region of the 1,200-cell grid stayed positive, and what separates it from the textbook rule isn't a less extreme threshold — the eventual locked variant uses the same threshold, RSI below 10, that the original four-line rule does. The difference is the lookback it's measured over: a 4-day RSI below 10 takes a slower, more sustained decline to trigger than a 2-day RSI below 10, since it's smoothed over twice as many days. The same number describes a milder, multi-day pullback instead of a violent two-day drop. Combined with holding until RSI recovers above 65 instead of selling at the first bounce off the 5-day average, that's the actual shape of the surviving variant.

![Parameter-grid heatmap of expectancy per trade across all ten indices](/charts/connors-dip-parameter-grid.png)

*Source: [Trading Research, Experiment 01](https://github.com/konradb-gh/trading-research/blob/main/experiments/01-index-dip-buying/README.md), `connors_dip_v1_AGGREGATE.png`. Six exit/stop combinations, RSI lookback (rows) vs. oversold threshold (columns), average expectancy per trade after costs, exploration data through 2012.*

Seven of nine markets in that region were positive in the exploration data, including the deepest ones — the US, France, Australia, Germany, Hong Kong. That was a discovery, not the original hypothesis, which makes it weaker evidence on its own. So before touching any 2013-onward data, the exact rule got written down and locked: RSI over 4 days below 10, index above its 200-day average, buy at the close, sell on RSI back above 65, tested with and without a 2×ATR stop-loss. Passing required three things — positive average expectancy, a profit factor of at least 1.10, and both the S&P 500 and Nasdaq 100 individually positive. Korea and Poland were excluded from the pass/fail decision in advance, for having too little history to carry weight.

It passed all three. Expectancy came in at +0.37% per trade, profit factor 1.30, and the S&P 500 and Nasdaq 100 came in at +0.11% and +1.28% respectively — both positive. Six of the eight counting markets were profitable on data the rule had never touched during the search; Germany and France were the two that weren't, both ending the sealed period in the red.

## Why passing isn't the same as working

Here's where I stop being impressed and get specific about why. Roughly 81 trades total across those eight markets over thirteen years — about one trade per market per year. The S&P 500's +0.11% is built on thirteen trades. That's not a small sample in the vague sense people usually mean it; it's a sample too small for the sign of the result to mean much of anything, in either direction. The FTSE's headline profit factor of 37.7 makes the point on its own — it comes from six trades containing exactly one small loss, which is arithmetic, not a finding.

The result isn't broad the way "seven of nine markets" makes it sound, either. The Nasdaq's +1.28% is carrying the average almost single-handedly; the DAX and CAC 40 were both positive in the exploration data and both turned negative once the sealed test ran. A pattern that looked structural across five markets narrowed to something closer to "worked in the US, mostly."

Then financing takes what's left. Holding a position for roughly fifteen calendar days on a leveraged product costs somewhere around 0.20–0.23% per trade in overnight financing at typical rates — more than half of the +0.37% gross edge, gone before you've argued about anything else. Run the version with an actual stop-loss, which is the only version anyone sane would trade live, and the net result lands close to zero.

## Is this worth trading?

No. Not "needs more research" — no, for a specific and stated reason rather than a general one. This isn't a case of a fake signal dressed up to look real; it's closer to the opposite. This is what a real signal looks like when it survives a test that most backtested trading claims never actually attempt: a hard wall between search and grading, a rule locked in writing before the sealed data was touched, and a result that came in positive on data the strategy had never seen. That's rarer than it should be, and it earns credit for clearing a bar almost nothing in retail trading content clears.

It's still not tradeable, and the reason is boring rather than damning: it doesn't fire often enough to matter. One trade per market per year isn't a strategy you can run — it's an occasional event you'd need to build monitoring infrastructure around, for a payoff that financing costs mostly erase and that leans on one market to stay positive at all. A real edge that fires once a year, net of costs, close to zero, is functionally the same as no edge — just with better paperwork behind it.

The more interesting result buried in here isn't about Connors RSI at all. It's that the test was probably unwinnable from the start, and that was knowable in advance. At roughly one trade per market per year, thirteen years of sealed data was always going to produce fewer than a hundred trades, which isn't enough to distinguish a real result from noise regardless of which way it comes out. That's now a standing rule for every later experiment in the series: project the trade count before running a sealed test, and if it's under about a hundred, say upfront that only a *failure* can actually be concluded from it — a pass doesn't mean much at that sample size either way.

[The full paper, data, and reproduction commands](https://github.com/konradb-gh/trading-research/tree/main/experiments/01-index-dip-buying) are in the repo, along with the next experiment in the series, which runs the same idea on individual stocks instead of indices.
