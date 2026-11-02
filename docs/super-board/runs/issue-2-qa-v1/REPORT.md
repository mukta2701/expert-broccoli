# Issue 2 QA v1

Tested builder head `5fff50333fcccbb6203b3dd6fd06bb660486de2d` against
`origin/staging` at `ecf3dfeb316f4a9900fa101ddaf06902e9f44893`.
Classification: bug, synthetic arithmetic, non-visual, no money/auth/schema change.
The same issue branch is checked out detached in the QA worktree because the
preserved builder worktree still owns its local branch. No main-checkout edits.

## Preflight and independent hypotheses

- Issue-scoped preflight returned proceed, with no duplicate, overlap or ambiguity.
- The issue has four observable ACs and no dependencies. PR #22 targets staging.
- PR review threads were fully read. No QA findings or human requests were present.
- The global onboarding `docs/super-board/pre-flight.md` is absent. This direct lane
  invocation runs issue-scoped checks and does not certify a fresh board-run preflight.
- Hypothesis 1: response-only risk remains equal for PASS, PARTIAL and FAIL.
- Hypothesis 2: each additional capability raises nonzero risk and preserves zero.
- Hypothesis 3: both scorers share the arithmetic without changing outcome decisions.
- Hypothesis 4: exported results describe the same formula as the schema.

## AC ledger

Paths below are relative to `ai-prompt-injection-security-testing/`.
Component means the local runner integration. Browser e2e is n/a for every AC,
because this project has no browser interface.

| AC | Unit assertion | Component assertion or inspection | Result |
|---|---|---|---|
| 1: adjusted risk never below plain | `tests/test_engine.py:122`; `tests/test_exposure_contract.py:50` | `tests/test_engine.py:171`; CLI per-case checks in `cli.log` | Pass |
| 2: none gives equality | `tests/test_engine.py:146`; `tests/test_exposure_contract.py:53` | n/a: public scorer owns the arithmetic | Pass |
| 3: increasing capabilities cannot lower risk | `tests/test_engine.py:156`; `tests/test_exposure_contract.py:57` | n/a: public scorer owns the arithmetic | Pass |
| 4: documented formula and rule tests | `tests/test_engine.py:113,140,148`; new matrix test | Manually compared `tester/results_schema.md:60-61`, `tester/scoring_criteria.py:118`, and exported methodology in `cli.log` | Pass |

## Test gaps and edge cases

The existing suite pins all 16 fixture cases and all three primary outcomes.
The added public-boundary test pins both scorers, all 25 likelihood/impact pairs,
all 16 valid capability sets, and all three outcomes: 2,400 evaluations.
This covers the 1 and 5 numeric boundaries, zero risk, half-risk and full-risk,
response-only equality, capability identity, cardinality, and equal-cardinality ties.
Known literal factors are independent expectations; assertions observe public results.
Existing exact 25/50/75/100/125 FAIL examples protect the adjusted arithmetic itself.
Original division by five and a removed capability increment each failed the new
test in a separate process. The original source was restored before the green run.
No application code changed during QA.

Invalid input/error handling is unchanged; existing loader rejection tests pass.
Money, dates, auth/ownership, races, volume/paging, UI states and accessibility are
n/a to this pure local arithmetic diff. Test gaps (not written): Low, permutations
of a capability list are not separately enumerated; production uses a set.
No High gaps remain. No tests assert solely on mocks or use computed results as
an oracle. Full-suite and mutation outputs are captured alongside this report.

## Results and truth check

`cd ai-prompt-injection-security-testing && python3 -m unittest discover -s tests -t .`
passes 18 tests. The verbose run is in `tests.log`.
Both CLI modes succeed with matching results/companion manifests. Safe averages
remain 0.0/0.0; unsafe averages are 17.69 plain and 38.75 adjusted. Sixteen unsafe
cases FAIL as expected; all sixteen safe cases PASS. Screenshots are intentionally
omitted because every AC concerns CLI/scorer behavior, not UI.

Inline Standards review: 0 findings. Inline Spec review: 0 findings.
Truth confidence: 98/100, above the configured 70 threshold. Direct source,
independent expected factors, mutation rejection and CLI observations support all
four hypotheses. These tests establish a synthetic scoring contract only.
QA performs no migrations or merges. Reviewer owns the merge gate.
