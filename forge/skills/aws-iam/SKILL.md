---
name: aws-iam
description: AWS IAM correctness and least-privilege guidance. Use for IAM roles, identity/resource policies, trust policies, STS assume-role, cross-account access, permission boundaries, Organizations/SCP interactions, and service execution roles.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: AWS
---

# AWS IAM

IAM mistakes are security defects. Verify non-trivial policy behavior against current AWS documentation.

## Evaluation model

- Explicit deny wins.
- Distinguish identity policies, resource policies, permissions boundaries, session policies, SCPs/RCPs where applicable, and service-specific controls.
- Do not assume an `Allow` in one layer bypasses restrictions in another.
- Be deliberate about principal type and account boundaries.

## Role and trust design

- Separate trust policy (who may assume) from permission policy (what the session may do).
- Use service principals and condition keys exactly as documented.
- For service-to-service trust, consider confused-deputy protections such as source account/source ARN where supported.
- For cross-account access, verify both sides of the relationship.
- Prefer temporary credentials/roles over long-lived IAM user keys.

## Least privilege

- Derive permissions from actual API operations and resource shapes.
- Scope resources and conditions where the service supports it.
- Avoid wildcard `Action` and `Resource` unless required and explicitly justified.
- Treat `iam:PassRole` as high impact and scope it tightly.
- Keep administrative roles distinct from application execution roles.

## Conditions and policy safety

- Verify condition-key availability for the specific action/resource.
- Understand `IfExists`, set operators, null/missing keys, and multi-valued context keys before using them.
- Test policies with representative requests and policy simulation/tools when available.

## Operational rules

- Never print or commit credentials.
- Rotate/revoke compromised credentials immediately.
- Record why each broad permission exists.
- Review permissions after architecture changes.
- For Organizations/SCPs, STS duration, service-linked roles, and quota/behavior edge cases, check current AWS docs instead of model memory.

If IAM is part of a serverless workload, load both `aws-iam` and `aws-serverless`.
