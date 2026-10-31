"""Conversational setup helpers. No installation, credentials or external service required."""
import argparse,importlib.util,json,sys
from pathlib import Path
from routing import recommendations,rules
from catalog_search import search as search_catalog
from adapters import HARNESSES

ROOT=Path(__file__).resolve().parents[1]


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0]=='new':
        spec=importlib.util.spec_from_file_location('init_project',ROOT/'scripts/init-project.py')
        init=importlib.util.module_from_spec(spec);spec.loader.exec_module(init)
        return init.main(argv[1:])
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('new',help='Start the interactive project wizard (use new --help for options)')
    prefs=sub.add_parser('preferences');prefs.add_argument('--projects-root',type=Path)
    recommend=sub.add_parser('recommend');recommend.add_argument('--preset',required=True);recommend.add_argument('--style',required=True);recommend.add_argument('--database',default='none');recommend.add_argument('--capabilities',default='')
    search=sub.add_parser('search');search.add_argument('query',nargs='?',default='');search.add_argument('--limit',type=int,default=8);search.add_argument('--status',choices=['reviewed','screened'])
    skills=sub.add_parser('skills').add_subparsers(dest='action',required=True)
    for action in ('add','update','check','rollback'):
        s=skills.add_parser(action);s.add_argument('--project',type=Path,required=True)
        if action!='check':s.add_argument('--yes',action='store_true');s.add_argument('--dry-run',action='store_true')
        if action=='add':s.add_argument('--skill',action='append',required=True)
        if action in ('add','update'):s.add_argument('--allow-screened',action='store_true')
        if action=='update':s.add_argument('--harness',choices=HARNESSES)
        if action=='rollback':s.add_argument('--transaction')
    a=p.parse_args(argv)
    if a.command=='preferences':
        file=ROOT/'.local/preferences.json'
        if a.projects_root:
            root=a.projects_root.absolute()
            if root.is_relative_to(ROOT):raise ValueError('Projects root must be outside the toolkit')
            file.parent.mkdir(exist_ok=True);file.write_text(json.dumps({'projectsRoot':str(root)},indent=2)+'\n',encoding='utf-8')
        print(file.read_text(encoding='utf-8') if file.exists() else '{}');return 0
    if a.command=='recommend':
        print(json.dumps(recommendations(ROOT,a.preset,a.style,a.database,[x for x in a.capabilities.split(',') if x]),indent=2));return 0
    if a.command=='search':
        catalog=json.loads((ROOT/'manifests/catalog.json').read_text(encoding='utf-8'))
        policy=rules(ROOT)
        index={'skills':[{'id':s['id'],'description':s['description'][:200],'status':s['validation']['status'],
                         'tags':s['technologies']+[s['category']]+policy['skills'].get(s['id'],{}).get('capabilities',[])} for s in catalog['skills']]}
        result=search_catalog(index,a.query,a.limit,a.status)
        if not result:print('No matches. Try fewer terms or a stack name, for example: search php.',file=sys.stderr)
        print(json.dumps(result,indent=2));return 0
    import skill_manager
    if a.action=='check':
        result=skill_manager.check(a.project);print(json.dumps(result,indent=2));return int(any(r['status']=='missing' for r in result))
    if a.action=='rollback':skill_manager.rollback(a.project,a.transaction,a.yes,a.dry_run);return 0
    changes,preserved=skill_manager.plan_change(ROOT,a.project,getattr(a,'skill',[]),a.allow_screened,getattr(a,'harness',None))
    if preserved:print('Preserved local customizations: '+', '.join(preserved))
    skill_manager.apply(a.project,changes,a.yes,a.dry_run);return 0
