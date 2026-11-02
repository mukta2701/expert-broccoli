# Plan: showpiece ready for 3 November

Owner goal: a finished, public-ready portfolio repo by 3 Nov that shows AI security skill to hiring managers who find it later. No live meeting or presentation is planned; the repo itself is the deliverable.
Direction: **evidence examples for review by security and governance readers**. These examples do not establish regulatory compliance.
Planned real-model target: a locally hosted model. No paid API calls, no spend. A local-model adapter and recorded model runs are still required; the current runner supports only the mock.
The labelled mock is a deterministic pipeline fixture for regression checks, not evidence of real-model security.
Working title: *Assurance Ledger* (rename freely).

## The one idea that makes it non-generic

Scanners report "attack success rate". Buyers and auditors need to know three other things:

1. **Did the attack actually work?** Prove it with a harmless canary token, not a refusal-phrase guess.
2. **How much damage could it do?** NCSC's position is that prompt injection may never be fully prevented,
   so the question is blast radius: what tools, data and egress the injected model can reach.
3. **Can I trust the scorer?** Measure it against human-labelled responses (precision, recall) and publish the number.

Then map every result to the controls an auditor asks about, and print a risk register. That chain is the product:

`attack -> canary result -> blast radius -> residual risk -> control crosswalk -> risk register -> evidence pack`

## Honest limits (state these in the README)

- Current results come from the labelled mock fixture. They exercise the pipeline, not real-model safety. Planned real-model results must name the local model, configuration and run manifest, and be reported separately.
- Framework mappings are indicative and need legal/compliance review. Testing does not certify compliance.
- UK market facts in `uk_market_analysis.md` are second-hand; verify before quoting.
- Clean-room: no employer code, prompts, logs or findings. Confirm your IP/approval position before publishing.

## Deliverables (all must exist and pass checks by 3 Nov morning)

| # | Deliverable | Owner | Done when |
|---|---|---|---|
| D1 | Attack cases moved to `data/cases.json` (id, family, severity, likelihood, impact, canary, blast_radius, expected_behaviour) | engine | Runner loads data file; old 16 cases preserved |
| D2 | Canary-based scorer using each case's own expectation; old substring scorer kept as baseline | engine | Unit tests cover PASS, PARTIAL, FAIL, and scorer disagreement |
| D3 | Blast-radius field and exposure-adjusted residual risk | engine | Documented formula; tests; shown in output |
| D4 | Run manifest: tool version, case-file hash, scorer version, seed, mode, timestamp | engine | Written beside every results file; same inputs give same hashes |
| D5 | Scorer validation: 40+ synthetic labelled responses, precision/recall per outcome | engine | `python -m tester.validate_scorer` prints a table; labelled synthetic |
| D6 | Evidence report generator: single-file HTML (summary, risk register, per-finding evidence, crosswalk, limits) plus Markdown | engine | `report` command produces both from a results file; opens offline |
| D7 | `data/framework_crosswalk.json` mapping each attack family to OWASP LLM 2025, MITRE ATLAS, ISO 42001/27001, NCSC, DSIT Code | content | Schema below; each entry flagged `verified: false` unless a primary page was opened |
| D8 | README rewrite, short reader walkthrough, one-page summary, CV/LinkedIn project blurb | content | Claims match what the code does; limits stated |
| D9 | LICENSE (Apache-2.0), SECURITY.md, CI workflow running tests | engine | CI file lints; tests exit 0 locally |
| D10 | Fresh independent review of code and of the report's design | reviewers | Findings fixed and rechecked |

### Crosswalk schema (shared contract between workers)

```json
{ "schema_version": 1,
  "entries": [ { "family": "RAG injection",
      "owasp_llm_2025": ["LLM01"], "mitre_atlas": ["AML.T0051"],
      "iso_42001": [], "iso_27001": [],
      "uk": [ { "source": "NCSC", "ref": "...", "note": "..." } ],
      "verified": false } ] }
```

`family` strings must match the 16 existing families exactly (see `data/cases.json`).

`verified: true` records that the cited primary source was seen. It does not mean the family-to-control mapping passed independent or compliance review.

## Schedule

- **Sun 1 Nov (today):** D1-D4 and D7 built in parallel. Plan reviewed.
- **Mon 2 Nov:** D5, D6, D8, D9. Independent review. Fix findings. Record demo run.
- **Tue 3 Nov, morning:** freeze, run every command in the README from a clean clone, last read of the limits. No new features.

If time runs short, cut in this order: D9 CI, D5 validation depth, HTML polish. Never cut D2, D3, D4, D6, or the limits.

## Reader walkthrough (optional 3-minute script, for the README or a screen recording)

1. Problem in one sentence (NCSC: injection may never be fully fixed, so measure blast radius).
2. Show the planned local-model run with its model ID and configuration when available. Show `safe` vs `unsafe` mock runs separately as labelled fixtures. Until the adapter and model run exist, show only the fixture and state the gap.
3. Open the HTML evidence pack: one finding, its canary proof, blast radius, control mapping, register entry.
4. Show the scorer validation table and the stated limits.
5. Roadmap: finish the local-model adapter and measured runs, then indirect/RAG scenarios and proposed comparisons with Garak/PyRIT/Promptfoo.

## Worker routing and spend

Included subscription usage only. Engineering: Codex (shows GPT-6.1-Sol). Content: Claude on Sonnet 5.5, because Fable 5.1
needs credits the account lacks. Design review: a fresh reviewer; if Fable is unavailable, say so and use the next eligible model.
