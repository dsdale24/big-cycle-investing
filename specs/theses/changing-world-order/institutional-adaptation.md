# Institutional adaptation thesis

**Status:** `active`
**Scale:** transition (primary); may have cyclical signatures

## Claim

The printing-press → Reformation arc — information access outpacing institutional adaptation, producing ~century of religious and political upheaval before societies reorganized — is a complementary precedent to empire decline. It's a **different transition mode**: technology-driven rather than resource-exhaustion-driven, faster in onset, and characterized by coalition-scrambling along adoption-vs-resistance lines rather than the class/sectional lines of classical debt-cycle transitions. The AI transition may be early in a similar arc, and US constitutional rigidity (a governance interface frozen in 1787 with a deliberately hard amendment process) is a mode-of-failure specifically sensitive to this class of transition.

## Rationale

The original framing from conversation with Darren:

> Language itself is a living interface — and every governance system has to decide how much drift between the words and the world it can tolerate before it breaks. The US Constitution essentially froze that interface in 1787 and built an amendment process so deliberately hard that originalism vs. living-constitutionalism became the central jurisprudential fight. Meanwhile AI context management is the opposite philosophy: meaning is continuously renegotiated, stale context is pruned, new context loaded. One optimizes for stability, the other for adaptability.
>
> Historical parallel worth noting: the printing press produced roughly a century of religious and political violence before societies reorganized around it. The Reformation wasn't just theological — it was what happens when information access outpaces institutional adaptation. We might be early in a similar arc.

Key distinction from reserve-currency / empire-decline transitions:

| Transition mode | Driver | Timescale | Cleavages |
|---|---|---|---|
| Empire decline (Dutch, British) | Resource exhaustion, fiscal over-extension, relative decline of productive base | 50-200 years | Class, sectional, center vs. periphery |
| Technology-adaptation (printing press, potentially AI) | New information-access regime outpacing institutional change rate | 50-150 years | Adoption vs. resistance, cuts across existing political coalitions |

Peer democracies (UK, NZ, Germany) have more adaptive constitutional frames and may be more resilient to this mode. US rigidity is an outlier, not a template.

## Implications

- Civilizational indicators should capture *both* transition modes, not just classical inequality/trust measures. The Internal Order Stress Index (from notebook 02, ported to `src/indicators.py` in PR #4-Path-A) measures classical stress (Gini + EPU + sentiment). A separate dimension for technology-adaptation stress is missing.
- Possible operationalizations for technology-adaptation stress worth discussing before coding: public-sector AI adoption rate, court backlog for new-technology cases, legislator median age / tech-literacy survey data, regulatory delay (time from new-tech emergence to first rule), patent-vs-regulation adoption gap.
- Cross-national comparison is even more important under this thesis — US rigidity is an outlier. UK, NZ, Germany provide natural control cases.
- The thesis is about *signal interpretation*, not about what assets to hold. It argues for broader indicator and data scope; it does not prescribe allocation shifts directly.

## Current evidence

Thesis is structural/historical, not instrumented for direct empirical test on the current dataset. Indirect support: Reformation period asset outcomes (~1520-1650, holders of church/feudal-tied assets lost substantially; gold and land held outside institutional ties fared better) — but data quality for that era is weak for backtesting.

## What would test this

- Cross-national comparison during the AI transition: do adaptive-governance democracies (UK/NZ/Germany) show different civilizational-stress signatures than rigid ones (US)? Requires same-metric cross-national data.
- Retrospective: do countries that adapted more quickly to new information regimes (telegraph, radio, television, internet) show different long-term outcomes than those that didn't? Historical-pattern work, hard to quantify.

## What would falsify this

- Evidence that historical technology-adaptation transitions played out without the institutional-upheaval signature — e.g., if we looked at printing-press diffusion and found countries that adapted their governance structures proactively had similar political volatility to those that didn't. Would falsify the mechanism claim.
- Evidence that the current AI transition will follow existing cleavages (left/right, class/sectional) rather than scrambling coalitions — would refine rather than falsify.

## Related

- `civilizational-leads-financial.md` — tests whether the stress index (classical version) leads financial stress; does not currently capture technology-adaptation stress, so a null result doesn't falsify this thesis
- `backtest-sample-scope.md` — cross-national data required to test this thesis at transition scale
