---
name: security-verification
description: Evidence-based application security verification guidance using OWASP Top 10:2025 as a risk taxonomy, OWASP ASVS 5.0 as a deeper web/API verification reference, and technology-appropriate dependency, secret, SAST, IaC, supply-chain, authentication, authorization, data-protection, and resilience checks.
metadata:
  source_type: official-standard-grounded
  vendor: OWASP
---

# Security Verification

Use this skill when designing, specifying, executing, or reviewing security verification.

## Authority

Follow the project's approved architecture, ADRs, specification, `AGENTS.md`, and configured tooling.

This skill does not authorize introducing a new scanner or changing the security baseline during `/verify`.

If required security tooling is missing, report the gap and route it to architecture/project initialization instead of silently installing a tool.

## Security verification posture

Security verification is evidence-based and risk-scoped.

Do not claim:

- "secure"
- "OWASP compliant"
- "ASVS compliant"
- regulatory compliance

unless an explicitly defined assurance program and its complete evidence support that claim.

Prefer precise statements about:

- checks executed
- controls covered
- findings observed
- uncovered risks
- residual risk

## OWASP Top 10:2025 risk taxonomy

Evaluate applicability of:

1. A01:2025 Broken Access Control
2. A02:2025 Security Misconfiguration
3. A03:2025 Software Supply Chain Failures
4. A04:2025 Cryptographic Failures
5. A05:2025 Injection
6. A06:2025 Insecure Design
7. A07:2025 Authentication Failures
8. A08:2025 Software or Data Integrity Failures
9. A09:2025 Security Logging and Alerting Failures
10. A10:2025 Mishandling of Exceptional Conditions

OWASP Top 10 is an awareness/risk taxonomy, not a complete verification standard.

Use OWASP ASVS 5.0 as a deeper technical-control reference for web/API systems where appropriate.

## Minimum security domains

Evaluate only domains applicable to the system/change, including:

- authentication
- authorization and object/function-level access control
- session/token handling
- input validation and output encoding
- injection, including SQL/NoSQL/command/template classes
- XSS and browser-facing output risks
- CSRF where cookie/session semantics make it relevant
- SSRF and outbound-request trust boundaries
- file upload, path traversal, archive extraction, and unsafe file handling
- deserialization/parser hazards
- cryptography, key management, randomness, and secret handling
- sensitive-data storage, transport, retention, and logging
- error/exception handling and information disclosure
- abuse controls, rate limiting, and resource exhaustion
- security logging, alerting, and auditability
- dependency vulnerabilities
- package provenance and software supply-chain risk
- build/release integrity
- cloud IAM, trust relationships, network boundaries, and least privilege
- IaC and container/image security where applicable
- data integrity, concurrency, idempotency, and replay when security-sensitive
- backup/recovery controls where they protect security or integrity guarantees

## Executable evidence

Prefer deterministic project-approved checks such as:

- dependency vulnerability scanners
- secret scanners
- SAST/static security analyzers
- IaC scanners
- container/image scanners
- framework security analyzers
- targeted auth/authz/injection/security integration tests
- configuration validation
- package lock/provenance verification

Do not infer that a risk is absent merely because no scanner reported it.

Scanner coverage is evidence, not proof.

## Coverage states

For each applicable security category use:

- `PASS`
- `FAIL`
- `NOT_APPLICABLE`
- `NOT_COVERED`

`NOT_COVERED` means applicable risk lacks sufficient approved executable evidence.

It must never be presented as a pass.

## Findings

A security finding should include:

- affected asset/boundary
- threat or failure mode
- evidence
- likely impact
- relevant requirement/control
- severity according to project policy
- required correction or residual-risk statement

Do not invent vulnerabilities merely to populate a checklist.

## Waivers

A security failure remains a failure even when the human owner accepts the risk.

Security waivers must:

- reference the exact failed verification
- preserve the original evidence
- state the residual risk
- identify compensating controls
- expire
- remain visible to review/CI/human production approval

A waiver must never be used to claim security compliance.
