# Issue 4 QA v1

Reviewed source head: `6fd25bd48d66b686461c694c8cd5ac01c7e4a941`, base `origin/staging`.
Classification: feature, offline Python command, no UI, money, auth or migration changes.
Preflight: proceed, no duplicate, overlap or semantic candidates. Tests use only the local synthetic corpus.

## Independent review hypotheses

- Precision uses prediction-column totals; recall uses reference-row totals. Fixed six-pair expectations and a rejected denominator mutation confirm this.
- Each reference is scored against its own case; labels remain independent of predictions. Case-specific canary tests include a different-case canary witness.
- The report exposes disagreement without claiming human review or real-world accuracy. CLI output states both limits.
- Only the corpus, validator and tests implement this card. The supervisor's README scope finding is fixed; README is absent from the diff.

## Acceptance criteria and test gaps

All paths below are relative to `ai-prompt-injection-security-testing/`.

| AC | Unit | Command integration | Browser | Result |
|---|---|---|---|---|
| 1: 40+ entries, 8+ per outcome | `tests/test_validate_scorer.py:74` | independent count: 48, 16 each, 16 cases | n/a, CLI | pass |
| 2: per-outcome precision/recall, exit 0 | `tests/test_validate_scorer.py:15` | `tests/test_validate_scorer.py:85`, numeric rows at :94 | n/a, CLI | pass |
| 3: synthetic and accuracy caveat | n/a, output contract | `tests/test_validate_scorer.py:88` | n/a, CLI | pass |
| 4: fixed-example metric maths | `tests/test_validate_scorer.py:15` | n/a, arithmetic seam | n/a, CLI | pass |

Zero denominators, empty prediction list, invalid labels, duplicate IDs, unknown cases, non-object records, invalid response types and missing reasons are pinned by existing tests. No High gaps remain. Strengthened the existing CLI assertion so confusion-matrix names cannot hide a missing metrics row. It rejects a removed PASS row before passing with the original source restored.
Test gaps (not written): Medium, main's malformed schema and synthetic-flag rejection branches lack direct regression tests. Low, spacing and scorer-version copy are not pinned. Auth, dates, volume paging, races and accessibility are n/a to this offline batch command.

## Evidence and truth check

`tests.log`: 20 tests pass, exit 0. `cli.log`: command exits 0 and reports all three metrics and matrix rows. Manual fractions from the displayed counts match printed values: PASS 11/13 and 11/16; PARTIAL 16/23 and 16/16; FAIL 12/12 and 12/16.
`mutation-cli-row.log` and `mutation-metrics.log`: both deliberate defects fail with exit 1; source restored after each, no application-code changes committed.
Inline standards review: 0 findings. Inline spec review: 0 findings. Code-grounding 95/100, local-history check 95/100, aggregate truth 95/100, threshold 70. Scorer implementation remains unchanged; its existing limitations are measured, not repaired by this card. Labels are AI-authored synthetic judgements, not independently human-reviewed.
Prior finding: supervisor README scope drift fixed, 1 fixed, 0 not fixed, 0 no longer applies. No prior reviewer report or QA-owned finding threads exist. Author explanation threads are preserved.
No screenshots: all four ACs are non-visual. No external service, secret, migration or merge is needed in QA. Reviewer owns the merge decision.

Local tests: `cd ai-prompt-injection-security-testing && python3 -m unittest discover -s tests -t .`
