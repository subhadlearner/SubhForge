---
name: azure-architecture
description: Azure architecture guidance for selecting and integrating Azure services with reliability, security, identity, networking, observability, deployment, governance, and cost controls. Use for Azure solution design and implementation decisions after the project selects Azure.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: Microsoft
---

# Azure Architecture

## Authority

Use only the services, region strategy, networking model, identity model, and IaC approach approved by the architecture/ADRs. If a major Azure service choice is missing, return to architecture instead of guessing.

## Architecture review

Evaluate each relevant workload against:
- reliability and failure domains
- security and identity
- operational excellence
- performance efficiency
- cost optimization

Make tradeoffs explicit rather than claiming every pillar can be maximized simultaneously.

## Identity and secrets

- Prefer Microsoft Entra workload identity/managed identities over embedded credentials when supported.
- Apply least privilege through appropriate Azure RBAC scopes.
- Keep secrets/keys/certificates in approved secret stores such as Key Vault where applicable.
- Do not expose management-plane credentials to application code.

## Reliability

- Define expected RTO/RPO, availability, zone/region failure behavior, retry policy, idempotency, and backpressure.
- Use availability zones/regions only when requirements justify cost and complexity.
- Verify whether each selected service is zonal, zone-redundant, regional, or global; do not infer.
- Design retries with bounded exponential backoff and avoid retry storms.

## Networking

- Choose public, service-endpoint, private-endpoint, VNet integration, and hub/spoke patterns from threat model and operational needs.
- DNS is part of private-endpoint design; plan it explicitly.
- Avoid forcing all traffic through expensive/complex network paths without a requirement.

## Data and messaging

- Select data stores from access, consistency, scale, latency, HA, and operational requirements.
- Select Service Bus, Event Grid, Event Hubs, Storage Queues, or other messaging services from delivery/ordering/throughput semantics, not name similarity.
- Record poison-message/dead-letter and replay behavior.

## Observability and operations

- Use Azure Monitor/Application Insights/Log Analytics only as approved; control ingestion/retention cost.
- Capture actionable logs, metrics, traces, health, and alerts.
- Use IaC and CI/CD for repeatable infrastructure changes.
- Require explicit approval for production deployment.

## Cost

Estimate fixed, variable, network-egress, logging, backup, HA, private-networking, and idle costs. Revisit architecture when cost is disproportionate to requirements.

For exact service capabilities, quotas, SKUs, regional availability, or pricing, verify current Microsoft documentation before implementation.
