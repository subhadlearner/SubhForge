# Curated Global Skills

These skills are the global engineering skill library for this Kilo configuration.

They are intentionally small, auditable, and technology-focused. Project-specific rules still belong in the project's `.kilo/skills/` directory.

## Authority

When a skill conflicts with approved project artifacts, use this priority:

1. approved PRD requirements
2. approved architecture and ADRs
3. project-level `AGENTS.md` and project rules
4. project-specific skills
5. these global skills
6. generic model knowledge

Do not let a global skill silently replace an approved technology choice.

## Included skills

| Skill | Source class | Primary use |
| --- | --- | --- |
| dotnet-production | Official-doc-grounded local skill | Production C#/.NET/ASP.NET Core engineering |
| python-production | Official-doc-grounded local skill | Production Python engineering |
| postgresql-production | Official-doc-grounded local skill | PostgreSQL schema, transactions, indexing, query performance |
| sqlite-production | Official-doc-grounded local skill | SQLite correctness, concurrency, migrations, performance |
| frontend-design | Anthropic-grounded local adaptation | Creating distinctive, intentional frontend visual design |
| web-design-guidelines | Vercel-grounded local adaptation | Reviewing accessibility, UX, interaction, and interface quality |
| react-best-practices | Vercel-grounded local adaptation | React performance and component/data-flow patterns |
| nextjs-production | Next.js/Vercel-grounded local adaptation | Next.js App Router and production runtime patterns |
| aws-serverless | AWS-grounded local adaptation | Lambda/API Gateway/EventBridge/SQS/Step Functions serverless engineering |
| aws-iam | AWS-grounded local adaptation | IAM policy, role, trust, boundary, and cross-account correctness |
| amazon-dynamodb | AWS-grounded local adaptation | DynamoDB access-pattern-led data modeling and operations |
| azure-architecture | Microsoft-grounded local adaptation | Azure architecture, reliability, security, operations, and cost |
| requirements-grilling | Addy/Matt-grounded local adaptation | Dependency-aware product/design interrogation before PRD |
| tdd | Addy/Matt-grounded local adaptation | Behavioral red → green vertical implementation |
| diagnosing-bugs | Matt-grounded local adaptation | Tight feedback-loop-first root-cause diagnosis |
| adversarial-check | Addy-grounded local adaptation | Fresh-context challenge of high-risk decisions |
| security-verification | OWASP official-standard-grounded local skill | OWASP Top 10:2025 / ASVS-informed security verification, dependency/supply-chain, secrets, SAST, IaC, cloud/IAM, and evidence/waiver discipline |

## Skill governance

- Do not install broad third-party skill packs globally.
- Prefer official/vendor-maintained sources.
- Keep external provenance in each skill's `SOURCE.md`.
- Re-review skills when upstream guidance changes materially.
- Version-sensitive facts, quotas, APIs, service limits, and pricing must be checked against current official documentation before making irreversible decisions.
- External skills are adapted rather than copied wholesale so that Kilo receives concise, stable guidance without unnecessary scripts or network dependencies.
