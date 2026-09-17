# Failure Chain Contract

`FailureChainSet` contains one or more `FailureChain` records. Each `FailureChainLink` must have one of `OBSERVED_SOURCE_SUPPORTED`, `DETERMINISTICALLY_DERIVED`, `HYPOTHESIZED`, `CONTRADICTED`, or `UNKNOWN_GAP`. A chain reports unresolved and contradictory links, temporal consistency, limitations, provenance, and human-review status.
