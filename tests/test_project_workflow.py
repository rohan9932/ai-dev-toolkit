import contextlib,hashlib,io,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cli,catalog_search,routing,skill_manager as manager
init=manager.init


class WorkflowFixture:
    def setUp(self):
        base=ROOT.parent/('.'+ROOT.name+'-test-runs');base.mkdir(exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=base);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.project=self.root/'project';self.toolkit=ROOT
    def plan(self,**kw):
        args=dict(root=self.toolkit,destination=self.project,preset_id='html-css',style_id='funky',team='small',brief='Club directory',audience='Members',database='none',integrations=[],extras=[],removed=[])
        args.update(kw);return init.build_plan(**args)[0]
    def install(self,**kw):
        with contextlib.redirect_stdout(io.StringIO()):init.apply_plan(self.plan(**kw),yes=True)
    def run_changes(self,extra=()):
        changes,preserved=manager.plan_change(self.toolkit,self.project,extra)
        with contextlib.redirect_stdout(io.StringIO()):tid=manager.apply(self.project,changes,yes=True)
        return tid,preserved
    def copy_toolkit(self):
        self.toolkit=self.root/'toolkit';self.toolkit.mkdir()
        for folder in ('presets','styles','manifests'):
            shutil.copytree(ROOT/folder,self.toolkit/folder)
        for folder in ('agents','design','instructions'):
            shutil.copytree(ROOT/'library'/folder,self.toolkit/'library'/folder)
        catalog=json.loads((ROOT/'manifests/catalog.json').read_text(encoding='utf-8'))
        for s in catalog['skills']:
            if s['validation']['status']=='reviewed':shutil.copytree(ROOT/s['path'],self.toolkit/s['path'])
    def change_upstream(self,sid='web-foundations',remove=None):
        file=self.toolkit/'manifests/catalog.json';catalog=json.loads(file.read_text(encoding='utf-8'));s=next(x for x in catalog['skills'] if x['id']==sid)
        path=self.toolkit/s['path']/(remove or 'SKILL.md')
        if remove:path.unlink();s['files'].remove(remove);del s['fileHashes'][remove]
        else:
            path.write_bytes(path.read_bytes()+b'\nNew upstream guidance.\n');s['fileHashes']['SKILL.md']=hashlib.sha256(path.read_bytes()).hexdigest()
        file.write_text(json.dumps(catalog),encoding='utf-8')
    def snapshot(self):return {p.relative_to(self.project).as_posix():p.read_bytes() for p in self.project.rglob('*') if p.is_file()}


class WorkflowTests(WorkflowFixture,unittest.TestCase):
    def test_entire_toolkit_tree_is_rejected(self):
        for dest in (ROOT,ROOT/'library/new-project',ROOT/'.local/new-project'):
            with self.assertRaises(ValueError):self.plan(destination=dest)
    def test_preferences_are_private_and_name_creates_external_folder(self):
        prefs=self.root/'fake-toolkit';prefs.mkdir()
        with patch.object(cli,'ROOT',prefs),contextlib.redirect_stdout(io.StringIO()):
            cli.main(['preferences','--projects-root',str(self.root/'projects')])
        self.assertTrue((prefs/'.local/preferences.json').is_file())
        r=subprocess.run([sys.executable,str(ROOT/'toolkit.py'),'new','--name','olive','--projects-root',str(self.root),'--preset','php','--style','glassmorphism','--noninteractive','--yes'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertTrue((self.root/'olive/AGENTS.md').is_file())
    def test_invalid_name_has_no_side_effects(self):
        for name in ('../escape','CON','folder/name'):
            with patch.object(init,'ROOT',ROOT),self.assertRaises(ValueError):init.main(['--name',name,'--projects-root',str(self.root),'--preset','php','--noninteractive','--yes'])
        self.assertEqual(list(self.root.iterdir()),[])
    def test_database_and_capability_route_to_reviewed_skills(self):
        plan=self.plan(database='sqlite',capabilities=['testing'])
        self.assertIn('.agents/skills/database-workflow/SKILL.md',plan)
        self.assertIn('.agents/skills/block-testing-strategy/SKILL.md',plan)
        result=routing.recommendations(ROOT,'php','glassmorphism','sqlite',['testing'])
        self.assertIn('database: sqlite',next(x for x in result if x['id']=='database-workflow')['reasons'])
    def test_known_stack_style_conflicts_rejected(self):
        for extra in ('frontend-implementation','professional-ui','wordpress-wp-plugin-development'):
            with self.assertRaises(ValueError):self.plan(extras=[extra])
        with self.assertRaises(ValueError):self.plan(capabilities=['imaginary'])
    def test_small_project_and_central_search(self):
        self.install();self.assertLess((self.project/'.ai-toolkit/catalog.json').stat().st_size,20000)
        self.assertFalse((self.project/'.ai-toolkit/search-index.json').exists())
        self.assertEqual(list(self.project.rglob('*.py')),[])
        r=subprocess.run([sys.executable,str(ROOT/'toolkit.py'),'search','php escaping','--limit','1'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(json.loads(r.stdout)[0]['id'],'php-development')
        with self.assertRaises(ValueError):catalog_search.search({'skills':[]},limit=1000)
        r=subprocess.run([sys.executable,str(ROOT/'toolkit.py'),'search','unfindable_topic'],capture_output=True,text=True)
        self.assertEqual(json.loads(r.stdout),[]);self.assertIn('Try fewer terms',r.stderr)
    def test_add_preserves_brief_design_handoff_and_user_instructions(self):
        self.install();agents=self.project/'AGENTS.md';agents.write_bytes(agents.read_bytes()+b'\nUser instruction: keep the logo.\n')
        for file in ('docs/PROJECT-BRIEF.md','docs/DESIGN-CONTRACT.md','docs/HANDOFF.md'):(self.project/file).write_text('User content')
        tid,_=self.run_changes(['block-testing-strategy'])
        self.assertTrue(tid);self.assertIn('keep the logo',agents.read_text())
        for file in ('docs/PROJECT-BRIEF.md','docs/DESIGN-CONTRACT.md','docs/HANDOFF.md'):self.assertEqual((self.project/file).read_text(),'User content')
        self.assertIn('block-testing-strategy',json.loads((self.project/'.ai-toolkit/installed.json').read_text())['skills'])
        self.assertEqual(manager.check(self.project),[])
    def test_dry_run_and_missing_confirmation_do_not_mutate(self):
        self.install();before=self.snapshot();changes,_=manager.plan_change(ROOT,self.project,['block-testing-strategy'])
        with contextlib.redirect_stdout(io.StringIO()):manager.apply(self.project,changes,dry_run=True)
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(ValueError):manager.apply(self.project,changes)
        self.assertEqual(before,self.snapshot())
    def test_upstream_update_is_restorable(self):
        self.copy_toolkit();self.install();old=(self.project/'.agents/skills/web-foundations/SKILL.md').read_bytes();self.change_upstream()
        tid,_=self.run_changes();self.assertNotEqual(old,(self.project/'.agents/skills/web-foundations/SKILL.md').read_bytes())
        with contextlib.redirect_stdout(io.StringIO()):manager.rollback(self.project,tid,yes=True)
        self.assertEqual(old,(self.project/'.agents/skills/web-foundations/SKILL.md').read_bytes());self.assertEqual(manager.check(self.project),[])
    def test_repeating_add_is_a_no_op(self):
        self.install();self.run_changes(['block-testing-strategy']);before=self.snapshot()
        tid,_=self.run_changes(['block-testing-strategy'])
        self.assertIsNone(tid);self.assertEqual(before,self.snapshot())
    def test_removed_upstream_file_is_backed_up_and_restored(self):
        self.copy_toolkit();self.install();p=self.project/'.agents/skills/web-foundations/LICENSE.txt';before=p.read_bytes()
        self.change_upstream(remove='LICENSE.txt');tid,_=self.run_changes();self.assertFalse(p.exists())
        with contextlib.redirect_stdout(io.StringIO()):manager.rollback(self.project,tid,yes=True)
        self.assertEqual(p.read_bytes(),before)
    def test_legacy_receipt_without_markers_preserves_user_edit(self):
        self.install();p=self.project/'AGENTS.md';p.write_text('Legacy customized instructions')
        baseline=self.project/'.ai-toolkit/base/AGENTS.md';baseline.unlink()
        with self.assertRaises(ValueError):manager.plan_change(ROOT,self.project,['block-testing-strategy'])
        self.assertEqual(p.read_text(),'Legacy customized instructions')
    def test_missing_handoff_is_added_without_resetting_brief(self):
        self.install();p=self.project/'.ai-toolkit/installed.json';v=json.loads(p.read_text())
        missing={'docs/HANDOFF.md','docs/QUALITY-CHECKS.md'}
        for rel in missing:(self.project/rel).unlink()
        v['files']=[row for row in v['files'] if row['path'] not in missing];p.write_text(json.dumps(v))
        (self.project/'docs/PROJECT-BRIEF.md').write_text('Keep this brief')
        self.run_changes();self.assertTrue((self.project/'docs/HANDOFF.md').is_file())
        self.assertEqual((self.project/'docs/PROJECT-BRIEF.md').read_text(),'Keep this brief')
    def test_customized_upstream_conflict_leaves_everything_unchanged(self):
        self.copy_toolkit();self.install();(self.project/'.agents/skills/web-foundations/SKILL.md').write_text('My custom skill');before=self.snapshot();self.change_upstream()
        with self.assertRaises(ValueError):manager.plan_change(self.toolkit,self.project)
        self.assertEqual(before,self.snapshot())
    def test_unchanged_upstream_preserves_custom_skill(self):
        self.install();p=self.project/'.agents/skills/web-foundations/SKILL.md';p.write_text('My custom skill')
        _,preserved=self.run_changes(['block-testing-strategy'])
        self.assertIn('.agents/skills/web-foundations/SKILL.md',preserved);self.assertEqual(p.read_text(),'My custom skill')
        self.assertEqual(manager.check(self.project)[0]['status'],'customized')
    def test_modified_managed_instructions_block_add(self):
        self.install();p=self.project/'AGENTS.md';p.write_text(p.read_text().replace('Only these project skills','My changed skill rules'));before=self.snapshot()
        with self.assertRaises(ValueError):manager.plan_change(ROOT,self.project,['block-testing-strategy'])
        self.assertEqual(before,self.snapshot())
    def test_rollback_preserves_edits_made_after_update(self):
        self.install();tid,_=self.run_changes(['block-testing-strategy']);(self.project/'.agents/skills/block-testing-strategy/SKILL.md').write_text('New user change');before=self.snapshot()
        with self.assertRaises(ValueError):manager.rollback(self.project,tid,yes=True)
        self.assertEqual(before,self.snapshot())
    def test_concurrent_change_between_plan_and_apply_is_preserved(self):
        self.install();changes,_=manager.plan_change(ROOT,self.project,['block-testing-strategy']);p=self.project/changes[0]['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_text('Concurrent user edit');before=self.snapshot()
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(ValueError):manager.apply(self.project,changes,yes=True)
        self.assertEqual(before,self.snapshot())
    def test_tampered_receipt_cannot_escape_project(self):
        self.install();p=self.project/'.ai-toolkit/installed.json';v=json.loads(p.read_text());v['files'].append({'path':'../outside','sha256':'0'*64});p.write_text(json.dumps(v))
        with self.assertRaises(ValueError):manager.plan_change(ROOT,self.project)
    def test_partial_update_can_be_recovered(self):
        self.install();before=self.snapshot();changes,_=manager.plan_change(ROOT,self.project,['block-testing-strategy']);real=manager.replace_file;count=0
        def fail_once(path,data):
            nonlocal count
            count+=1
            if count==3:raise OSError('Simulated disk failure')
            return real(path,data)
        with patch.object(manager,'replace_file',side_effect=fail_once),contextlib.redirect_stdout(io.StringIO()),self.assertRaises(OSError):manager.apply(self.project,changes,yes=True)
        with contextlib.redirect_stdout(io.StringIO()):manager.rollback(self.project,yes=True)
        after={p:v for p,v in self.snapshot().items() if not p.startswith('.ai-toolkit/history/')}
        self.assertEqual(before,after)


if __name__=='__main__':unittest.main()
