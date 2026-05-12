# Agent instructions (Huginn)

Huginn does **not** use `CLAUDE.md`. Use this file as the project entry point for Cursor agents.

| Topic | Canonical doc |
|--------|----------------|
| Cursor agent conventions (GitLab, resume, authority) | [`docs/workflows/cursor_agent_protocol.md`](docs/workflows/cursor_agent_protocol.md) |
| CI/CD, staging vs prod, `Makefile` / `release/x.y.z` / EB | [`docs/architecture/SAO.md`](docs/architecture/SAO.md) §9–§10 |
| Milestone → factory → release | **dark-factory** Cursor skill (`SKILL.md` in that skill folder); phases **4.5–6** must match **SAO** + repo **Makefile** |
| Factory scaffold (`factory/`, scripts, prompts) | [`factory/README.md`](factory/README.md) |
| Cautious implementation / LE review bar | [`.cursor/agents/dr-dobbs-v2.md`](.cursor/agents/dr-dobbs-v2.md) (see also protocol) |

If anything disagrees, **this repo’s SAO and Makefile win** over skill wording.
