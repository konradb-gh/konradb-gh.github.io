---
title: "Stop-Fill Assumption Simulation: The Hidden Assumption That Turned +17.73% Into −38.98%"
description: "A single line in a trading backtest — what price a stop-loss fills at overnight — quietly picked the winner of an exit-strategy test, and inflated the whole system's headline return. Here's how, in plain terms."
pubDate: 2026-08-13
tags: ["trading-strategies", "backtesting", "risk-management", "quantitative-research", "markets"]
slug: "stop-fill-assumption-backtest-2026"
category: "experiments"
---

To break even with a 1:1.5 risk-to-reward ratio per trade, you need a minimum win rate of 40%. Any win rate above 40% makes your strategy profitable, while anything below will lose money over time. That single fact is the lens the rest of this post reads through, so it's worth sitting with before anything else.

Here's the general version. Your breakeven win rate is:

**risk ÷ (risk + reward)**

Risk 1 to make 1.5, and breakeven is 1 ÷ (1 + 1.5) = 40%. Risk 1 to make 3 instead — a bigger potential win for the same size loss — and breakeven drops to 1 ÷ (1 + 3) = 25%. Same trader, same discipline, a completely different bar for "profitable," just from changing how big the wins are relative to the losses.

That's why a win rate on its own doesn't tell you anything. A strategy that wins 26% of the time isn't automatically bad, and one that wins 54% of the time isn't automatically good — it depends entirely on how big the average win is compared to the average loss. Keep that in your back pocket, because this post is about a real trading-system test where that exact fact both explained a genuine result and, it turned out, hid a fake one.

This comes from my own [trading-research repo](https://github.com/konradb-gh/trading-research) — [Experiment 05](https://github.com/konradb-gh/trading-research/tree/main/experiments/05-stop-fill-assumption), specifically. A few terms I'll use throughout, defined once so you're not guessing later:

- **R** — a trade's result measured as a multiple of what you risked, not in dollars. Risk $100 (the distance from your entry to your stop-loss) and make $150, and that trade is "+1.5R." Lose the full $100, and it's "−1R." Every trade gets measured on the same scale regardless of position size.
- **Expectancy** — the average R you make per trade, averaged across every trade, wins and losses together. An expectancy of +0.10R means every trade nets you, on average, one-tenth of whatever you risked.
- **Profit factor** — total R earned by winning trades divided by total R lost by losing trades. Above 1.0 means the winners outweigh the losers overall; below 1.0 means they don't, no matter how it feels trade to trade.
- **Stop-loss** — a price you set in advance where you'll exit automatically if the trade goes against you, capping the damage.
- **Gap-through** — when a stock's price jumps overnight past a price level (like your stop) without ever actually trading there. The market just reopens somewhere else the next morning.

## Why this test happened

The system this research is about buys stocks two ways: **breakouts**, buying as a stock pushes to a new high on the bet that momentum carries it further; and **pullbacks**, buying a short dip inside an existing uptrend on the bet that the dip is temporary and the trend resumes. Both setups already exist in the live system. What Experiment 05 tested was something narrower — not when to buy, but when to sell. Could a different exit rule beat the one already in use?

Three exit approaches went into the test, alongside the system's current one:

- **The incumbent** (what the system already does) — sell part of the position once it's up 2.5R, move the stop to breakeven once it's up 1R, trail the rest under a moving average, and force an exit after 15 trading days no matter what.
- **Touch** — much simpler: close the whole position the instant it touches a target, like +2.0R. No trailing, no partial exits.
- **Step ratchet** — a stop that "ratchets" upward as the trade goes your way, locking in +1R once you're up that much, then +2R, then +3R, always trailing the price higher instead of sitting still.

All of it ran on 11,267 historical buy signals from before 2013 — the "in-sample" data this research series is always allowed to explore freely, kept separate by a hard rule from later data reserved for a real, one-shot test. 4,171 of those signals survived the system's other filters. That's a large enough sample to trust the result, not a handful of lucky trades.

## The pullback results — and the one that looked like a real win

Here's what the pullback setups produced, tested as originally coded:

| Exit rule | Win rate | Expectancy | Profit factor | Median trade |
|---|---|---|---|---|
| **Step ratchet, 1.0R** | **54.1%** | **+0.1002R** | 1.208 | **+0.474R** |
| Step ratchet, 2.0R | 42.8% | +0.1039R | 1.173 | −0.787R |
| Incumbent (current system) | 26.6% | +0.0609R | 1.120 | −0.130R |
| Touch, 2.0R | 43.1% | +0.0209R | 1.035 | −0.760R |

Read the incumbent row through the risk:reward math from the opening. It wins barely more than one trade in four — well below a coin flip — and its *median* trade (the outcome you'd land on if you lined up every trade from worst to best and picked the one in the middle) actually loses money, at −0.130R. And yet its *average* trade (its expectancy) is positive, at +0.0609R. Those two facts only coexist if the wins, when they come, are considerably bigger than the typical loss. That's not a flaw in the system. That's exactly the "low win rate, big reward" case from the opening math playing out in real trade data — it works precisely because it isn't trying to win often.

Step ratchet at the 1.0R level looks like something else entirely: a *high* win rate (54.1%, better than a coin flip) stacked on top of a *positive* median trade (+0.474R) and the best expectancy in the table. That's not "wins big occasionally" — that's winning often *and* winning well, on the same cell. It was, in the researchers' own words, the only cell in the entire study with a positive median trade. That combination is rare enough that it deserved real suspicion instead of a celebration lap, and to their credit, that's exactly what happened next.

## The breakout results: dead on arrival either way

The published paper's own prose only states expectancy for the breakout side under corrected fills, not win rate — so I pulled every win rate directly from the study's own published data file (`exit_grid_both_conventions.csv`) rather than leaving them out or guessing. Here's how breakout looked under the original, uncorrected assumption — the same one that's about to get fixed in the next section:

| Exit rule | Win rate | Expectancy |
|---|---|---|
| Incumbent | 25.95% | −0.0745R |
| Touch, 1.0R | 49.21% | −0.0837R |
| Touch, 1.5R | 43.72% | −0.0902R |
| Touch, 2.0R | 43.26% | −0.0724R |
| Step ratchet, 1.0R | 49.58% | −0.0335R |
| Step ratchet, 1.5R | 43.63% | −0.0615R |
| Step ratchet, 2.0R | 43.07% | −0.0590R |

Every single cell is already negative here, before any correction. Some of these win rates (49%, even touching 50%) look perfectly respectable next to the incumbent pullback's 26.6%. It doesn't matter. None of them clear the bar, because on this setup the wins aren't big enough relative to the losses to make even a coin-flip win rate pay for itself. Same lesson as the opening math, running in the opposite direction — a healthy-looking win rate paired with a bad risk:reward is exactly as useless as a low win rate paired with a good one is valuable.

Apply the same stop-fill correction covered next, and breakout doesn't recover — it gets worse across the board:

| Exit rule | Win rate (corrected) | Expectancy (corrected) |
|---|---|---|
| Incumbent | 25.95% | −0.0944R |
| Touch, 1.0R | 49.21% | −0.0915R |
| Touch, 1.5R | 43.72% | −0.0985R |
| Touch, 2.0R | 43.26% | −0.0808R |
| Step ratchet, 1.0R | 48.47% | −0.1033R |
| Step ratchet, 1.5R | 43.16% | −0.1113R |
| Step ratchet, 2.0R | 42.79% | −0.0984R |

Every expectancy figure got worse, not better — the incumbent drops from −0.0745R to −0.0944R, and step ratchet 1.0R falls hardest, from −0.0335R to −0.1033R. The win rates barely move for touch and the incumbent — those exits trigger off a price target being touched, not off the stop, so an overnight gap through the stop rarely changes whether the trade counted as a win at all, only how much was won or lost. Step ratchet dips a little in every cell, for the same reason it took the biggest hit on the pullback side: its stop sits closest to the market, so it's the exit style most often gapped through. Breakout was never a false positive the way pullback's step ratchet was — it was already dead before correction, and correction just widens the margin.

## The $98 stop that becomes a $91 fill

Back to the pullback side, and the cell that looked too good: step ratchet at 1.0R. Chasing down *why* it won led to one line of code nobody had looked at twice: how the backtest decides what price a stop-loss actually fills at when the market gaps past it overnight.

Here's the plain version of the problem. Imagine you set a stop-loss at $98 on a stock that closed at $100. Overnight, bad news breaks, and the stock opens at $91 the next morning. You don't get $98. You get roughly $91 — your order fills wherever the market actually reopens, not at the price you'd hoped for. The backtest was assuming you'd always get $98. Every time.

That assumption isn't crazy on an ordinary day, when the market doesn't gap past your stop at all. It's only wrong on the days it actually happens — and once the researchers checked, it happened a lot: 11.6% of all 32,748 historical trades in the study exited on a day that gapped straight through the stop.

The step ratchet's whole design is a stop that trails close behind the current price, ratcheting up as the trade goes your way. That's also exactly what makes it collect this error the most. A stop sitting right under the market gets gapped through far more often than one sitting well below it — and the step ratchet at 1.0R got gapped through **32.7%** of the time, close to **three times** the incumbent's **11.0%**. Once the fills were corrected to reflect what a trader would actually have gotten, that −0.107R gap-through cost wiped out essentially the entire edge. Step ratchet 1.0R went from the best cell in the study, +0.1002R, to a loser, −0.0067R. It hadn't found a better way to sell. It had found the exit style that benefited most from a backtest quietly being too generous to everyone — and collected more of that generosity than the rest.

## The bigger number this changes

Here's where it stops being an interesting footnote about exit rules and becomes something that changes what the whole system's track record actually says. The same flawed assumption — stops always fill exactly where you set them — sits underneath the flagship backtest of the entire trading system, measured across more than four decades of history (October 1982 to July 2026), run with the system's regime gate switched on — its actual, live configuration:

| | As published | Corrected for real stop fills |
|---|---|---|
| Total return | **+17.73%** | **−38.98%** |
| Max drawdown (the biggest peak-to-trough loss the account went through along the way) | −43.84% | −67.06% |
| Worst single trade | −3.63% of equity | −11.78% of equity |

Same 1,200 trades in both columns — correcting the assumption doesn't change *which* trades were taken, only what they were actually worth. And the number that gets erased is the one that mattered most: a system that was published as modestly profitable over 44 years is, once you fill stops the way real markets actually fill them, a system that lost nearly 39% over that same stretch.

One thing genuinely survives this correction — and it's important to be exact about which one. The system has a rule — a "gate" — that's only supposed to trade during favorable market conditions. Turn that gate off entirely, and the corrected result is worse still: −75.52%, with a deeper drawdown too. So the gate is still doing real work — a losing system with the gate on lost roughly half what the same system lost with it off. What does *not* survive is the claim that mattered to anyone actually trading this: that the system, as a whole, made money. It didn't. Cutting your losses roughly in half is a real, useful thing for a trading rule to do. It is not the same thing as having an edge, and the corrected numbers make that distinction impossible to paper over.

## The lesson

A hidden assumption baked into how you test a trading idea doesn't just make everything look a bit better across the board. It plays favorites — and it favors whichever strategy happens to lean on that particular assumption the hardest. The step ratchet didn't win the exit-rule test because it was a genuinely better way to sell. It won because its whole design (a stop that trails close to the market) made it the strategy most exposed to an error that was quietly subsidizing everyone a little, and it collected the biggest subsidy. Nothing about how the test was run would have caught that on its own — the sample was large enough, the result held up when split in half, and it wasn't riding on a handful of lucky trades. Every ordinary check passed. The number underneath all of them was still wrong.

That's the actual, practical takeaway, and it's not "check for gaps in your backtest," useful as that specific fix is. It's this: when you're comparing two strategies on the same testing tool, ask which of that tool's built-in assumptions each strategy depends on more than the other — because if there's a difference, that assumption isn't neutral. It's deciding your winner for you.

And for what it's worth, here's where that leaves the actual trading system behind all this: it's a disciplined way to generate and log candidate trades, not a proven money-maker, and — now backed by the corrected math instead of the original, flattering version of it — it shouldn't be sized like one.

[The full paper, data, and reproduction steps](https://github.com/konradb-gh/trading-research/tree/main/experiments/05-stop-fill-assumption) are in the repo.
