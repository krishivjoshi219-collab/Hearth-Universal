# Savings Methodology: How Every Dollar Figure Is Computed

> **All figures below are generated from live code, never hand-typed.**
> Run `python3 scripts/export_savings_figures.py` to regenerate
> `docs/savings_figures.csv` + `docs/savings_figures.json` and diff.
> Inputs are declared sandbox fixtures (`commerce.sandbox_disclaimer()`);
> **the arithmetic on those inputs is real** and shown step-by-step here.

## 1. Subscription hygiene: $803.76/yr

Source: `SUBSCRIPTION_SERVICES` (`src/hearth/commerce.py`) →
`scan_subscriptions()` → `potential_annual_savings = sum(savings_yr)`.

| Service | Annual cost | Usage evidence | Action | Savings/yr |
|---|---|---|---|---|
| StreamBox 4K Family Plan | $239.88 | Dormant (0 streams in 60d) | cancel | $239.88 |
| Metro Fitness All-Access Plus | $780.00 | Low (1 visit in 45d) | downgrade to Standard $35/mo | $360.00 |
| Ultra Cloud Gaming Ultimate | $203.88 | Inactive (no sessions) | cancel | $203.88 |
| Echo Music HD Family | $203.88 | Active (daily, 4 Echo devices) | keep | $0.00 |
| Secure Vault Cloud Storage 2TB | $119.88 | Active (1.82 TB / 91%) | keep | $0.00 |
| **Total recoverable** | | | | **$803.76** |

Formula: `239.88 + 360.00 + 203.88 = 803.76`.
Rule: flag `cancel` when dormant ≥60d, `downgrade` when utilization <10%.
Nothing is cancelled by the agent — each becomes a Tier-2 Approval Tray
proposal (`cancel_subscription` / `downgrade_subscription`).

## 2. Subscribe & Save cart bundle: $22.28 per staged cart

Source: `stage_amazon_cart()` — sums pantry staples at regular price,
applies the 15% multi-item S&S tier, returns
`{regular_subtotal, final_total, savings}`.

Measured: `regular $148.46 → final $126.18`, **savings $22.28**
(`savings = regular_subtotal − final_total`).
Per-order savings recur with every replenishment cycle; the tray card shows
the exact cart math before any human approves.

## 3. Swarm VPP microgrid: +$0.55/hr seller, +$1.16/hr buyer, $2,496/yr retained

Source: `coordinate_microgrid()` uniform-price double auction
(`src/hearth/swarm.py`).

Measured clearing: 3.8 kW @ **$0.18/kWh**
(vs utility buyback $0.035 and peak tariff $0.485):

- `seller_gain = 3.8 × (0.18 − 0.035) = $0.55/hr`
- `buyer_save = 3.8 × (0.485 − 0.18) = $1.16/hr`
- `community_dividend = 0.55 + 1.16 = $1.71/hr`
- `annualized = 1.71 × 4h/day × 365d = $2,496.60/yr` retained locally
- `carbon = 3.8 × 0.85 = 3.23 kg CO₂e/hr` avoided peaker dispatch

Assumption stated plainly: 4 peak solar hours/day. Change the assumption
and the sheet recomputes — the auction math doesn't.

## 4. Predictive acoustic part: $12.74 vs $14.99 (+$450 compressor saved)

Source: `scan_appliance_acoustics()` — real `numpy.rfft` over a synthesized
bearing signal (fault sidebands + noise), SNR/kurtosis health scoring,
exponential RUL. On detection it stages the OEM damper/belt kit
(ASIN `B09SZBELT1`): `final = 14.99 × (1 − 0.15) = $12.74`.
Catching the bearing weeks early avoids a ~$450 compressor replacement —
that avoided cost, not the $2.25 discount, is the headline.

## 5. Honesty appendix

- Fixture inputs are synthetic (sandbox twin, no real bills/utility API).
- Every formula above executes in code paths covered by the 213-test suite.
- Reproduce everything: `python3 scripts/export_savings_figures.py`
  then `git diff --stat docs/savings_figures.*` — empty diff means docs == code.
