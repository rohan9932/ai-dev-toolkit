"""Interactive project/team installer. Python 3.10+ standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from routing import recommendations,validate_selection
from adapters import HARNESSES,adapter,instruction_files,relocate_markdown

ROOT = Path(__file__).resolve().parents[1]

def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def digest(data):
    return hashlib.sha256(data).hexdigest()

def no_links(path):
    path=Path(os.path.abspath(path))
    for item in [path,*path.parents]:
        if item.is_symlink() or (item.exists() and getattr(item.lstat(),'st_file_attributes',0)&1024):
            raise ValueError(f'Refusing linked/reparse path: {item}')
        if item!=path and item.exists() and not item.is_dir(): raise ValueError(f'Parent is not a directory: {item}')
    return path

def safe_path(root,relative):
    if not relative or '\\' in relative or re.match(r'^[A-Za-z]:',relative): raise ValueError('Invalid portable relative path')
    rel=Path(relative)
    if rel.is_absolute() or '..' in rel.parts: raise ValueError('Path escapes root')
    path=no_links(root/rel)
    if not path.is_relative_to(root): raise ValueError('Path escapes root')
    return path

def choose(label,options,default=None):
    print('\n'+label)
    for index,option in enumerate(options,1):
        print(f"  {index:2}. {option['name']} ({option['id']})"+(' [default]' if option['id']==default else ''))
    while True:
        answer=input('Choose number or ID'+(f' [{default}]' if default else '')+': ').strip() or default
        if answer and answer.isdigit() and 1<=int(answer)<=len(options): return options[int(answer)-1]['id']
        if answer in [o['id'] for o in options]: return answer
        print('Please choose one of the listed options.')

def split_ids(value):
    return value if isinstance(value,list) else [v.strip() for v in (value or '').split(',') if v.strip()]

def build_plan(root,destination,preset_id,style_id,team,brief,audience,database,integrations,extras,removed,allow_screened=False,capabilities=None,harness='codex'):
    root=root.resolve(); destination=no_links(destination)
    host=adapter(harness)
    if destination.exists() and not destination.is_dir(): raise ValueError('Destination must be a directory')
    if destination.is_relative_to(root): raise ValueError('Choose a project directory outside the entire toolkit checkout.')
    catalog=read_json(root/'manifests/catalog.json'); entries={s['id']:s for s in catalog['skills']}
    if len(entries)!=len(catalog['skills']): raise ValueError('Duplicate catalog IDs')
    preset_file=safe_path(root,'presets/'+preset_id+'.json'); style_file=safe_path(root,'styles/'+style_id+'.json')
    if not preset_file.is_file(): raise ValueError('Unknown preset: '+preset_id)
    if not style_file.is_file(): raise ValueError('Unknown design style: '+style_id)
    preset=read_json(preset_file); style=read_json(style_file); options=read_json(root/'manifests/project-options.json')
    if team not in ('small','solo'): raise ValueError('Team must be small or solo')
    if database not in options['databases']: raise ValueError('Unknown database: '+database)
    if any(i not in options['integrations'] for i in integrations): raise ValueError('Unknown integration')
    if any(i not in entries for i in extras+removed): raise ValueError('Unknown additional/removed skill')
    capabilities=capabilities or []
    reasons=recommendations(root,preset_id,style_id,database,capabilities)
    selected={r['id'] for r in reasons}|set(extras)
    selected.update(options['databases'][database]['skills'])
    for integration in integrations: selected.update(options['integrations'][integration]['skills'])
    selected-=set(removed)
    pending=list(selected)
    while pending:
        sid=pending.pop()
        if sid not in entries: raise ValueError('Unknown catalog dependency: '+sid)
        for dep in entries[sid].get('requires',[]):
            if dep in removed: raise ValueError(f'{sid} requires removed skill {dep}')
            if dep not in selected: selected.add(dep); pending.append(dep)
    selected=sorted(selected); plan={};adaptations=[]
    policy=validate_selection(root,selected,preset_id,style_id,database,capabilities)
    targets=set()
    def add(relative,data):
        target=safe_path(destination,relative)
        if relative.casefold() in targets: raise ValueError('Duplicate installation target: '+relative)
        targets.add(relative.casefold())
        if isinstance(data,str): data=data.encode('utf-8')
        state='create'
        if target.exists(): state='unchanged' if target.is_file() and target.read_bytes()==data else 'conflict'
        plan[relative]={'path':target,'data':data,'sha256':digest(data),'action':state}
    for sid in selected:
        entry=entries[sid]
        if entry['validation']['status']!='reviewed' and not (allow_screened and entry['validation']['status']=='screened'):
            raise ValueError(f'{sid} needs task-specific review. Inspect its provenance and scripts; --allow-screened opts into installing it with a review requirement.')
        for filename in entry['files']:
            source=safe_path(root,entry['path']+'/'+filename); data=source.read_bytes()
            if digest(data)!=entry['fileHashes'].get(filename): raise ValueError('Source hash mismatch: '+str(source.relative_to(root)))
            original=data;data=relocate_markdown(data,filename,harness,[entries[s]['name'] for s in selected])
            if data!=original:
                adaptations.append({'path':host['skills']+'/'+entry['name']+'/'+filename,
                    'kind':'native-skill-paths','sourceSha256':digest(original)})
            add(host['skills']+'/'+entry['name']+'/'+filename,data)
    stack_instructions=safe_path(root,preset['instructions']).read_text(encoding='utf-8')
    design_instructions=safe_path(root,style['instructions']).read_text(encoding='utf-8')
    skill_lines='\n'.join(f"- `{sid}`: {entries[sid]['description']}" for sid in selected)
    add('AGENTS.md',f'''# Project working agreements

Read `docs/PROJECT-BRIEF.md`, `docs/DESIGN-CONTRACT.md`, `docs/HANDOFF.md` and `.ai-team/TEAM.md`.
The agent harness provides execution. Use its native file editing, search, commands, connected
tools and delegation where available. These project resources add domain guidance and quality
criteria; they do not replace the harness or require alternative tools for basic operations.
Stack: **{preset['name']}**. Visual direction: **{style['name']}**.
User choices override generic aesthetics in optional skills. Do not default every project to
React or a restrained business look. Preserve the selected stack and existing project constraints.

The Planner coordinates scope and handoffs, the Designer owns the design contract, the Builder
implements, and the Reviewer checks evidence. Follow ownership in `.ai-team/TEAM.md`.
In small-team mode, use native subagents when available for useful independent work;
otherwise perform the named roles sequentially. Do not invent an agent process or successful
handoff. These portable role definitions do not themselves launch agent infrastructure.

<!-- toolkit:skills:start -->
Only these project skills were installed:

{skill_lines}
Selected skill files live in `{host['skills']}/`; let the harness discover and load them.
<!-- toolkit:skills:end -->

Search the central checkout with `python toolkit.py search <topic> --limit 8` when more expertise is needed.
Use `python toolkit.py skills add --project <project> --skill <id> --dry-run` from the central
checkout to preview additions. Updates preserve working documents and stop on conflicting skill edits.
Keep `docs/HANDOFF.md` short: current state, key decisions, actual checks, blockers and next step.
A new chat reads that note and verifies the current files. Use native session resume when available.
For visible UI, agree a representative design preview and record tokens/states in the design contract
before expanding the application. Run the checks in docs/QUALITY-CHECKS.md; report unavailable checks.

{stack_instructions.strip()}
''')
    for filename,content in instruction_files(harness).items():add(filename,content)
    add('docs/PROJECT-BRIEF.md',f'''# Project brief

## Goal

{brief.strip() or 'Clarify the goal with the user before implementing the application.'}

## Audience

{audience.strip() or 'Clarify the intended users during planning.'}

## Selected setup

- Stack: {preset['name']} (`{preset_id}`)
- Design: {style['name']} (`{style_id}`)
- Database: {database}
- Optional integrations: {', '.join(integrations) or 'none'}
- Team mode: {team}

This setup installed instructions and skills only. The Planner identifies acceptance criteria,
existing constraints, privacy requirements and the first useful delivery before building.
No framework, database, MCP connection or application dependency was provisioned.
''')
    contract=design_instructions
    if style_id!='none':
        contract+='''
## Project decisions (Designer fills before expanding the UI)

- Audience and primary task:
- Direction / references and why they fit:
- Concrete colors, typography, spacing, radii and motion:
- Representative screen / preview path:
- Responsive layout changes:
- Loading, empty, error and success states that exist:
- User preference or explicit assumptions:
- Narrow and desktop render evidence; keyboard/contrast checks:

Status: not yet designed. Do not treat this template as evidence of a completed design.
'''
    add('docs/DESIGN-CONTRACT.md',contract)
    add('.gitignore','.ai-toolkit/history/\n.ai-toolkit/operation.lock\n')
    for role in ('planner','designer','builder','reviewer'): add(f'.ai-team/roles/{role}.md',(root/f'library/agents/{role}.md').read_bytes())
    add('.ai-team/TEAM.md',(root/'library/agents/TEAM.md').read_text(encoding='utf-8')+f'\nSelected execution mode: **{team}**.\n')
    add('docs/HANDOFF.md',f'''# Project handoff

Current state: project instructions and selected skills installed; application work has not started.
Decisions: {preset_id}; {style_id}; database {database}; team {team}.
Checks: setup only; no application checks run yet.
Blockers: none recorded.
Next: define acceptance criteria and the first useful milestone; preview the design if there is a UI.

Update this note at meaningful handoffs. Keep durable requirements in PROJECT-BRIEF.md and
visual decisions in DESIGN-CONTRACT.md. Verify saved claims against current files before continuing.
''')
    add('docs/QUALITY-CHECKS.md',(root/'library/instructions/quality-checks.md').read_bytes())
    add('.ai-toolkit/base/AGENTS.md',plan['AGENTS.md']['data'])
    add('docs/AI-TOOLKIT.md',f'''# Project toolkit

Toolkit {catalog['version']}; preset `{preset_id}`; style `{style_id}`; team `{team}`.

Begin with: "Read AGENTS.md and docs/HANDOFF.md, then follow the current request.
Use the relevant roles and skills. A preparation-only request does not authorize building."

Source toolkit: https://github.com/creativekamrul/ai-dev-toolkit
Installed skills: {', '.join(selected)}.
The shared catalog is a snapshot; update from the central repository for another milestone.
Reproduce this setup with `python scripts/init-project.py --config <project.json>
--destination <new-folder> --noninteractive --yes` using `.ai-toolkit/project.json`.
''')
    shared={'toolkitVersion':catalog['version'],'source':'https://github.com/creativekamrul/ai-dev-toolkit',
            'skills':[{k:entries[sid][k] for k in ('id','name','description','category','compatibility','validation')} for sid in selected],
            'selectionReasons':reasons,'harness':harness,'skillDirectory':host['skills'],
            'searchCommand':'From the central checkout: python toolkit.py search <topic> --limit 8'}
    add('.ai-toolkit/catalog.json',json.dumps(shared,indent=2)+'\n')
    needs_review=[sid for sid in selected if entries[sid]['validation']['status']!='reviewed']
    if needs_review:
        add('.ai-toolkit/REVIEW-REQUIRED.md','# Selected community skills requiring review\n\n'+
            '\n'.join('- '+sid for sid in needs_review)+'\n\nThese packages passed license/metadata/static checks, not behavioral review. Before using their instructions or scripts, inspect the installed TOOLKIT-PROVENANCE.json and relevant files. Do not execute unreviewed scripts. User stack, style and authorization remain authoritative.\n')
    config={'preset':preset_id,'style':style_id,'team':team,'harness':harness,'brief':brief,'audience':audience,'database':database,'allow_screened':allow_screened,
            'integrations':integrations,'add_skills':extras,'remove_skills':removed,'capabilities':capabilities}
    add('.ai-toolkit/project.json',json.dumps(config,indent=2)+'\n')
    receipt={'schemaVersion':4,'toolkitVersion':catalog['version'],'preset':preset_id,'style':style_id,'harness':harness,'skills':selected,
             'adaptations':adaptations,
             'files':[{'path':p,'sha256':v['sha256']} for p,v in sorted(plan.items())]}
    add('.ai-toolkit/installed.json',json.dumps(receipt,indent=2)+'\n')
    return plan,selected

def apply_plan(plan,dry_run=False,yes=False,noninteractive=False):
    for relative,item in plan.items(): print(f"{item['action']:10} {relative}")
    if any(item['action']=='conflict' for item in plan.values()): raise ValueError('Conflicts found; no files written. Use a separate folder to compare or merge explicitly.')
    if dry_run: print('Dry run: no files or directories written.'); return False
    if not yes:
        if noninteractive: raise ValueError('Use --yes to install or --dry-run to preview')
        if input('Install these resources? [y/N]: ').strip().lower()!='y': print('Cancelled.'); return False
    for item in plan.values(): no_links(item['path'])
    for item in plan.values():
        if item['action']=='unchanged': continue
        target=no_links(item['path']); target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f: f.write(item['data'])
    return True

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('destination','preset','style','team','brief','audience','database','integrations','add-skills','remove-skills','config','capabilities','name','projects-root'): parser.add_argument('--'+name)
    for name in ('noninteractive','dry-run','yes','list','allow-screened'): parser.add_argument('--'+name,action='store_true')
    parser.add_argument('--harness',choices=HARNESSES)
    args=parser.parse_args(argv)
    presets=[read_json(p) for p in sorted((ROOT/'presets').glob('*.json'))]; styles=[read_json(p) for p in sorted((ROOT/'styles').glob('*.json'))]
    if args.list:
        print(json.dumps({'presets':[{k:p[k] for k in ('id','name')} for p in presets],'styles':[{k:p[k] for k in ('id','name')} for p in styles]},indent=2)); return 0
    preferences=read_json(ROOT/'.local/preferences.json') if (ROOT/'.local/preferences.json').is_file() else {}
    saved=read_json(Path(args.config)) if args.config else {}
    values={name:getattr(args,name) if getattr(args,name) is not None else saved.get(name) for name in
            ('destination','preset','style','team','brief','audience','database','integrations','add_skills','remove_skills','capabilities','harness')}
    if args.name and not values['destination']:
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}',args.name) or re.fullmatch(r'(?i)(con|prn|aux|nul|com[0-9]|lpt[0-9])',args.name):raise ValueError('Use a portable project name with letters, digits, hyphens or underscores')
        projects_root=Path(args.projects_root or preferences.get('projectsRoot') or ROOT.parent/'projects')
        values['destination']=str(projects_root/args.name)
    if not args.noninteractive:
        values['brief']=values['brief'] if values['brief'] is not None else input('What are we building? ')
        values['audience']=values['audience'] if values['audience'] is not None else input('Who is it for? ')
        values['destination']=values['destination'] or input('Destination project directory (outside this toolkit): ').strip()
        values['preset']=values['preset'] or choose('Choose the technology stack',presets)
        values['style']=values['style'] or choose('Choose the visual direction',styles,'business')
        values['harness']=values['harness'] or choose('Which coding harness?',[
            {'id':key,'name':value['name']} for key,value in HARNESSES.items()],'codex')
        values['team']=values['team'] or choose('How should the team work?',[
            {'id':'small','name':'Four roles: Planner, Designer, Builder, Reviewer'},
            {'id':'solo','name':'One agent performs the roles sequentially'}],'small')
        options=read_json(ROOT/'manifests/project-options.json')
        values['database']=values['database'] or choose('Database guidance (no provisioning)',[{'id':k,'name':v['name']} for k,v in options['databases'].items()],'none')
        if values['integrations'] is None: values['integrations']=input('Optional integrations (penpot; Enter for none): ')
        if values['add_skills'] is None: values['add_skills']=input('Extra reviewed skill IDs (comma separated; Enter for defaults): ')
        if values['remove_skills'] is None: values['remove_skills']=input('Remove optional skill IDs (comma separated; Enter for none): ')
    if not values['destination'] or not values['preset']: raise ValueError('--destination and --preset are required')
    plan,selected=build_plan(ROOT,Path(values['destination']),values['preset'],values['style'] or 'business',values['team'] or 'small',
        values['brief'] or '',values['audience'] or '',values['database'] or 'none',split_ids(values['integrations']),split_ids(values['add_skills']),split_ids(values['remove_skills']),args.allow_screened or saved.get('allow_screened',False),split_ids(values['capabilities']),values['harness'] or 'codex')
    if apply_plan(plan,args.dry_run,args.yes,args.noninteractive):
        print(f'Installed {len(selected)} skills and project guidance. Open {Path(values["destination"]).absolute()} and say: Read AGENTS.md and docs/HANDOFF.md, then follow my current request.')
    return 0

if __name__=='__main__':
    try: sys.exit(main())
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as error:
        print('ERROR: '+str(error),file=sys.stderr); sys.exit(1)
