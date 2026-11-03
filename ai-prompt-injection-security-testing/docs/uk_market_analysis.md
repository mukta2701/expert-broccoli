# UK Market Analysis: AI Security, LLM Red-Teaming, AI Assurance and GRC

Researched: 2026-11-01. Method: web search only (secondary sources). Primary documents
(gov.uk, FCA, PRA, ICO, NCSC, EUR-Lex, Parliament) were NOT opened directly.
Every claim carries a confidence tag: [V] corroborated by 2+ sources, [S] single or
secondary source, [U] could not verify.

## 1. Bottom line

- Demand is real but young. Regulation is mostly guidance and existing rules, not
  AI-specific UK law. Buyers are paying for governance, assurance and evidence first,
  and technical red-teaming second.
- The tool market has consolidated. Lakera and Promptfoo now sit inside Check Point and
  OpenAI. Mindgard (UK) is well funded. Open-source scanners remain the free baseline.
- The most defensible gap for a portfolio project is not "another scanner". It is
  evidence: mapping test results to UK/EU controls in a form an auditor or GRC lead can use.

## 2. Job volumes and salaries

### Volumes
- I could NOT obtain reliable posting counts for "AI security", "LLM red team" or
  "AI assurance" on Reed, Indeed UK, LinkedIn or CWJobs. Job boards were not queryable. [U]
- One career guide cites 79 live AI Assurance postings on AI-Governance-Jobs.com, 37 with
  a published salary range. I could not see the underlying figures. [U]
  https://www.ai-governance-jobs.com/ai-governance-career-guides/how-to-get-an-ai-assurance-job/
- Check live counts yourself before quoting any number.

### Advertised salary ranges (individual postings and aggregators, not surveys) [S]

| Role type | Range (GBP) | Source |
|---|---|---|
| AI Security Engineer, London, cloud security focus | 75k-95k base | https://www.itjobswatch.co.uk/jv/Huxley-Associates/AI-Security-Engineer-security-engineering-cloud-security-Job-City-of-London-London-UK-4xrm8o |
| AI Security Engineer, GenAI, central London | 70k-100k | https://grabjobs.co.uk/uk/job/full-time/others/ai-security-engineer-154111115 (listed URL pattern; aggregator) |
| Cyber Security AI Specialist (aggregator estimate) | 60k-107.5k | https://www.jobijoba.co.uk/detail/92/730a9e997415e5f596aca8883befd5aa |
| AISI Research Engineer, Red Team | 65k-145k (one board) | https://builtinlondon.uk/job/research-engineer-research-scientist-red-team-misuse/8732558 |
| AI Assurance Specialist, London | 40k-50k | https://www.itjobswatch.co.uk/jv/Robert-Half/AI-Assurance-specialist-Job-London-South-East-England-UK-4tqxgj |
| AI Assurance Specialist, London/Portsmouth | 50k-65k | https://www.itjobswatch.co.uk/jv/83zero/Assurance-Specialist-Job-Guildford-Surrey-UK-4wzvmw |
| AI Governance Lead (QA career guide average) | 57k-100k | https://www.qa.com/browse/job-roles/ai-governance-lead/ |
| Risk and AI Governance Consultant, remote | 75k-90k | https://www.itjobswatch.co.uk/jv/LUMORA-SOLUTIONS/AI-Governance-Consultant-Job-London-South-East-England-UK-4ya1e9 |
| DWP Lead Tech Delivery Manager, AI Assurance, Manchester | ~76k | https://findajob.dwp.gov.uk/details/17969886 |

Reading: technical AI security roles cluster around 70k-100k in London, with a long
upper tail at AISI and frontier labs. Assurance and GRC roles sit lower at the
specialist level (40k-65k) and rise to 75k+ at consultant and lead level.
Caveats: the aggregator numbers marked "estimate" are modelled, not offered. US-dollar
red-team figures in search results were excluded. Taylor Root's 2026-27 guide exists
but I could not read its numbers: https://www.taylorroot.com/report/uk-risk-compliance-and-governance-salary-guide/ [U]

### Market size (government)
- DSIT 2024 report: 524 UK firms supplying AI assurance (84 specialist, 225 developers,
  182 diversified, 33 in-house), ~GBP 1.01bn GVA, ~12,572 staff, projected GBP 6.53bn
  by 2035. [S] https://www.gov.uk/government/publications/assuring-a-responsible-future-for-ai/assuring-a-responsible-future-for-ai
- DSIT Sept 2025 trusted third-party roadmap projects GBP 18.8bn by 2035. The two
  projections differ and I found no explanation. [S, conflict]
  https://www.burges-salmon.com/articles/102l5fo/trusted-third-party-ai-assurance-dsit-roadmap/

## 3. Demand drivers

### NCSC
- Dec 2025 guidance: prompt injection may never be fully mitigated because models do not
  separate data from instructions. Advice is to limit blast radius, not rely on filters. [S]
  https://securitybrief.co.uk/story/ncsc-warns-ai-prompt-injection-could-drive-huge-uk-data-breaches
- Implication: buyers need testing of impact containment (tool permissions, data access),
  not only jailbreak pass/fail rates. Confirm wording on ncsc.gov.uk. [U]

### DSIT AI Cyber Security Code of Practice
- Voluntary, Jan 2025, 13 principles across the AI lifecycle, with an implementation
  guide. [V] https://www.gov.uk/government/publications/ai-cyber-security-code-of-practice
- Became ETSI standard EN 304 223 (earlier called TS 104 223). Covers data poisoning,
  model manipulation and indirect prompt injection. [S]
  https://www.techuk.org/insights/news/etsi-sets-out-new-european-standard-to-strengthen-ai-cyber-security
- Adoption/enforcement status in UK procurement: not found. [U]

### AI Security Institute (AISI)
- Has tested 30+ frontier models; open-source Inspect evaluation framework; red team
  hiring in London. [S] https://www.aisi.gov.uk/blog/our-2025-year-in-review
  https://github.com/UKGovernmentBEIS/inspect_ai
- AISI sets a technical bar and a hiring signal, but it is a public research body, not a
  buyer of commercial testing services.
- Reported salaries up to 145k and budget figures conflict across sources. [U]

### EU AI Act (UK firms exporting)
- Extraterritorial: applies where UK firms place AI systems or outputs on the EU market. [S]
- Digital Omnibus agreement defers Annex III high-risk duties to 2 Dec 2027 and Annex I
  to 2 Aug 2028. Sources disagree on whether it is already in force. [S, conflict]
  https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines/
  https://www.grantthornton.co.uk/insights/the-eu-ai-act-what-uk-and-cross-border-general-counsel-need-to-know-now-the-high-risk-deadline-has-moved/
- GPAI, transparency and prohibited-practice duties are not covered by the delay. [S]
- Check the Official Journal before quoting dates. [U]

### ISO/IEC 42001
- Commentary links red-teaming to evidencing 42001 robustness controls. [S, vendor-heavy]
  https://www.compliancehub.wiki/compliance-with-iso-42001-leveraging-ai-red-teaming-for-enhanced-ai-governance
  https://arxiv.org/pdf/2602.21267
- UK certification volumes and demand data: not found. [U]

### FCA / PRA / ICO
- No AI-specific rules. Supervisors apply existing regimes: Consumer Duty, SM&CR,
  PRA SS1/23 model risk (banks using internal models). [V]
  https://www.covingtonblogs.com/2026/04/09/uk-financial-services-regulators-approach-to-artificial-intelligence-in-2026/
  https://tlt.com/insights-and-events/insight/the-bank-of-england-and-pra-set-out-plans-for-safe-ai-innovation-what-firms-need-to-know
- FCA Mills Review of AI in retail financial services launched 27 Jan 2026, report due
  summer 2026. Outcome not checked. [S/U]
- ICO statutory AI code reportedly announced around 1 June 2026. [U, single source]
- April 2026: regulators reportedly held urgent talks with banks and insurers on
  frontier-model cyber risk. [S] https://qa-financial.com/uk-finance-watchdogs-hold-emergency-talks-as-ai-testing-scrutiny-intensifies/

### Cyber Security and Resilience Bill
- Introduced 12 Nov 2025; Commons second reading 6 Jan 2026; passed Commons in June 2026
  (10 or 16 June, sources differ); now in Lords. Royal Assent not found. [S, conflict]
  https://digitalpolicyalert.org/event/43452-house-of-commons-passed-cyber-security-and-resilience-bill
- Updates NIS Regulations: adds data centres and managed service providers, 24-hour
  incident reporting. It is not AI-specific; it raises general cyber assurance demand. [S]
- Verify stage on bills.parliament.uk. [U]

### Other
- CREST added an optional AI-Enabled Penetration Testing annex (July 2026). It governs
  how testers use AI, not testing of AI systems. [S]
  https://itbrief.co.uk/story/crest-launches-ai-testing-standard-for-cyber-firms
- DSIT roadmap explores certification of assurance professionals and processes. [S]

## 4. Who buys

Evidence of named UK contracts for AI red-teaming is thin. [U] The below is inference.

| Buyer | Why they buy | Evidence |
|---|---|---|
| Banks, insurers, payments | SS1/23, Consumer Duty, SM&CR, EU exposure, regulator focus on AI cyber risk | Regulatory commentary [S]; vendor claim of move to multi-year red-team programmes [S, vendor] |
| Public sector | AI assurance roles (DWP, intelligence services); CREST/CHECK gates on testing suppliers | Job ads [S]; CHECK vs CREST scope claims conflict [U] |
| Consultancies and Big 4 | Resell assurance and ISO 42001 readiness; hire GRC and AI governance staff | Job listings [S] |
| SaaS and AI-native firms | Customer security questionnaires, EU AI Act, ISO 42001 as sales enabler | Inference [U] |
| Frontier labs and AISI | Research-grade red-teaming; hire not buy | AISI postings [S] |

CBEST / CREST STAR-FS intelligence-led testing exists for major financial firms. Whether
it now includes AI scope was not found. [U]

## 5. Competitors and tools

| Tool | Type | Notes |
|---|---|---|
| garak (NVIDIA) | Open source scanner | Broad static probe library; detailed reports; weaker CI polish; detector reliability issues |
| PyRIT (Microsoft) | Open source framework | Adaptive multi-turn attacks via attacker LLM; needs LLM access; less structured output |
| Promptfoo | OSS + commercial | OpenAI announced acquisition 9 Mar 2026; deal terms unverified |
| Lakera | Runtime guardrails and red team | Check Point acquisition announced Sept 2025, ~USD 300m reported [S] |
| HiddenLayer | Model supply-chain and runtime | Scans 35+ model formats for deserialisation and backdoors |
| Mindgard | UK platform, Lancaster spinout | ~USD 30m Series A reported, total ~42m; enterprise focus; sources differ on earlier rounds |
| Inspect (AISI) | Open-source eval framework | 200+ prebuilt evals; capability and safety focus |
| Giskard, CyberSecEval | Open source | Covered in academic comparison |

Sources:
- https://arxiv.org/abs/2410.16527 (peer-reviewed scanner comparison; main finding is weak
  reliability in detecting successful attacks across tools)
- https://qawerk.com/blog/llm-red-teaming-tools/
- https://www.bloomberg.com/news/articles/2026-03-09/openai-buying-ai-security-startup-promptfoo-to-safeguard-ai-agents
- https://www.securityweek.com/check-point-to-acquire-ai-security-firm-lakera/amp/
- https://itbrief.co.uk/story/mindgard-raises-usd-30-million-to-boost-ai-security
- https://www.superblocks.com/blog/generative-ai-security-tools

Pattern: standalone commercial testing is being absorbed into platforms. Remaining
independents compete on enterprise breadth. None of the sources show a tool aimed at
producing UK-regulator-shaped assurance evidence. [S, absence of evidence]

## 6. Gaps this project could fill

Assumption: the project is a sanitised prompt-injection test harness and portfolio piece.
I did not re-read its code for this analysis, so check each gap against what exists.

1. **Control mapping.** Map each test to NCSC guidance, DSIT Code principles / EN 304 223,
   ISO 42001 controls, and OWASP LLM Top 10. Output a traceability table. Scanners report
   probe pass rates; auditors want control evidence.
2. **Blast-radius testing.** NCSC says prevention will not be complete. Test what an
   injected agent can reach (tools, data, egress), not only whether it was jailbroken.
3. **Indirect and agentic injection.** EN 304 223 names indirect prompt injection.
   Garak is largely static; PyRIT needs more setup. Reproducible RAG/tool-use scenarios
   are a visible differentiator.
4. **Detector reliability.** The academic comparison found weak detection of successful
   attacks. Report precision against human-labelled results, with confidence intervals.
5. **Regulator-shaped reporting.** Short board-level output aligned to SS1/23 model-risk
   language, Consumer Duty and SM&CR accountability. No tool surfaced here does this. [S]
6. **Reproducibility and safety.** Pinned versions, fixed seeds, and sanitised payloads
   make results defensible for assurance use, and safe for a public portfolio.
7. **Credibility signals.** CREST and CHECK gate commercial testing sales. A portfolio
   project cannot replace them, but it can show methodology awareness and honest limits.

What it should not claim: parity with Mindgard, Lakera or Promptfoo on coverage, or that
it provides compliance. It evidences testing; it does not certify anything.

## 7. Could not verify (consolidated)

- Posting counts on UK job boards, and any 2026 salary survey figures.
- NCSC, FCA, PRA, ICO and EU texts read directly. All regulator claims are second-hand.
- Whether the EU Digital Omnibus on AI is legally in force.
- Current stage of the Cyber Security and Resilience Bill, and the Commons passage date.
- ICO statutory AI code announcement; FCA Mills Review outcome.
- Named UK buyers of AI red-teaming; UK ISO 42001 certification volumes.
- Promptfoo deal value (an USD 86m figure circulated); Lakera price beyond press reports.
- Why DSIT's two market projections differ (6.53bn vs 18.8bn).
- AISI salary and budget figures.
- Several results were vendor blogs or aggregators with commercial interest.
