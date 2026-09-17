# R1 Day 14 Host UI Validation Checklist

Run on the Windows host after PostgreSQL, backend, and frontend are running. Do not fill Actual or Result before performing the check.

| Screen | Action | Expected result | Actual result | Pass/Fail | Notes |
|---|---|---|---|---|---|
| Investigation Workspace | Select the primary investigation | Product, ProductVersion, complaints, timeline, evidence, limitations, provenance load |  |  |  |
| AI Investigator | Run Analysis | Observations, explanations, contradictions, gaps, questions, limitations, and sources appear; no root-cause winner |  |  |  |
| Hypotheses | Generate Hypotheses | Competing hypotheses show support, contradiction, assumptions, gaps, temporal fit, weakening conditions, provenance |  |  |  |
| Challenger | Review Day 13 output | Challenges, contradictions, temporal concerns, assumptions, alternatives, confounders, provenance visible |  |  |  |
| Unknowns Radar | Run Unknowns & Chain | Unknowns show why they matter, resolution requirement, status, temporal context, provenance; not negative facts |  |  |  |
| Failure Chain | Review chain links | Each link labels source-supported, deterministic, hypothesized, contradicted, or unknown/gap; broken chains stay broken |  |  |  |
| UI states | Exercise loading, empty, error, partial, stale, insufficient-evidence, permission-denied paths | UI remains usable and does not show partial data as complete or leak backend errors |  |  |  |
| Temporal switch | Switch Current/Event/Known and change context rapidly | Late responses do not overwrite selected context; future evidence is not historical |  |  |  |

Record browser, timestamp, investigation ID, backend commit, and screenshots/logs in the live integration report. A source-code build is not a substitute for manual checks.
