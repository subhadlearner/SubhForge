---
name: requirements-grilling
description: Dependency-aware interactive interrogation for large, ambiguous, or high-stakes product/design ideas before PRD creation. Use when important product decisions would otherwise be guessed.
metadata:
  source_type: community-grounded-adaptation
  sources: Addy Osmani and Matt Pocock
---

# Requirements Grilling

The goal is shared understanding, not maximum question count.

## Decision tree

Model unresolved decisions as a dependency tree.

The current frontier contains only questions whose prerequisites are already settled.

Ask the whole useful frontier in a round, then recompute after the user's answers.

## Each question

Include:

- one focused decision
- concrete choices when useful
- a recommended answer
- concise reasoning
- the consequence of the decision when material

The user may accept, reject, or refine the recommendation.

## Facts vs decisions

Research facts yourself whenever tools, repository context, or authoritative docs can answer them.

Examples of facts:

- current code behavior
- existing API shape
- current vendor capability
- repository conventions

Examples of user decisions:

- scope
- priority
- acceptable trade-offs
- business behavior
- success definition
- risk/cost tolerance

Never ask the user to do research the agent can safely perform.

## Avoid interrogation failure modes

- do not ask a giant flat questionnaire
- do not ask dependent questions before prerequisites are settled
- do not keep asking after material decisions are complete
- do not turn best-practice buzzwords into requirements without measurable meaning
- do not make architecture choices during product discovery
- do not interpret polite agreement as evidence when the decision remains unclear

## Completion

Restate:

- outcome
- users
- success
- scope/non-goals
- binding constraints
- confirmed decisions
- explicit assumptions/open questions

Get explicit confirmation before treating discovery as settled.
