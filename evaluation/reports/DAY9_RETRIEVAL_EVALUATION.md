# Day 9 Retrieval Evaluation

## Scope

Evaluation covers the Day 9 trusted retrieval foundation at the controlled R1 Golden Dataset scale.

## Actual Run Results

- Automated Day 9 tests: `14 passed`
- Day 9 validator: PASS
- Full regression after Day 9 implementation: `155 passed`
- pgvector: PASS
- Indexed tenant chunk embeddings observed by validator: `5`
- Failed embedding rows observed by tests: `>=1` controlled failure
- Retrieval provenance rows observed by validator: `28`

## Retrieval Metrics

The current R1 dataset does not yet contain a formal Day 9 relevance-label file separate from Ground Truth. Broad Precision@K, Recall@K, Hit Rate@K, and MRR are therefore not reported as statistical benchmark metrics.

Controlled gate metrics from automated tests and validator:

| Metric | Result |
| --- | --- |
| Source-anchor coverage | 100% for material retrieved results |
| Wrong tenant count | 0 |
| Wrong Product presented as applicable | 0 |
| Wrong Version presented as applicable | 0 |
| Future evidence leakage in KNOWN-AS-OF | 0 |
| Ground Truth indexed | 0 |
| Ground Truth retrieved | 0 |
| Duplicate logical chunk results | 0 in controlled tests |
| No-match false positive | 0 |
| Silent embedding failure | 0 |
| Unsupported causal conclusions | 0 |

## Individual Failures

No Day 9 validator failures were observed.

## Limitation

Formal Golden Scenario retrieval labels should be added before claiming broad Precision@K or Recall@K across all VS001-VS012 questions.
