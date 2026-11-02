# Current prototype vs real product

Scope: a product sketch grounded in README, mock_app, tester, and all five reports.
Everything under "Real product" is proposed. Wireframe commands and numbers are illustrative.

## How it works today

```text
Public research -> sanitized prompt documents / coverage matrices
                   (reference material, not loaded by the runner)

CLI: python3 tester/test_runner.py --mode safe|unsafe --output results.json
                              |
                              v
tester/scoring_criteria.py: 16 hard-coded TEST_CASES, PI-01..PI-16
                              |
                              v
tester/test_runner.py -> mock_app/mock_chatbot.chat(prompt, mode)
                              |
                   ordered keyword categorization
                              |
                 +------------+-------------+
                 |                          |
            safe mode                  unsafe mode
         canned refusal           canned bypass/leak/action text
                 +------------+-------------+
                              |
                substring scoring: PASS / PARTIAL / FAIL
                              |
       effectiveness = 1 / 0.5 / 0; residual = L x I x (1 - effectiveness)
                              |
                 per-test JSON + console summary

playground.py -> same chat() function, interactive terminal
reports/*.md -> static findings, risk register, coverage, mitigations, exec summary
                (not generated or refreshed by test_runner.py)
```

- Verified baseline: safe 16 PASS, mean residual 0.0; unsafe 16 FAIL, mean 17.69.
- No model/API calls, retrieval pipeline, persistent conversation state, or executed tools.
- Multi-turn, RAG, encoding, flooding, and delayed-action cases are single-prompt simulations.
- `expected` is recorded, but the scorer checks shared substrings rather than each expectation.
- A mock PASS and calculated zero residual risk do not establish real-world safety.

## Real product

```text
PR / deploy / schedule / dashboard
              |
              v
Run manifest: target revision + corpus tag/hash + scoring/gate policy versions
              |
Versioned attack corpus -> isolated execution workers -> target adapters
  IDs, provenance,          budgets, retries, timeouts     | OpenAI / Anthropic APIs
  expected behavior,        sessions, fixture resets      | Azure / AWS Bedrock APIs
  multi-turn scripts,                                     | RAG application endpoints
  RAG/tool fixtures                                       | agents with sandboxed tools
                                                         v
                              responses + retrieval/memory/tool-action traces
                                                         |
                                  rule checks + isolated LLM judge + review
                                                         |
                                   immutable run/evidence store + mappings
                                                         |
                        +------------------+-------------+----------------+
                        v                  v                              v
                   CI/CD gate       HTML/PDF audit pack          regression dashboard
                   allow/block      evidence + remediation       baseline vs candidate
```

- Adapters normalize messages, streaming, tool calls, model/deployment IDs, and API errors.
- Exercise actual RAG ingestion/retrieval, session memory, tool authorization, and observed effects.
- Use scoped credentials, target allowlists, synthetic canaries, isolated tool fixtures, and cost limits.
- Corpus releases pin attack IDs, sources/licenses, variants, channel, severity, and expected assertions.
- Rules detect canary leakage and unauthorized actions. A pinned LLM judge applies a versioned rubric
  to task-specific outcomes and benign controls; refusal wording alone cannot establish a PASS.
- Treat target output as untrusted judge input; isolate it from judge instructions and tool access.
  Calibrate against human labels; retain rationale, confidence, disagreements, and reviewer decisions.
- Gate example: block High/Critical failures, any new regression, incomplete runs, and unresolved
  scoring uncertainty. Use exit 0 for pass, 1 for policy failure, 2 for execution/scoring errors.
  Record every exception with an owner, justification, approval, and expiry. PR smoke + nightly full suite.
- Trend attack success, leakage, unauthorized actions, benign-task success, cost, and latency by family.
  Compare matched corpus/judge/config versions with repeated trials and uncertainty; flag version drift.
- Auditor-ready HTML/PDF packs include scope/exclusions, methodology, manifest, coverage gaps,
  redacted transcripts and tool traces, evidence IDs/hashes, findings, owners, retests, and sign-off.
  Keep restricted originals under access controls and retention rules; link findings to immutable evidence.

## Proposed framework mapping

Each mapping stores the framework edition/revision, clause or technique ID, applicability, rationale,
test/evidence IDs, owner, reviewer, and coverage state. Show untested and not-applicable entries explicitly.
These are proposed evidence crosswalks; testing alone does not establish certification or legal compliance.

| Framework / official source | Proposed mapping and evidence |
|---|---|
| [OWASP LLM Top 10, 2025](https://genai.owasp.org/llm-top-10/) | PI -> LLM01; disclosure -> LLM02; tool abuse -> LLM06; prompt leakage -> LLM07; retrieval weaknesses -> LLM08 where applicable. Mark remaining categories as gaps until tested. |
| [MITRE ATLAS](https://atlas.mitre.org/) | Map attack steps to versioned techniques, including LLM prompt injection; attach execution traces and demonstrated outcomes. |
| [ISO/IEC 42001:2023](https://www.iso.org/standard/42001) | Support AIMS risk assessment/treatment, evaluation, and improvement evidence; validate clause/control mappings against the licensed standard. |
| [ISO/IEC 27001:2022](https://www.iso.org/standard/27001) | Support ISMS risk treatment, access control, logging, and secure development evidence; validate control IDs and Statement of Applicability. |
| [EU AI Act, Regulation 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj/eng) | For applicable high-risk systems, support Article 9 risk-management/testing, Article 12 record-keeping, and Article 15 robustness/cybersecurity evidence. Record role, classification, applicable dates, and legal review. |
| [UK NCSC guidelines](https://www.ncsc.gov.uk/collection/guidelines-secure-ai-system-development) + [DSIT AI Cyber Security Code](https://www.gov.uk/government/publications/ai-cyber-security-code-of-practice) | Cross-reference secure lifecycle guidance with threat models, security tests, release decisions, monitoring, and remediation evidence. |

## CLI and dashboard wireframe

```text
$ aisec run --target staging-rag --corpus pi@1.2.0 --baseline run-041 \
    --policy release@3 --report html,pdf --ci
Run 042 | 200 cases | PASS 190 | PARTIAL 6 | FAIL 4 | ERROR 0
New regressions: 2 | High/Critical failures: 1 | Gate: BLOCK | exit 1
Evidence: run-042/manifest.json | Report: run-042/report.html / report.pdf

+------------------------------------------------------------------------+
| AI security | Targets | Corpus | Runs | Findings | Mappings | Reports     |
| Target [staging-rag v18] Corpus [pi@1.2.0] Baseline [041]  [Run suite]    |
| Gate BLOCK | 2 new regressions | 1 High/Critical failure | [HTML] [PDF]   |
| Attack success, matched runs: 038 1% -> 039 1% -> 040 0% -> 042 2%       |
| Family         Coverage   Fail   Change    Owner       Evidence          |
| RAG injection  40/40      3      +2        App team    [Trace] [Retest]  |
| Tool abuse     20/20      1       0        Agent team  [Trace] [Retest]  |
| Finding -> prompt/retrieval/tool trace -> rule/judge -> mappings -> fix   |
| Coverage [OWASP] [ATLAS] [ISO 42001/27001] [EU] [UK]   [Review exception] |
+------------------------------------------------------------------------+
```

## Prioritised gaps

| Order | Gap today | Next deliverable / completion evidence |
|---|---|---|
| P0.1 | Only a deterministic mock target | Adapter contract + OpenAI/Anthropic/Azure/Bedrock connectors; recorded contract checks and staging runs. |
| P0.2 | RAG, state, and tools exist as response text | Real app/agent adapters; isolated multi-turn/RAG/tool fixtures with trace and side-effect assertions. |
| P0.3 | Substring scoring ignores per-case expectations | Rule + LLM-judge scoring with human calibration, benign controls, and explicit uncertainty/error states. |
| P1.1 | Corpus embedded in Python; no release manifest | Versioned corpus/schema, provenance, fixtures, hashes, and reproducible run manifests. |
| P1.2 | Local CLI has no release decision | CI integration, pinned thresholds/baselines, blocking exit codes, and expiring reviewed exceptions. |
| P1.3 | Static Markdown and broad governance themes | Reviewed framework crosswalks and evidence-linked HTML/PDF generation with redaction and access controls. |
| P2.1 | No stored history or comparison UI | Run database + dashboard; matched-version regression trends, repeated trials, and verified fix retests. |
