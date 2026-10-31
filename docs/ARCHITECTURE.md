# Architecture

The host harness owns execution, native tools, planning, sessions and delegation. The toolkit
owns a passive specialist library, project presets, design directions and safe resource copying.

library/skills, library/community and library/local are passive. Only project-kickoff is active
in this checkout, with Codex/Goose and Claude Code entrypoints. Startup instructions route to
START-HERE.md. Native host discovery loads only selected project skills.

toolkit.py uses Python 3.10+ standard library for new, preferences, recommend, search and skills
management. It has no AI service, custom task tracker, session manager or runtime checker.
The installer selects one harness adapter: AGENTS.md with .agents/skills for Codex/Goose,
or CLAUDE.md importing AGENTS.md with .claude/skills for Claude Code. Goose gets .goosehints too.
Role briefs are passed to native subagents rather than implementing another dispatch runtime.

Projects receive brief/design/handoff documents, quality criteria, role briefs, installed-skill
metadata, source hashes and a portable setup receipt. They contain no Python runtime helper or
copy of the complete search index. The central checkout performs additional skill search/updates.
Projects remain usable without that checkout after creation.
Markdown references to selected skills are relocated to the chosen native skill directory.
Receipts record each adapted file and its original hash; scripts and provenance stay byte-identical.

Creation rejects destinations inside the checkout, links/reparse points, escaping paths and
conflicting existing files. Dry runs write nothing; exclusive creates preserve concurrent edits.
Individual file creation is protected, but the whole installation is not an atomic transaction.

Skill updates compare baseline, current and incoming hashes. They preserve working documents
and detect conflicts before writes. AGENTS.md can update fully when unchanged; otherwise only
the managed skill block changes for current-format projects. Legacy custom instructions require
an explicit manual merge. Changing harness moves only receipt-owned skills and adapter files.
Transactions back up previous bytes locally, and rollback refuses to overwrite subsequent edits.

Legacy task/state records remain historical project-owned data. Upgrade copies their content
into a handoff note when none exists, removes unchanged generated runtime helpers, and replaces
unchanged instructions. It never discards the original notes or a custom handoff document.
