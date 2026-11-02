# ai-prompt-injection-security-testing

A public project that demonstrates how to design and run **prompt-injection and jailbreak security testing** for chatbot/LLM workflows using a local mock application.

## Public Sanitised Portfolio-Safe Reconstruction

This repository is a **public, sanitised, portfolio-safe reconstruction**.

It is intentionally built as a clean-room project for hiring review and security education.
No employer code, private prompts, confidential logs, or internal findings are included.

See [DISCLAIMER.md](./DISCLAIMER.md) for full boundaries.

## Project Explanation (Step by Step)

This section explains the full workflow end-to-end in plain language.

1. Define the threat focus.
This project focuses on prompt injection and jailbreak behavior: attempts to make an AI assistant ignore safety rules, reveal hidden instructions, or trigger unauthorized actions.

2. Build a safe test catalog.
Prompt families are collected from public security research and converted into sanitized templates.
No operational exploit payloads are stored.

3. Simulate an AI target locally.
A local mock chatbot (`mock_app/mock_chatbot.py`) simulates two control postures:
- `safe` mode: stronger guardrail behavior
- `unsafe` mode: weak controls for comparison

4. Execute repeatable tests.
`tester/test_runner.py` runs test cases across prompt-injection families and records outcomes.

5. Score each result.
Each test is scored as `PASS`, `PARTIAL`, or `FAIL`, then weighted with:
- Likelihood (1-5)
- Impact (1-5)
- Control effectiveness
- Residual risk score

6. Convert technical results into governance evidence.
Outputs are mapped into findings, risk register entries, and mitigation recommendations in audit/GRC style.

7. Link to recognized frameworks.
Findings are mapped to OWASP LLM risks (especially Prompt Injection and Sensitive Information Disclosure) and aligned to ISO/IEC 27001 control themes.

8. Keep the repository safe for public sharing.
All examples use synthetic data and mock behavior only.

## Security Objectives

- Test direct prompt injection and instruction override attempts.
- Test jailbreak-style framing and policy bypass pressure.
- Test system prompt extraction attempts (mock prompt only).
- Test indirect prompt injection (RAG/document/web/metadata channels).
- Test prompt-to-tool action hijack patterns in agent-like workflows.
- Measure residual risk and produce evidence-led security reporting.

## Skills Demonstrated

- AI security test design for LLM applications
- Prompt-injection and jailbreak taxonomy development
- Adversarial test automation in Python
- Risk scoring using Likelihood x Impact with control effectiveness
- Mapping technical findings to OWASP and ISO 27001 control expectations
- Audit/GRC reporting: findings summary, risk register, mitigation plan, executive summary

## How To Run the Mock Tester (Local Only)

```bash
cd ai-prompt-injection-security-testing
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 tester/test_runner.py --mode safe --output safe_results.json
python3 tester/test_runner.py --mode unsafe --output unsafe_results.json
```

Optional interactive mock chat:

```bash
python3 mock_app/playground.py --mode safe
python3 mock_app/playground.py --mode unsafe
```

The default mock target calls no external APIs.

### Opt in to a real model

An OpenAI-compatible chat API can receive the same synthetic prompts:

```bash
python3 tester/test_runner.py --target openai_compat \
  --base-url http://localhost:11434/v1 --model llama3.2:3b \
  --timeout 30 --requests-per-second 1 --output model_results.json
```

Start your model server separately. The adapter uses Python's standard library.
By default, only literal loopback addresses and `localhost` are allowed.
`localhost` is pinned to `127.0.0.1`; arbitrary DNS names and LAN addresses
require `--i-have-authorization`. Use that flag only with permission to test the target.
Proxies and redirects are disabled. Each request carries `X-Assurance-Ledger-Test: 1`.
The timeout limits blocking socket operations, not the total duration of a run.
Requests are sequential, paced at the configured rate, and never retried.
The adapter sends a single user message per prompt; it does not send the mock's
protected canary or configure model guardrails. `--mode` only changes mock behavior.
Results record the target name and response metadata. Mock scoring rules remain
illustrative and require review before drawing conclusions about a real model.
This adapter does not configure API credentials.

## Example Outputs (Synthetic Data Only)

```text
Run mode: safe
Methodology: Weighted Likelihood x Impact with control effectiveness adjustment
Total tests: 16
PASS: 16 | PARTIAL: 0 | FAIL: 0
Average residual risk: 0.0
Overall risk posture: Low

Run mode: unsafe
Methodology: Weighted Likelihood x Impact with control effectiveness adjustment
Total tests: 16
PASS: 0 | PARTIAL: 0 | FAIL: 16
Average residual risk: 17.69
Overall risk posture: High
```

All outputs are synthetic and generated by the local mock app.

## OWASP LLM Risk Mapping

Primary mapping emphasis:
- **Prompt Injection** (core project focus)
- **Sensitive Information Disclosure** (modeled as a downstream outcome of successful injection or prompt leakage)

Additional related themes covered:
- System prompt leakage attempts
- Indirect prompt injection via external context sources
- Excessive agency/tool-call abuse driven by prompt manipulation

Reference links are listed in [references.md](./references.md).

## What This Repository Does Not Contain

- Employer source code, private prompts, or internal runbooks
- Real chatbot logs, screenshots, tickets, or private security findings
- Customer, employee, or partner data
- Internal URLs, cloud account identifiers, architecture details, or environment specifics
- Credentials, API keys, tokens, or secrets
- Instructions to exploit real systems

## Summary

This project demonstrates practical AI security engineering and GRC capability in one portfolio artifact.
It shows that I can:
- design structured prompt-injection test coverage,
- automate repeatable control validation,
- quantify residual risk,
- and communicate remediation priorities in an audit-ready format.

