# SubhForge Migration Manifest

SubhForge consolidates the two repositories that previously made up Subhadeep's personal AI-assisted engineering workflow.

## Source snapshots

- production-ai-project
  - source: https://github.com/subhadlearner/production-ai-project
  - branch: main
  - commit: 9ba3bf77f75f671d41aad6caf61053035ec2babd
  - target responsibility: template/

- kilo-configuration
  - source: https://github.com/subhadlearner/kilo-configuration
  - branch: feature/v0.2.0
  - commit: a524c8dff5ddb1e866f02d1eec4898b08bf4f5ac
  - target responsibilities:
    - kilo/ runtime content -> forge/
    - V0.2 design material -> design/
    - poc/ -> poc/

## Migration rule

This phase is structural only. Existing behaviour must remain unchanged. The old repositories remain the authoritative pre-SubhForge Git history until consolidation is validated and they are archived.

## Validation gate

Before any v0.2 behavioural implementation begins:

1. imported file inventory matches both source snapshots;
2. SubhForge runtime configuration is behaviourally equivalent to the current Kilo configuration;
3. generated project scaffold is equivalent to production-ai-project;
4. Stable v0.1 FAST/FULL smoke remains valid;
5. only after those checks do v0.2 behavioural changes begin.
