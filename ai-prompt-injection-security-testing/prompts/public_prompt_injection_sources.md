# Public Prompt-Injection Sources Used

This portfolio references public prompt-injection resources for defensive testing design.

## Scope Notes

- Sources are public.
- Payloads are sanitized before use in this repository.
- No private or employer-origin payloads are included.
- No testing is performed against unauthorized real systems.

## Model/Platform Targets Considered in Threat Modeling

- ChatGPT (OpenAI)
- Gemini (Google)
- Claude (Anthropic)
- Le Chat (Mistral)

## Public Tools and Datasets Referenced

- `TakSec/Prompt-Injection-Everywhere` (public payload corpus)
- `NVIDIA/garak` (LLM vulnerability scanner)
- `promptfoo/promptfoo` (prompt and agent security testing)
- `praetorian-inc/augustus` (adversarial probe framework)
- `praetorian-inc/julius` (LLM service fingerprinting for exposure discovery)
- Public jailbreak collections/challenge sets used as taxonomy inputs
- Prompt injection challenge labs (for learning signal only):
  - Gandalf (Lakera)
  - Prompt Airlines (Wiz)

## How These Sources Were Used Here

1. Build a category-based test taxonomy.
2. Convert unsafe payload patterns into safe synthetic prompts.
3. Map test categories to OWASP LLM risk themes.
4. Score control behavior using a residual-risk model for audit/GRC reporting.
