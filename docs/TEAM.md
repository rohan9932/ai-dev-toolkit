# Small team, native execution

Generated projects receive four concise role briefs in .ai-team/roles/ and a TEAM.md agreement.
The main agent can coordinate as Planner. In small-team mode, use native delegation for useful
independent design, implementation or review, with at most four active roles. Solo mode and hosts
without delegation use sequential roles, with self-review identified honestly.

The toolkit supplies role instructions rather than a scheduler or task tracker. The harness owns
planning, task state, sessions, tool access and permissions. Each worker gets relevant project
documents and selected skill paths; concurrent writers get separate files.

Durable requirements belong in docs/PROJECT-BRIEF.md; visual decisions in docs/DESIGN-CONTRACT.md.
At meaningful handoffs, update docs/HANDOFF.md with current state, evidence, blockers and next step.
Native agent configuration can be added for a specific host when useful; it is not required here.
