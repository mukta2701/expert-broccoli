# Jailbreak and Prompt Injection Research Matrix (Defensive)

## Objective

Provide evidence-backed coverage for prompt-injection and jailbreak testing without distributing actionable bypass payloads.

## Coverage Matrix


| Family ID | Family Name                 | Direct/Indirect | Typical Target            | Primary Risk                  | Priority |
| --------- | --------------------------- | --------------- | ------------------------- | ----------------------------- | -------- |
| PI-01     | Instruction Override        | Direct          | Core chat                 | Policy bypass                 | Critical |
| PI-02     | System Prompt Extraction    | Direct          | Core chat                 | Confidential instruction leak | Critical |
| PI-03     | Authority Impersonation     | Direct          | Core chat                 | Unauthorized actions          | High     |
| PI-04     | Persona/Mode Hijack         | Direct          | Core chat                 | Guardrail bypass              | High     |
| PI-05     | Prompt Sandwiching          | Direct          | Core chat                 | Filter evasion                | High     |
| PI-06     | Hypothetical Framing        | Direct          | Core chat                 | Restricted output leakage     | High     |
| PI-07     | Multi-turn Persistence      | Direct          | Stateful chat             | Durable compromise            | High     |
| PI-08     | Context Flooding            | Direct          | Long-context apps         | Guardrail dilution            | Medium   |
| PI-09     | Encoded Payload             | Direct          | Core chat                 | Detector bypass               | High     |
| PI-10     | Unicode/Homoglyph           | Direct          | Core chat                 | Pattern bypass                | Medium   |
| PI-11     | Protocol/Role Spoof         | Direct          | Prompt wrappers           | Control-channel confusion     | Critical |
| PI-12     | Output Coercion             | Direct          | API/JSON outputs          | Structured leakage            | High     |
| PI-13     | Reflection/Echo Abuse       | Direct          | Debug/chat                | Payload replay                | Medium   |
| PI-14     | Reasoning Leak Pressure     | Direct          | Core chat                 | Internal policy leakage       | Medium   |
| PI-15     | Social Pressure Coercion    | Direct          | Support bots              | Safety degradation            | Medium   |
| PI-16     | RAG Document Injection      | Indirect        | RAG systems               | Remote instruction hijack     | Critical |
| PI-17     | Web/HTML Hidden Injection   | Indirect        | Browser agents            | Remote instruction hijack     | Critical |
| PI-18     | Metadata Injection          | Indirect        | File-ingest bots          | Hidden instruction execution  | High     |
| PI-19     | Tool-Call Hijack            | Direct+Agentic  | Agents with tools         | Unauthorized execution        | Critical |
| PI-20     | Cross-Tool Forgery          | Agentic         | Multi-plugin agents       | Data exfil/action pivot       | Critical |
| PI-21     | Second-Order Injection      | Indirect        | Memory workflows          | Delayed compromise            | High     |
| PI-22     | Transform Pivot             | Direct/Indirect | Translate/summarize flows | Safety bypass                 | Medium   |
| PI-23     | Benign Workflow Camouflage  | Indirect        | Enterprise assistants     | Low-visibility compromise     | High     |
| PI-24     | Multi-lingual Split Payload | Direct/Indirect | Global assistants         | Detection gaps                | Medium   |


## Evidence-Centered Test Method

1. Define one sanitized template per family.
2. Run in baseline and hardened modes.
3. Capture refusal quality, leakage indicators, and action-attempt indicators.
4. Score PASS/PARTIAL/FAIL and compute residual risk.
5. Map findings to OWASP LLM01 and control recommendations.

## What "Used in This Portfolio" Means

- Public prompt-injection families were reviewed and normalized.
- Unsafe payloads were converted into non-operational templates.
- Tests were executed against a mock chatbot only.

## Out-of-Scope

- Live bypass payload publishing
- Real-system exploitation instructions
- Employer/internal test artifacts

