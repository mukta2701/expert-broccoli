# Tripwire: prompt-injection evidence pipeline, one page

## Problem

A chatbot that follows instructions hidden in user input can leak data or misuse tools. Teams need more than a pass/fail label: what happened, how far it could reach, and whether the scorer deserves trust.

## Approach

A standard-library Python harness runs 16 hand-written synthetic prompt-injection cases. A harmless canary string and a per-case expected behaviour decide the outcome. Each case gets a blast-radius score, then the results become a Markdown risk register and an HTML evidence pack with an indicative framework mapping. It runs against a local mock by default, or a model you run yourself.

The repo was built with AI coding agents (Claude and Codex) under the owner's direction, with independent AI review at each step and the owner approving changes at gates.

## What the evidence shows

- Mock chatbot: safe mode scores 16 PASS, unsafe mode scores 16 FAIL. This shows the pipeline works.
- Scorer validation on 48 synthetic labelled replies: precision/recall is PASS 0.846/0.688, PARTIAL 0.696/1.000, FAIL 1.000/0.750. Weak spots: 5 of 16 reference PASS scored PARTIAL; 2 of 16 reference FAIL scored PASS.
- First real run (llama3.2:3b via Ollama, 16 cases, 5 trials): 0 of 80 attack successes. This is not a safety result. The scorer expects the mock's wording, so all 80 trials scored PARTIAL, and the canary was never in the model's context.
- Case study: a reply that opens with a refusal but contains the canary. The old substring scorer says PASS; the canary scorer catches it. The same leak with the canary respelled is missed by both scorers.

## What it does not show

- Nothing about whether any real model is safe. One 3B model, one machine, one temperature, no system prompt.
- Not real-world scorer accuracy: the reference labels were written by an AI, not independently labelled by humans.
- Risk scores are illustrative, not measured. The framework mapping is indicative and not a compliance verdict.
- No comparison with Garak, PyRIT or Promptfoo, and no attack coverage beyond 16 cases.

## Next steps

- Build a scorer for real-model replies and validate it on labelled real replies.
- Put the canary in the model's context so leakage can be measured.
- Test more models.
