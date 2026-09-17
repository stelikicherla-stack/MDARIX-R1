# R1 Day 16 Manual UI Validation Checklist

- [ ] Open Investigations and confirm the Counterfactual workflow tab retains the selected investigation, ProductVersion, and temporal context.
- [ ] Select readable intervention type and target; confirm no raw UUID is required as the primary interaction.
- [ ] Run Counterfactual and observe validating/running, success, insufficient-evidence, unsupported, empty, and error feedback states.
- [ ] Confirm the result is labelled `COUNTERFACTUAL / WHAT-IF — NOT OBSERVED EVIDENCE`.
- [ ] Review baseline, invariants, affected/unsupported relationships, unexplained observations, hypothesis impact, Failure Chain impact, unknowns, limitations, evidence needed, and provenance.
- [ ] Repeat in Current, Event-as-of, and Known-as-of modes.
- [ ] Rapidly change investigation/version/date/mode while a request runs; confirm the old result cannot overwrite the new context.
- [ ] Open Decision Center and confirm counterfactual output is explanatory hypothetical context, not source evidence or a human decision.
- [ ] Repeat at 1920x1080 and 1366x768; confirm no major horizontal overflow or clipped primary controls.

Manual status: PENDING HUMAN VALIDATION. No item is marked PASS until performed by a human or approved browser automation.
