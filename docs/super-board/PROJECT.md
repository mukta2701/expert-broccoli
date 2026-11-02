# expert-broccoli

Public, sanitised portfolio repo. One project: `ai-prompt-injection-security-testing/`, a clean-room demo of prompt-injection and jailbreak testing against a local mock chatbot.

| Thing | Value |
|---|---|
| Language | Python 3, stdlib only (no dependencies) |
| Layout | `mock_app/` mock chatbot · `tester/` runner, scoring, results schema · `prompts/` · `data/` · `tests/` · `docs/` · `reports/` · `evidence/` |
| Tests | `cd ai-prompt-injection-security-testing && python3 -m unittest discover -s tests -t .` (14 tests, offline) |
| Base branch | `staging` |

## Boundaries

- NEVER add employer code, private prompts, confidential logs or internal findings. See `ai-prompt-injection-security-testing/DISCLAIMER.md`.
- NEVER point the tester at a real or third-party system. It targets the local mock app only.
- NEVER add third-party dependencies without asking.
