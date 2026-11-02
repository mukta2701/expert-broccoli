# Issue 3 QA, version 1

Tested input: `6efc9ef75df60b3aa3ac93a01b68426089a2ab46`.
Builder head: `eae03509df0e6042c6ca32fd68e9df0636919785`.
Base: `origin/staging` at `cbcec7a40dfb5b1839e450667762c83d89daab98`.
The input includes a pre-existing merge of staging's GitHub-read helper fix.
The issue diff against that base adds only the licence, policy and workflow.
QA adds this report and command output. No application code changes.

## Acceptance evidence

| AC | Observable check | Result |
|---|---|---|
| 1 | `cmp LICENSE /tmp/sb-issue3-qa/apache-canonical.txt`, downloaded with `curl -fsSL https://www.apache.org/licenses/LICENSE-2.0.txt` | PASS, exact bytes; SHA-256 in verification.txt |
| 2 | Inspect `SECURITY.md:5-16` and `SECURITY.md:20-27` | PASS, private advisory route, safe fallback, no live payloads, only the local mock authorised |
| 3 | `actionlint .github/workflows/tests.yml`; inspect lines 3, 12-14, 23; execute its command | PASS, push and pull_request, project working directory, 14 tests pass |
| 4 | GitHub REST run and job evidence for PR 14 | PASS at builder head, run 41372628770, pull_request, success; every job step succeeded |

Original PR run: https://github.com/mukta2701/expert-broccoli/actions/runs/41372628770
Original push run: https://github.com/mukta2701/expert-broccoli/actions/runs/41372600547
Both runs completed successfully with head `eae03509df0e6042c6ca32fd68e9df0636919785`.
The handoff comments and PR AC block record fresh CI for the evidence commit.

## Test-gap ledger

| AC | Unit | Component | Integration / e2e |
|---|---|---|---|
| 1 | n/a, static licence | n/a, no component | Exact canonical byte comparison in verification.txt |
| 2 | n/a, prose policy | n/a, no component | Manual policy review at the lines above; browser n/a |
| 3 | Existing `tests/test_engine.py:22-198`, 14 tests | n/a, no component | actionlint plus successful Actions execution with configured cwd and command |
| 4 | n/a, hosted workflow result | n/a, no component | REST run and job conclusions, PR association and full head checked |

Boundary review: no changed runtime inputs, error paths, dates, money, ownership,
races, volume or UI state. Workflow events, working directory, Python version,
read-only permissions and checkout credential persistence were checked explicitly.
No new tests were needed for this documentation and CI-only change.
Existing tests assert concrete scoring, migration and runner outputs rather than mocks.
No high-risk logic changed, so mutation testing is not applicable.
Test gaps (not written): none within the four ACs.
Screenshots omitted intentionally because no UI changes or visual ACs exist.

## Independent review and truth check

Performed inline as required by the Codex worker adaptation.
Standards: 0 findings. Spec: 0 findings. Prior reviewer findings: none.
Five author notes were read, including all replies; no QA requests remain open.
Truth confidence: 98/100, above the configured 70 threshold. Exact licence bytes,
source lines, fresh local test output and hosted CI support the four ACs.
The final handoff is conditional on green CI for the published evidence commit.
Merge belongs to the Reviewer lane and its merge gate.

## Codex QA refresh, 2 November 2026

Verified saved merge `d42eb6d` by its full HEAD in git; the issue files and
application tree match published `7ae7b39ecdb64d33a6b53330078d17df39c9a5df`.
Current staging is `1659d50`; its only additional change fixes GitHub-read usage handling.
Fresh checks: exact Apache bytes, actionlint, 14 tests with Python 3.14.6,
and 14 tests using the exact configured command with Python 3.15.2 all pass.
CI at published `7ae7b39` passed for pull_request run 41375060301 and push run
41375055941. The handoff records CI for this refreshed evidence commit.
AC2 policy review confirms private reporting, disabled-button fallback, synthetic
examples, no live payloads and local-mock-only scope at SECURITY.md:5-27.
Inline independent review: Standards 0, Spec 0; no prior reviewer findings.
Truth confidence remains 98/100; test-gap ledger above still applies.
Screenshots intentionally omitted: no UI or visual acceptance criteria.
