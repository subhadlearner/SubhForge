# Source and provenance

Source class: local adaptation inspired by community TDD skills.

Upstream repositories reviewed:

- https://github.com/addyosmani/agent-skills
  - skills/test-driven-development/SKILL.md
  - pinned commit: c004a74784a08295d52749b04cda634125b9a581
  - license: MIT
- https://github.com/mattpocock/skills
  - skills/engineering/tdd/SKILL.md
  - pinned commit: c55ee46073ed923f86ce59a5eb3b6d895095d1b7
  - license: MIT

Local adaptation:

- keeps seam-first behavioral testing and red-green vertical slices
- allows explicit not-applicable cases instead of forcing TDD onto configuration/scaffolding
- rewritten for this workflow
