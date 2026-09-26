---
name: aws-serverless
description: AWS serverless engineering guidance for Lambda, API Gateway, EventBridge, SQS/SNS, Step Functions, DynamoDB Streams, EventBridge Pipes, SAM/CloudFormation/CDK, retries, concurrency, idempotency, observability, and cost.
metadata:
  source_type: vendor-grounded-adaptation
  vendor: AWS
---

# AWS Serverless

## Authority

Use only AWS services and IaC selected by approved architecture. This skill does not authorize changing providers, regions, persistence, messaging, or deployment tools.

## Event-driven correctness

- Define event contracts, producer/consumer ownership, versioning, and failure semantics.
- Expect at-least-once delivery where the service provides it; make consumers idempotent.
- Design retries, backoff, dead-letter handling, partial-batch failure, and poison-message behavior explicitly.
- Set timeouts so upstream/downstream timeout chains cannot amplify failures.
- Avoid retry storms across Lambda, SDK, queue, and workflow layers.
- Preserve correlation identifiers across asynchronous hops.

## Lambda

- Keep handlers thin; move business logic into testable modules.
- Reuse SDK clients and safe immutable configuration across warm invocations.
- Never depend on execution-environment reuse for correctness.
- Size memory/concurrency from workload evidence.
- Treat reserved/provisioned concurrency as cost and availability controls, not default tuning knobs.
- Validate event-source batch and visibility-timeout relationships.

## Messaging and orchestration

- Use EventBridge for event routing, SQS for durable queueing/backpressure, SNS for fanout, and Step Functions for orchestration only when approved by architecture.
- For SQS/event-source batches, support partial failure where the runtime/integration allows it.
- Use ordering/deduplication features only when the business requirement justifies their cost/constraints.
- Make EventBridge filters precise; avoid consumers receiving irrelevant events.

## Security

- Use least-privilege execution roles and resource policies.
- Avoid wildcard actions/resources except where AWS APIs genuinely require them and the architecture accepts the risk.
- Put secrets in approved secret/configuration stores, never environment/config files committed to source.
- For IAM details, also load `aws-iam`.

## Observability and cost

- Emit structured logs, meaningful metrics, and traces/correlation according to project architecture.
- Alarm on user-impacting failure signals, not every transient retry.
- Consider invocation, duration, concurrency, queue, log-ingestion, tracing, NAT/data-transfer, and state-transition cost.
- Prefer avoiding unnecessary NAT gateways for serverless workloads when approved private/public connectivity patterns make that possible.

## IaC and verification

- Infrastructure changes must go through the approved SAM/CloudFormation/CDK/Terraform workflow.
- Validate templates and permissions before deployment.
- Never deploy production automatically without the project's explicit approval gate.
- Verify quotas, service limits, runtime support, pricing, and newly introduced features against current AWS documentation.
