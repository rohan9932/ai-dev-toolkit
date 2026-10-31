# Universal AI Development Toolkit

A portable project starter and specialist skills library for Codex, Claude Code and Goose.
Your harness handles editing, commands, planning, sessions and delegation. This toolkit adds
design direction, stack-specific knowledge and a small set of project agreements.

## Clone, open, talk

```bash
git clone https://github.com/creativekamrul/ai-dev-toolkit.git
cd ai-dev-toolkit
```

Open the folder in your coding harness and say:

> Read START-HERE.md. Create a funky WordPress portfolio in ../my-portfolio.
> Help me with any missing choices, then start the first useful milestone.

The AI asks only for missing choices, recommends relevant skills, previews setup and creates
the project outside the toolkit. If the host cannot switch workspace, open the new folder and say:

> Read AGENTS.md and docs/HANDOFF.md. Continue the next milestone.

Python 3.10+ is the only setup-helper requirement. No global skill installation, toolkit service
or API key is needed. The harness must already be configured. Application runtimes depend on
your chosen stack. Normal development in a generated project does not require toolkit scripts.

## What you choose

- **18 stacks:** HTML/CSS/JavaScript, PHP, Laravel, WordPress site/plugin/theme/headless,
  Next.js, React/Vite, MERN, Express, NestJS, SaaS, landing page, API service, n8n, Python or custom.
- **9 design directions:** business, funky, glassmorphism, minimal, editorial, brutalist,
  match existing, custom references or no UI.
- **Harness:** Codex, Claude Code or Goose. Selected skills use the host's native directory.
- **Team:** Planner, Designer, Builder and Reviewer using native delegation, or sequential solo roles.

The Designer turns the chosen direction into concrete tokens, states and a representative preview.
Framework and database skills guide implementation; stack-specific quality checks define evidence.
Role briefs guide native agents and do not launch a separate runtime.

## What travels with each project

Only selected specialist packages, plus a project brief, design contract, short handoff note,
quality criteria and role briefs. AGENTS.md holds shared agreements. Claude Code additionally
gets CLAUDE.md importing AGENTS.md and skills in .claude/skills; Codex and Goose use .agents/skills.
Goose also gets a short .goosehints adapter. No custom task database, checkpoint service or doctor.

The central passive library contains **776 packages**: 635 local snapshots, 132 community imports
and 9 toolkit skills. **14 are reviewed; 762 are screened optional packages.** Supporting files,
licenses and provenance travel with installed packages. Generic delivery and code-review checklists remain
optional and are no longer installed by every preset. The library is not loaded wholesale.

Screened imports may have original-host dependencies; compatibility needs task-specific review.
The historical discovery index is audit data, not the recommended installation list.

## Optional commands â€” the AI can run them

```bash
python toolkit.py new --name olive --preset php --style glassmorphism --database sqlite --harness claude --noninteractive --dry-run
python toolkit.py search "php escaping" --limit 5
python toolkit.py preferences --projects-root ../projects
python toolkit.py skills add --project ../projects/olive --skill block-testing-strategy --dry-run
python toolkit.py skills update --project ../projects/olive --harness goose --dry-run
python toolkit.py skills check --project ../projects/olive
python toolkit.py skills rollback --project ../projects/olive --dry-run
```

Replace --dry-run with --yes to apply the agreed change. Updates preserve project documents,
stop on conflicting skill edits and save reversible backups. Switching harnesses moves managed
skills into the appropriate native directory; local customizations are never silently discarded.
Machine-specific preferences stay in ignored .local/. See [maintenance](docs/MAINTENANCE.md).

## Details and validation

[Start here](START-HERE.md) Â· [Compatibility and sources](docs/COMPATIBILITY.md) Â·
[Team](docs/TEAM.md) Â· [Architecture](docs/ARCHITECTURE.md) Â· [Catalog](docs/CATALOG.md) Â·
[Validation results](PROGRESS.md) Â· [Outcome evaluation](evaluation/README.md)

Maintenance checks: install requirements-dev.txt, run `python scripts/validate.py`, then
`python -m unittest discover -s tests -v`. CI covers Windows/Ubuntu behavior and application fixtures.
See compatibility evidence for the difference between adapter layout tests and native runtime checks.

Original toolkit code is MIT licensed. Imported packages retain their own licenses; see
THIRD-PARTY-NOTICES.md and package provenance. The WordPress evaluation plugin is GPL-2.0-or-later.
