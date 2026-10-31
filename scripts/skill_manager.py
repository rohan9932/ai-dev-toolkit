"""Preview and apply focused skill changes with conflict checks and restorable backups."""
import hashlib,importlib.util,json,os,uuid
from datetime import datetime,timezone
from pathlib import Path
from adapters import SKILL_PREFIXES

spec=importlib.util.spec_from_file_location('project_initializer',Path(__file__).with_name('init-project.py'))
init=importlib.util.module_from_spec(spec);spec.loader.exec_module(init)
digest=init.digest
read=init.read_json


def current(path):
    if path.exists() and not path.is_file():raise ValueError('Expected a file: '+str(path))
    return path.read_bytes() if path.exists() else None


def block(text):
    start='<!-- toolkit:skills:start -->';end='<!-- toolkit:skills:end -->'
    if text.count(start)!=1 or text.count(end)!=1:raise ValueError('Missing or duplicate skill markers in AGENTS.md')
    left=text.index(start);right=text.index(end)+len(end)
    if right<left:raise ValueError('Invalid skill markers')
    return left,right,text[left:right]


def plan_change(root,project,extras=(),allow_screened=False,harness=None):
    root=root.resolve();project=init.no_links(project)
    config=read(init.safe_path(project,'.ai-toolkit/project.json'))
    receipt=read(init.safe_path(project,'.ai-toolkit/installed.json'))
    # Never use untrusted receipt paths without checking containment/reparse points.
    old={row['path']:row['sha256'] for row in receipt['files']}
    for rel in old:init.safe_path(project,rel)
    config['add_skills']=sorted(set(config.get('add_skills',[]))|set(extras))
    config['allow_screened']=config.get('allow_screened',False) or allow_screened
    config['harness']=harness or config.get('harness','codex')
    desired,selected=init.build_plan(root,project,config['preset'],config['style'],config['team'],config['brief'],config['audience'],
        config['database'],config.get('integrations',[]),config['add_skills'],config.get('remove_skills',[]),config['allow_screened'],config.get('capabilities',[]),config['harness'])
    managed={p for p in desired if p.startswith(SKILL_PREFIXES)}
    managed|={p for p in old if p.startswith(SKILL_PREFIXES)}
    managed|={p for p in ('CLAUDE.md','.goosehints') if p in desired or p in old}
    managed|={'AGENTS.md','.ai-toolkit/base/AGENTS.md','.ai-toolkit/catalog.json','.ai-toolkit/search-index.json',
              '.ai-toolkit/project.json','.ai-toolkit/tools.py','.ai-toolkit/REVIEW-REQUIRED.md',
              '.ai-team/team.py','.ai-team/TEAM.md'}
    managed|={p for p in desired if p.startswith('.ai-team/roles/')}
    # Project-owned documents and old task/state records are never overwritten or deleted.
    for rel in ('docs/HANDOFF.md','docs/QUALITY-CHECKS.md'):
        if rel not in old and not init.safe_path(project,rel).exists():managed.add(rel)
    if 'docs/HANDOFF.md' in managed:
        history=[]
        for rel in ('.ai-team/state.json','.ai-team/tasks.json'):
            path=init.safe_path(project,rel)
            if path.is_file():history.append('## Previous '+rel+'\n\n```json\n'+json.dumps(read(path),indent=2)+'\n```\n')
        if history:
            desired['docs/HANDOFF.md']['data']=('# Project handoff\n\nMigrated notes below are historical claims. Verify current files before continuing.\n\n'+'\n'.join(history)).encode('utf-8')
    changes=[];conflicts=[];preserved=[]
    # Preserve project instructions outside the managed skill block. Legacy installations
    # without a baseline can only update an entirely unchanged AGENTS.md.
    agents=current(init.safe_path(project,'AGENTS.md'))
    baseline=current(init.safe_path(project,'.ai-toolkit/base/AGENTS.md'))
    if agents is not None and baseline is not None:
        try:
            a=agents.decode('utf-8');b=baseline.decode('utf-8');n=desired['AGENTS.md']['data'].decode('utf-8')
            left,right,section=block(a)
            if section!=block(b)[2]:raise ValueError('Customized managed skill block')
            if a!=b:
                if receipt.get('schemaVersion',0)<4:
                    raise ValueError('Legacy instructions need manual migration')
                desired['AGENTS.md']['data']=(a[:left]+block(n)[2]+a[right:]).encode('utf-8')
        except (ValueError,UnicodeError):conflicts.append('AGENTS.md (managed skills block needs a manual merge)')
    for rel in sorted(managed):
        path=init.safe_path(project,rel);before=current(path);after=desired.get(rel,{}).get('data')
        if before==after:continue
        before_hash=digest(before) if before is not None else None
        if rel=='AGENTS.md' and baseline is not None and not conflicts:
            pass
        elif before_hash!=old.get(rel):
            if after is not None and digest(after)==old.get(rel):
                preserved.append(rel);continue
            conflicts.append(rel);continue
        if before is not None or after is not None:changes.append({'path':rel,'before':before,'after':after})
    if conflicts:raise ValueError('Conflicts; no files changed: '+', '.join(conflicts))
    new_receipt=dict(receipt,toolkitVersion=read(root/'manifests/catalog.json')['version'],skills=selected,harness=config['harness'],schemaVersion=4,
                     adaptations=json.loads(desired['.ai-toolkit/installed.json']['data'])['adaptations'])
    hashes=dict(old)
    for change in changes:
        if change['after'] is None:hashes.pop(change['path'],None)
        else:hashes[change['path']]=digest(change['after'])
    new_receipt['files']=[{'path':p,'sha256':h} for p,h in sorted(hashes.items())]
    before=current(init.safe_path(project,'.ai-toolkit/installed.json'))
    after=(json.dumps(new_receipt,indent=2)+'\n').encode()
    if before!=after:changes.append({'path':'.ai-toolkit/installed.json','before':before,'after':after})
    return changes,preserved


def replace_file(path,data):
    """Replace one owned file; never leave a partially written target."""
    init.no_links(path);path.parent.mkdir(parents=True,exist_ok=True)
    if data is None:
        path.unlink();return
    temp=path.with_name(path.name+'.toolkit-'+uuid.uuid4().hex)
    try:
        with temp.open('xb') as f:f.write(data)
        os.replace(temp,path)
    finally:
        if temp.exists():temp.unlink()


def apply(project,changes,yes=False,dry_run=False):
    project=init.no_links(project)
    for row in changes:
        action='remove' if row['after'] is None else 'create' if row['before'] is None else 'update'
        print(action+' '+row['path'])
    if dry_run or not changes:return None
    if not yes:raise ValueError('Use --yes to apply or --dry-run to preview')
    lock=init.safe_path(project,'.ai-toolkit/operation.lock')
    with lock.open('x') as f:f.write(str(os.getpid()))
    try:
        for row in changes:
            if current(init.safe_path(project,row['path']))!=row['before']:raise ValueError('File changed after preview: '+row['path'])
        tid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:12]
        history=init.safe_path(project,'.ai-toolkit/history/'+tid);history.mkdir(parents=True)
        # Hide each backup even in legacy projects without a top-level ignore rule.
        with (history/'.gitignore').open('x',encoding='utf-8') as f:f.write('*\n')
        journal={'id':tid,'status':'prepared','changes':[]}
        for row in changes:
            if row['before'] is not None:
                backup=init.safe_path(history,'files/'+row['path']);backup.parent.mkdir(parents=True,exist_ok=True)
                with backup.open('xb') as f:f.write(row['before'])
            journal['changes'].append({'path':row['path'],'before':digest(row['before']) if row['before'] is not None else None,
                'after':digest(row['after']) if row['after'] is not None else None})
        record=history/'transaction.json';replace_file(record,(json.dumps(journal,indent=2)+'\n').encode())
        try:
            for row in changes:
                path=init.safe_path(project,row['path'])
                if current(path)!=row['before']:raise ValueError('Concurrent edit: '+row['path'])
                replace_file(path,row['after'])
        except Exception:
            # The prepared journal can be restored after disk errors; never erase it.
            print('Interrupted update. Restore transaction with: skills rollback --transaction '+tid)
            raise
        journal['status']='applied';replace_file(record,(json.dumps(journal,indent=2)+'\n').encode())
        print('Saved rollback transaction: '+tid)
        return tid
    finally:lock.unlink()


def rollback(project,transaction=None,yes=False,dry_run=False):
    project=init.no_links(project);history=init.safe_path(project,'.ai-toolkit/history')
    candidates=[]
    if history.exists():
        for p in sorted(history.glob('*/transaction.json'),reverse=True):
            init.no_links(p)
            data=read(p)
            if data['status'] in ('applied','prepared'):candidates.append((p,data))
    if transaction:
        candidates=[(p,d) for p,d in candidates if p.parent.name==transaction]
    if not candidates:raise ValueError('No restorable transaction')
    record,journal=candidates[0];changes=[]
    for row in journal['changes']:
        path=init.safe_path(project,row['path']);now=current(path);h=digest(now) if now is not None else None
        if h not in (row['after'],row['before']) or journal['status']=='applied' and h!=row['after']:
            raise ValueError('Cannot rollback a file edited after the update: '+row['path'])
        previous=None
        if row['before'] is not None:
            previous=init.safe_path(record.parent,'files/'+row['path']).read_bytes()
            if digest(previous)!=row['before']:raise ValueError('Corrupt backup: '+row['path'])
        if now!=previous:changes.append({'path':row['path'],'before':now,'after':previous})
    print('Restore transaction: '+record.parent.name)
    # Rollback is itself recorded, making it reversible. The lock covers apply; journal
    # status is bookkeeping, not permission to bypass file hash verification.
    result=apply(project,changes,yes,dry_run)
    if yes and not dry_run:
        journal['status']='reverted';replace_file(record,(json.dumps(journal,indent=2)+'\n').encode())
    return result


def check(project):
    project=init.no_links(project);receipt=read(init.safe_path(project,'.ai-toolkit/installed.json'));result=[]
    for row in receipt['files']:
        if not row['path'].startswith(SKILL_PREFIXES):continue
        data=current(init.safe_path(project,row['path']))
        if data is None or digest(data)!=row['sha256']:
            result.append({'path':row['path'],'status':'missing' if data is None else 'customized'})
    return result
