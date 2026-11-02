# Crosswalk sources (D7)

Checked 2026-11-01. Companion to `data/framework_crosswalk.json`.

Method: OWASP, NCSC and GOV.UK pages were fetched and read as text. The MITRE ATLAS site renders in JavaScript and returned only a stub (or 404) to plain fetches, so it was opened in a real browser and technique IDs and titles were read from the rendered pages.

Mappings are indicative and need legal/compliance review. A page being opened confirms the ID, title and stated content. It does not mean the source endorses the mapping to a given attack family.

## OWASP Top 10 for LLM Applications 2025 (genai.owasp.org)

All opened and loaded.

| URL | Confirmed |
|---|---|
| https://genai.owasp.org/llmrisk/llm01-prompt-injection/ | ID/title `LLM01:2025 Prompt Injection`. Covers direct and indirect injection, jailbreaking, multimodal injection. RAG scenario, Base64/emoji obfuscation scenario, least-privilege and human-approval mitigations. No mention of persistence/memory. |
| https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/ | `LLM02:2025 Sensitive Information Disclosure`. Notes system-prompt restrictions can be bypassed by injection. |
| https://genai.owasp.org/llmrisk/llm042025-data-and-model-poisoning/ | `LLM04:2025 Data and Model Poisoning`. Opened, not mapped to any family. |
| https://genai.owasp.org/llmrisk/llm052025-improper-output-handling/ | `LLM05:2025 Improper Output Handling`. Scenario: website summariser with injected prompt. |
| https://genai.owasp.org/llmrisk/llm062025-excessive-agency/ | `LLM06:2025 Excessive Agency`. Excessive functionality, permissions, autonomy in tools/extensions. |
| https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/ | `LLM07:2025 System Prompt Leakage`. System prompt is not a secret or a security control. |
| https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/ | `LLM08:2025 Vector and Embedding Weaknesses`. Scenario: hidden instruction in a document ingested into a RAG store. |
| https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/ | `LLM10:2025 Unbounded Consumption`. Opened to rule out "context flooding"; it is about resource exhaustion, so not mapped. |

Not checked: OWASP has announced a 2026 list (seen only in a search result title).

## MITRE ATLAS (atlas.mitre.org)

Homepage matrix and technique pages rendered in a browser. IDs and titles below were read from the site; page descriptions were read only where noted.

| ID | Title as shown | Notes |
|---|---|---|
| AML.T0051 | LLM Prompt Injection | Sub-techniques seen: AML.T0051.000 Direct, AML.T0051.001 Indirect, AML.T0051.002 Triggered. Description and mitigations read (mitigation AML.M0008 covers testing instruction/data boundaries). |
| AML.T0054 | LLM Jailbreak | Page opened. Its mitigations mention multi-turn, multilingual, encoded and multimodal jailbreak testing. |
| AML.T0053 | AI Agent Tool Invocation | Page opened; title confirmed. |
| AML.T0069 / AML.T0069.002 | Discover LLM System Information / System Prompt | Sub-techniques seen: .000 Special Character Sets, .001 System Instruction Keywords, .002 System Prompt. |
| AML.T0068 | LLM Prompt Obfuscation | Page opened; title confirmed. |
| AML.T0066 | Retrieval Content Crafting | Page opened; title confirmed. |
| AML.T0070 | RAG Poisoning | Seen in the matrix listing. |
| AML.T0093 | Prompt Infiltration via Public-Facing Application | Page opened; title confirmed. Description text not captured. |
| AML.T0086 | Exfiltration via AI Agent Tool Invocation | Page opened; title confirmed. Description text not captured. |
| AML.T0080 | AI Agent Context Poisoning | Page opened; title confirmed. Description not captured. Used only as a candidate. |

Also seen in the matrix but not mapped: AML.T0073 Impersonation (description not read), AML.T0143 LLM Prompt Propagation, AML.T0071 False RAG Entry Injection, AML.T0085 Data from AI Services, AML.T0110/T0099 AI agent tool poisoning.

Not found: `AML.T0056` "LLM Meta Prompt Extraction". It appears in a MITRE SAFE-AI PDF snippet from a search result, but not in the current technique list, so it was not used. `AML.T0069.002` is used instead.

The `/techniques/<ID>` URLs return HTML in a browser. Plain fetchers returned 404 for the same URLs, so anyone re-checking should use a browser.

## UK sources

| URL | Confirmed |
|---|---|
| https://www.ncsc.gov.uk/blog-post/prompt-injection-is-not-sql-injection | Title "Prompt injection is not SQL injection (it may be worse)", published 8 Dec 2025. Says an LLM is inherently confusable; approach is to reduce risk and impact; an LLM's privileges drop to those of the party whose content it processes; tool access raises worst-case impact. |
| https://www.ncsc.gov.uk/collection/guidelines-secure-ai-system-development | "Guidelines for secure AI system development", 27 Nov 2023, v1.0. Landing page only: secure by default, security across the lifecycle. Does not discuss prompt injection. Detail pages not read; not cited in any entry. |
| https://www.ncsc.gov.uk/collection/machine-learning-principles | "Machine learning principles", 22 May 2024, v2.0. Introduction only; not cited in any entry. |
| https://www.gov.uk/government/publications/ai-cyber-security-code-of-practice/code-of-practice-for-the-cyber-security-of-ai | "Code of Practice for the Cyber Security of AI", published 31 Jan 2025, described as voluntary. 13 principles. Provisions use bare dotted numbers (e.g. 2.2, 6.3), no "Provision" prefix on the page; the JSON writes "Provision n.n" as a label. Provisions cited: 2.2 (withstand adversarial attacks and unexpected inputs), 2.6 (permissions as required, risk assessed), 5.4.1 (checks and sanitisation of inputs), 6.3 (least privilege), 12.1 (log system and user actions). Prompt injection is named only in the introduction ("indirect prompt injection"), not in a numbered provision. |
| https://www.gov.uk/government/publications/ai-cyber-security-code-of-practice | Landing page, "AI Cyber Security Code of Practice". Does not itself say "voluntary"; the child page does. |

## Not opened (and therefore not used)

- ISO/IEC 42001 and ISO/IEC 27001 clause text (paywalled; iso.org pages not opened). The JSON leaves `iso_42001` and `iso_27001` empty and gives unverified theme names in `iso_themes_42001` / `iso_themes_27001`. No clause or Annex A numbers were written.
- NCSC "Guidelines for secure AI system development" detail pages and the ML principles detail pages.
