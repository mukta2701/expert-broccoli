> Edit before use: facts about you (role, dates, employer) are deliberately left out.

## CV entry (3 lines)

- Prompt-injection evidence pipeline: Python harness that runs 16 synthetic injection cases and produces a risk register and HTML evidence pack.
- Shows canary-based scoring, measured scorer precision and recall, and repeated trials with confidence intervals; built with AI coding agents under my direction.
- Limit: validated on a mock and one local 3B model; the scorer labels are AI-written, so it is not a safety verdict.

One-line alternative: Prompt-injection evidence pipeline (Python, synthetic cases, canary scoring); mock-validated, first local-model run inconclusive.

## LinkedIn description

A small Python project that runs 16 synthetic prompt-injection cases against a chatbot and turns the results into reviewable evidence: canary-based pass/fail, a risk register and an HTML evidence pack. It publishes its own scorer precision and recall, including weak spots. A first run on a local llama3.2:3b model showed 0 of 80 attack successes, which is not evidence the model resisted, because the scorer fits the mock's wording and the canary was never in the model's context. Built with AI coding agents under my direction. Not a safety verdict or certification.
