# the-well-design-system

> Universal rules (em-dash ban, migration idempotency, PR workflow) live in ~/.claude/CLAUDE.md and apply here automatically.

## Accuracy - all humans and all agents

Repeated here because ~/.claude/CLAUDE.md is not present in cloud or scheduled sessions, so those sessions never see the universal rules above.

- Don't guess, and never present a guess as fact. If you have not confirmed a table, column, file path, function, API behavior, number, or what someone said, check it, or say you don't know and how you would find out.
- Never invent sources, quotes, links, IDs, statistics, or records. Every number and claim in your output must trace to something you actually read; if it can't, cut it or label it unverified. Carry the same rule into any prompt you write for a model (unknown means null, not a plausible value).
- Missing context: if a person is in the conversation and the answer would change the work, ask. Otherwise state your assumption in one line and proceed, or escalate. An unattended job never stalls waiting on a question.

Language mix: PowerShell script (sync-brand-assets.ps1) + GH Actions.
