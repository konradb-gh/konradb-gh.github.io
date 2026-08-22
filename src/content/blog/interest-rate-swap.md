---
title: "Interest Rate Swaps, Explained"
description: "A contract to trade interest payments without ever swapping the actual debt. What an interest rate swap is, who actually uses one, and why they matter more when rates look like they do right now."
pubDate: 2026-08-22
tags: ["interest-rate-swaps", "derivatives", "fixed-income", "glossary", "interest-rates"]
slug: "interest-rate-swap"
category: "glossary"
---

An interest rate swap is a contract between two parties to exchange interest payments on a set amount of money, without ever exchanging the underlying principal itself. Most commonly, one side pays a fixed rate and the other pays a floating rate that resets periodically. That's the whole idea. Everything else is detail.

## The analogy

Say you and a friend each owe $300,000 on a mortgage. Yours is fixed at 6%. Hers floats with the market — 5% one year, maybe 7% the next. Neither of you wants to actually refinance; that means new paperwork, new fees, and your bank isn't going to let you hand your loan to a stranger anyway. So instead, you make a private side deal: each month, you work out what the other person's payment would have been under your rate instead of theirs, and whoever comes out behind on paper pays the difference to the other.

Your actual mortgages never move. Your bank still bills you at your fixed rate, and hers still bills her at whatever the floating rate reset to. But between the two of you, you've swapped the exposure — she now effectively has a fixed payment, and you're now effectively riding the market. Scale that up to institutional size, swap the friend for a bank or a dealer as the counterparty, and that's functionally an interest rate swap.

Two terms worth pinning down here, since neither is optional vocabulary once you're actually reading about swaps: the **notional amount** is the number the payments get calculated against — the $300,000 in the mortgage version above — and it's never actually paid by either side, it just sets the math. The **floating rate** is whatever resets periodically off a public benchmark, most commonly SOFR (the Secured Overnight Financing Rate) today, so that side's payment never sits still for long.

## Who actually does this, and why

A company that borrowed at a floating rate — a corporate loan tied to SOFR, say — but wants to know exactly what it owes every quarter for budgeting purposes can swap into paying fixed, handing the uncertainty to a bank willing to take it on. Banks run a version of this too, though for a different reason than the company above. A bank holding a large book of fixed-rate mortgages isn't funding those loans with fixed-rate money — it's funding them with deposits and short-term borrowing that cost a floating rate. So when rates rise, what the bank pays out on its funding goes up while what it collects on those old fixed-rate mortgages doesn't move at all, squeezing the gap between the two. The fix is the same shape of swap as the company's: the bank pays a fixed rate and receives a floating one, so the floating payments it takes in rise right along with its own rising funding costs and cancel the squeeze out. In the ordinary version of this trade, neither side is speculating. Both are converting a risk they already have into a shape they'd rather hold.

## Why this matters more right now

I wrote earlier this month about [the Fed holding its policy rate at 3.50%–3.75% under a new, less-forthcoming chair](/blog/fed-september-2026-rate-decision), and separately about [the Treasury scrambling to manage a 30-year yield that had just touched a 19-year high](/blog/treasury-bond-buyback-2026). Both are versions of the same underlying condition: rates that are elevated and genuinely uncertain, not calm and drifting.

That's exactly the environment where a swap stops being a rounding error and starts being worth paying for. When policy rates are stable and long yields aren't moving much, a floating-rate borrower isn't losing sleep — next quarter's payment probably looks a lot like this quarter's. When the Fed's next move is a real open question and the long end of the curve can reprice by the better part of a percentage point in a matter of months, the value of locking in certainty goes up a lot, because the cost of guessing wrong has gone up too.

There's no trade recommendation buried in any of this. A swap doesn't create money or destroy it — it just moves who's holding a specific kind of risk from one balance sheet to another. Understanding that mechanism is the useful part. Picking a side isn't the point of this post.
