"""Native project instruction and skill locations; no agent runtime."""

HARNESSES = {
    'codex': {'name': 'Codex', 'skills': '.agents/skills'},
    'claude': {'name': 'Claude Code', 'skills': '.claude/skills'},
    'goose': {'name': 'Goose', 'skills': '.agents/skills'},
}
SKILL_PREFIXES = tuple(sorted({v['skills'] + '/' for v in HARNESSES.values()}))


def adapter(harness):
    if harness not in HARNESSES:
        raise ValueError('Unknown harness: ' + str(harness))
    return HARNESSES[harness]


def instruction_files(harness):
    adapter(harness)
    if harness == 'claude':
        return {'CLAUDE.md': '@AGENTS.md\n'}
    if harness == 'goose':
        return {'.goosehints': 'Project agreements: AGENTS.md. Selected skills: .agents/skills/.\n'}
    return {}


def relocate_markdown(data, filename, harness, selected_names):
    """Adapt known native skill paths in guidance, never executable/provenance bytes."""
    if not filename.lower().endswith('.md'):
        return data
    target=adapter(harness)['skills'].encode()+b'/'
    for prefix in SKILL_PREFIXES:
        for name in selected_names:
            tail=(name+'/').encode()
            data=data.replace(prefix.encode()+tail,target+tail)
    return data
