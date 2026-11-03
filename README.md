# Tripwire

A personal test bench for prompt injection: it plants a harmless secret in a model's hidden instructions, attacks the model with 16 synthetic cases, and shows whether the secret leaks, with the exact replies as proof. Terminal-based, Python standard library only, built for local models.

The project lives in [`ai-prompt-injection-security-testing/`](ai-prompt-injection-security-testing/); start with its [README](ai-prompt-injection-security-testing/README.md), which also lists what the results do and do not show.

Security reports: see [SECURITY.md](SECURITY.md).
