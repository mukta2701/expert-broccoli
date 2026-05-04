# Mitigation Recommendations (Audit/GRC Prioritized)

## Priority 1: Mandatory Control Strengthening

1. Enforce strict instruction hierarchy (system > developer > user) with non-bypassable policy checks.
2. Implement output filtering for prompt leakage and sensitive-value patterns.
3. Enforce least-privilege tool access with explicit authorization and human approval for high-risk actions.
4. Apply retrieval filtering and context trust labels so RAG content cannot issue executable instructions.

## Priority 2: Monitoring and Assurance

5. Capture adversarial prompt telemetry, refusal events, and policy-bypass attempts.
6. Add alerting thresholds for repeated jailbreak/probing behavior.
7. Establish evidence retention standards for AI security test runs and control audits.

## Priority 3: Governance and Continuous Improvement

8. Run recurring red-team style test cycles with trend tracking.
9. Define risk acceptance criteria for unresolved residual risk.
10. Integrate AI control testing into ISMS review cadence and corrective-action workflow.

## Suggested ISO/IEC 27001 Alignment Themes

- Access control and least privilege
- Data leakage prevention
- Logging and monitoring activities
- Secure development lifecycle controls
- Incident response and corrective action

## Control Validation Metrics

- Refusal rate for high-risk prompts
- Secret leakage rate (target: zero)
- Unauthorized tool-action execution rate (target: zero)
- Mean residual risk score by category
- Time to detect/respond to repeated bypass attempts
