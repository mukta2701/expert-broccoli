# Security policy

## Reporting a vulnerability

Report repository vulnerabilities privately through
[GitHub Security Advisories](https://github.com/mukta2701/expert-broccoli/security/advisories).
Choose **Report a vulnerability** and include the affected commit, impact, and
minimal reproduction steps using synthetic data and the local mock only.

If that button is unavailable, open an issue asking the maintainer to enable
private vulnerability reporting. Do not include vulnerability details in that
public issue. Wait for a private advisory before sharing the report.

Do not post exploit details in public issues or pull requests. Never submit live
exploit payloads, credentials, employer material, private prompts, or confidential
logs, even in a private report. Use sanitised examples and harmless canaries.

## Authorised use

Only the local mock chatbot in `ai-prompt-injection-security-testing/mock_app/`
may be tested with this repository's tooling. Do not target production services,
employer systems, or any real or third-party system. This repository grants no
authorisation to test those systems.

All examples and evidence must remain synthetic. See the project's
[disclaimer](ai-prompt-injection-security-testing/DISCLAIMER.md) for the content
and usage boundaries.
