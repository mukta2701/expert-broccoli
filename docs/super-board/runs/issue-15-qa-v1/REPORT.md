# Issue 15 QA, round 1

Result: PASS, all five acceptance criteria verified against builder head `2e94d2c3de9144b470b0bf5d23432c9c1735ba84` plus the QA tests in this commit.

## Acceptance evidence

Paths below are relative to `ai-prompt-injection-security-testing/`.

| AC | Unit assertion | Integration assertion | Browser |
|---|---|---|---|
| 1. Mock outcomes | `tests/test_engine.py:163`, 16 safe PASS and 16 unsafe FAIL | CLI/manifest regression at `tests/test_engine.py:196`; `contracts.log` records direct counts | n/a, command line |
| 2. Local HTTP transport | `tests/test_targets.py:147`, captured prompt/model/path, returned text/id | `tests/test_targets.py:176`, subprocess CLI completes 16 local HTTP requests | n/a, HTTP API |
| 3. Authorization | `tests/test_targets.py:76`, DNS aliases, integer addresses and remote IPv6 rejected | `tests/test_targets.py:167`, nonzero CLI exit, zero requests, no output | n/a, command line |
| 4. Header and timeout | `tests/test_targets.py:117`, stalled reply raises TimeoutError with marked request | `tests/test_targets.py:176`, all 16 CLI requests marked | n/a, HTTP API |
| 5. No dependencies | Import audit in `contracts.log`; requirements unchanged from base | All 38 tests pass under `python3 -S`, with site packages disabled | n/a, Python runtime |

## Test gaps and edge cases

Added high-risk guard coverage at `tests/test_targets.py:69`, `:76`, `:84`, and `:94`. It checks pinned localhost without DNS, literal IPv6 loopback configuration, seven denied address variants, all five HTTP redirect codes, Unicode prompt/reply transport, and exclusion of the synthetic protected canary from requests.

Each new test detected a temporary source mutation before the final green runs. `mutation-checks.log` records the four observed failures. The production source matches the builder commit. Existing tests also cover proxy isolation, all-request marking, pacing, invalid limits, null replies, and authorization opt-in configuration.

Test gaps (not written): Medium, no actual IPv6 socket integration or TLS handshake test. Low, no dedicated tests for malformed JSON/error status presentation or blank model names. The timeout is a socket timeout, as documented, rather than a deadline for the full run. UI states, ownership, money, dates, pagination, and concurrent requests are outside this sequential CLI adapter.

## Independent review and truth check

Inline Standards and Spec checks found no blocking defect. The implementation meets the five ACs with standard-library transport. Authorization is checked before opening a request; proxy lookup and redirects are disabled. The new tests assert captured requests and adapter output rather than their own mocks. A socket timeout and minimum sequential spacing match the documented controls.

Grounding: cited code and assertions were inspected locally. History: the issue branch contains one builder commit atop the configured staging base; no prior reviewer findings or human replies were present. Nine author-note threads had no replies, and both thread pagination checks were complete. Confidence: 95/100, above the configured 70 threshold. The remaining uncertainty is real model compatibility, which the ACs explicitly exercise through a fake server.

The privacy hook flagged two synthetic fake-server assertions. QA reviewed them inline, refreshed the existing moved assertion's fingerprint and added one exact exception for the fixed Unicode test string. Both retain automated attribution, issue #15, and expiry on 2026-11-16. No personal data, human approval claim, broad suppression, or hook bypass was added.

## Reproduction

From the repository root: `cd ai-prompt-injection-security-testing && python3 -m unittest discover -s tests -t .`.

Python 3.15.2 and Python 3.14 each pass 38 tests. `tests.log` contains the full verbose run and the second-interpreter result. `no-site-packages.log` records the 38-test run with `python3 -S`. `git diff --check` passes. No live model, remote service, migration, or merge was attempted. Screenshots are omitted because all ACs concern CLI or HTTP behavior.
