# Yield Curve Sensitivity Analyzer

Prices a bond portfolio against a baseline spot curve and a few shocked versions of it. Instead of discounting everything at one yield, it discounts each cash flow at the spot rate for that point on the curve.

## What it does

If you discount every cash flow at a single rate, you're assuming a flat curve, which is basically never true. This reads a term structure from a CSV, interpolates across it, and prices each cash flow at the rate that actually lines up with its timing, fractional years included.

It deals with a few annoying cases:

- **Odd first periods.** Bonds don't always have a clean number of whole periods left. It works out the stub and builds the cash flow schedule from there.
- **Different coupon frequencies.** Annual, semi-annual, quarterly all work, just set `coupon_frequency`.
- **Missing tenors.** Your CSV won't have a rate for every fractional date a bond needs, so anything in between gets interpolated and anything past the end gets extrapolated.

You get a table of each bond priced under every curve, so you can see straight away how much each one moves when rates shift.

## Setup

```bash
git clone https://github.com/jacobnagora/yield-curve-analyzer.git
cd yield-curve-analyzer
pip install pandas numpy scipy
python main.py
```

It comes with a sample `data.csv`, so it runs straight out of the box. The output is a table of every bond priced under every curve.

## Using your own data

The sample CSV is just a starting point. To run it on your own curves, open `data.csv` and edit it, in Excel, a text editor, whatever's easiest. Change the yield numbers, add or remove tenors, swap in entirely different curves. As long as the column format holds (below), the script picks up your changes on the next run. Nothing in the code needs touching.

## Input format

`data.csv` needs a `Tenor (Maturity)` column and one column per curve. Tenors can be in months (`1-Month`, `3-Month`) or years (`2-Year`, `10-Year`), it sorts that out either way. Yields are read as percentages (`4.25%`) and turned into decimals for you.

A row looks like:

| Tenor (Maturity) | Baseline Yield (Spot Rate) | 2-Year Shock Curve | 5-Year Shock Curve | 10-Year Shock Curve |
|---|---|---|---|---|
| 3-Month | 4.85% | 5.35% | 5.10% | 4.95% |
| 2-Year | 4.20% | 4.95% | 4.55% | 4.30% |

One thing to be mindful of: the script assumes the first three rows are sub-year tenors (i.e. in months) and converts them to fractional years. Keep your shortest maturities at the top and adjust as necessary.

## How it works

1. Load the curves and convert all the tenors to years.
2. Turn the percentage yields into decimals.
3. For each bond, build the cash flow schedule, grab the right rate at each payment date, discount, and add it up.
4. Run every bond against every curve and print the result.

The heart of it is `calculate_bond_price()`, which takes a bond and a curve and hands back a price.

## Roadmap

- Key rate durations (KRD) per bond
- Effective duration and convexity
- Portfolio-level totals across positions
