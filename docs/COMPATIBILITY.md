# Harness adapters and evidence

The setup helper requires Python 3.10+ standard library only. Each generated project selects
one harness; native delegation and tool availability are supplied by that installed host.

| Harness | Instructions | Selected skills |
|---|---|---|
| Codex | AGENTS.md | .agents/skills/<name>/SKILL.md |
| Claude Code | CLAUDE.md importing @AGENTS.md | .claude/skills/<name>/SKILL.md |
| Goose | AGENTS.md and a short .goosehints | .agents/skills/<name>/SKILL.md |

This follows [Codex skills](https://learn.chatgpt.com/docs/build-skills) and
[project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[Claude Code skills](https://code.claude.com/docs/en/skills) and
[shared instruction imports](https://code.claude.com/docs/en/memory#share-one-file-with-other-coding-tools),
and Goose's official [skill locations](https://github.com/aaif-goose/goose/blob/main/documentation/docs/guides/context-engineering/using-skills.md)
and [hint loader](https://github.com/aaif-goose/goose/blob/main/crates/goose/src/hints/load_hints.rs).
Sources checked 2026-11-01. Claude's explicit import also supports versions that do not read
AGENTS.md directly. No symlinks or global host configuration changes are needed.

The toolkit checkout has both native kickoff entrypoints so any of these hosts can start setup.
They contain identical instructions; Goose may discover either compatible copy, depending on its
version. Generated projects have only one skill location, avoiding duplicate installed packages.

Use `python toolkit.py skills update --project <folder> --harness claude --dry-run` from the
central checkout to switch adapters; apply with --yes. Codex and Goose share their skill location.
Start the host in the project afterward or refresh its skill discovery. Customized managed files
cause conflicts when moving; merge them explicitly before switching. No adapter installs a host,
model provider, browser, MCP service or framework runtime.

Automated tests exercise every stack/style/harness layout, selected bytes, conflict handling,
portable config replay, harness switching and rollback. Layout tests do not prove native loading.
Codex's real loader is tested separately without a model call; see PROGRESS.md for current evidence.
Goose 1.51.0 native skills/list discovery is also verified; no model or provider call is needed.
Claude Code layout and relocated WordPress commands are tested, but its native loader is not
verified on this machine because Claude Code is not installed.
Additional screened imports can still contain host-specific dependencies and require review.

Maintainer application fixtures exercise representative HTML, PHP, Next.js and WordPress behavior.
They do not establish that every future AI-generated application will meet its design contract.
Normal project work needs only the chosen harness, relevant application runtimes and project files.
