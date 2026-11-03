# Mitigation Recommendations (Audit/GRC Prioritized)

These are proposed controls for systems beyond the mock. The synthetic runs do not validate their effectiveness. Test each control against the target deployment and record bypass attempts and residual risk.

## Priority 1: Mandatory Control Strengthening

1. Use instruction hierarchy (system > developer > user) as one layer. Enforce tool and data permissions outside the model, and test attempted policy bypasses.
2. Implement output filtering for prompt leakage and sensitive-value patterns.
3. Enforce least-privilege tool access with explicit authorization and human approval for high-risk actions.
4. Treat retrieved content as untrusted. Use filtering and trust labels alongside application-enforced tool permissions; test whether injected content causes unauthorized actions.

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
