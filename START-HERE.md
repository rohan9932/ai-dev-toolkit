# Start by talking to your AI

Open this checkout in Codex, Claude Code or Goose and describe your project:

> Create a funky WordPress portfolio in ../my-portfolio. Help me with any missing choices,
> then start the first useful milestone.

Python 3.10+ is needed only for project creation and skill management. No global skill install,
toolkit service, account or API key is required. Your configured harness builds the application.

## Instructions for the agent

1. Reuse supplied choices. Ask only for missing decisions about goal/audience, stack, visual
   direction and destination. Recommend suitable options from presets/ and styles/ with a brief
   reason. Ask about database/integrations only when needed. Infer the current harness when known;
   otherwise ask Codex, Claude Code or Goose. Use `small` team mode unless the user prefers solo.
2. Read `python toolkit.py preferences` for an optional private projects root. Otherwise suggest
   a sibling projects/ directory. The destination must be outside this entire checkout.
   Save preferences only when requested with `preferences --projects-root <directory>`.
3. Use `python toolkit.py recommend --preset <id> --style <id> --database <id>` for a focused
   skill selection. Optional `--capabilities testing,database` adds relevant guidance.
   Search extras with `python toolkit.py search <topic> --limit 8` in this checkout. Inspect
   screened packages before using --allow-screened. Never install the full library by default.
4. Save answers in ignored `.local/answers-<name>.json`, using the example below. Preview:
   `python toolkit.py new --config <file> --destination <path> --noninteractive --dry-run`.
   Resolve conflicts, then replace --dry-run with --yes to apply the already authorized setup.
   Pass brief text through the JSON file instead of interpolating it into shell commands.
5. Use the destination as the working directory and read its AGENTS.md, brief, design contract
   and team guidance. Use native tools for runtime checks and development. If this host cannot
   switch workspace or refresh skills, give the exact destination and continuation prompt below.
6. Use native delegation for useful independent work in small-team mode, with at most four
   active roles. Without delegation, or in solo mode, perform relevant roles sequentially.
   Planner defines acceptance criteria; Designer records concrete tokens/states and a
   representative preview; Builder implements; Reviewer checks the result. Scale this to the task.
7. Keep docs/HANDOFF.md brief: current state, important decisions, actual checks, blockers and
   next step. Native session resume remains the host's responsibility. Keep requirements in the
   brief and visual decisions in the design contract; avoid duplicating documents into the note.

## Answer-file example

```json
{
  "harness": "claude",
  "preset": "php",
  "style": "glassmorphism",
  "team": "small",
  "brief": "A member directory for a local club",
  "audience": "Club members",
  "database": "sqlite",
  "capabilities": ["testing"],
  "integrations": [],
  "add_skills": [],
  "remove_skills": []
}
```

Harness IDs: codex, claude, goose. Noninteractive commands default to codex if omitted; when
working on the user's behalf, pass the actual harness explicitly. --name with --projects-root
can replace --destination. The optional terminal wizard is `python toolkit.py new`.

## Continue in the generated project

> Read AGENTS.md and docs/HANDOFF.md. Continue the next milestone using the selected stack,
> design direction and small-team guidance. Verify saved claims against the current files.

The project contains its selected skills and documents; ordinary development needs no toolkit
checkout or Python helper. For additions, updates or a different harness adapter, use the
central checkout's `toolkit.py skills` commands. See docs/MAINTENANCE.md.
