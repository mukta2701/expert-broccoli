# Risk Register (Prompt Injection Focus, Synthetic)

| Risk ID | Risk Description | Prompt Injection Family | OWASP LLM Risk Theme | ISO/IEC 27001:2022 Control Theme | Likelihood | Impact | Inherent Risk | Residual Risk (Unsafe Baseline) | Severity | Status |
|---|---|---|---|---|---:|---:|---:|---:|---|---|
| AIR-PI-001 | Model follows user override against policy hierarchy | Direct instruction override | Prompt Injection | Secure development, access control | 5 | 5 | 25 | 25 | Critical | Open |
| AIR-PI-002 | Hidden instructions disclosed by extraction prompts | System prompt extraction | Prompt Injection / Sensitive disclosure pathway | Data leakage prevention, monitoring | 4 | 5 | 20 | 20 | Critical | Open |
| AIR-PI-003 | Fake authority claims bypass policy checks | Authority impersonation | Prompt Injection | Access control and authorization | 4 | 4 | 16 | 16 | High | Open |
| AIR-PI-004 | Retrieved text overrides model safeguards | RAG/document/web indirect injection | Prompt Injection / Vector-context weakness | Input validation, monitoring | 4 | 5 | 20 | 20 | Critical | Open |
| AIR-PI-005 | File metadata instructions alter response behavior | Metadata injection | Prompt Injection | Data processing controls, secure ingestion | 4 | 4 | 16 | 16 | High | Open |
| AIR-PI-006 | Prompt content triggers unauthorized tool execution | Tool-call hijack | Excessive Agency | Least privilege, approval workflow | 5 | 5 | 25 | 25 | Critical | Open |
| AIR-PI-007 | Cross-tool instruction pivot leaks protected data | Cross-tool forgery | Excessive Agency / Prompt Injection | Segregation of duties, connector governance | 4 | 5 | 20 | 20 | Critical | Open |
| AIR-PI-008 | Delayed payload executes through memory/state reuse | Second-order injection | Prompt Injection | Change control, monitoring, secure state management | 4 | 4 | 16 | 16 | High | Open |
