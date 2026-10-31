import contextlib,hashlib,importlib.util,io,json,shutil,subprocess,sys,unittest,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
spec=importlib.util.spec_from_file_location('initializer',ROOT/'scripts/init-project.py');init=importlib.util.module_from_spec(spec);spec.loader.exec_module(init)

class SetupTests(unittest.TestCase):
    def setUp(self):
        self.test_root=ROOT.parent/('.'+ROOT.name+'-test-runs');self.run_root=self.test_root/uuid.uuid4().hex;self.run_root.mkdir(parents=True)
        self.dest=self.run_root/'project with spaces';self.addCleanup(self.clean)
    def clean(self):
        target=self.run_root.resolve();assert target.is_relative_to(self.test_root.resolve()) and target!=self.test_root.resolve();shutil.rmtree(target)
    def plan(self,preset='html-css',style='business',**kwargs):
        args=dict(root=ROOT,destination=self.dest,preset_id=preset,style_id=style,team='small',brief='A useful site',audience='Members',database='none',integrations=[],extras=[],removed=[]);args.update(kwargs);return init.build_plan(**args)
    def apply(self,plan,**kwargs):
        with contextlib.redirect_stdout(io.StringIO()):return init.apply_plan(plan,yes=True,noninteractive=True,**kwargs)
    def snapshot(self):return {p.relative_to(self.dest).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.dest.rglob('*') if p.is_file()}
    def test_all_stack_presets_have_a_valid_small_team(self):
        for p in (ROOT/'presets').glob('*.json'):
            with self.subTest(preset=p.stem):
                plan,selected=self.plan(preset=p.stem)
                self.assertNotIn('project-delivery',selected)
                self.assertNotIn('block-code-review',selected)
                self.assertEqual(len([key for key in plan if key.startswith('.ai-team/roles/')]),4)
                self.assertIn('.ai-toolkit/catalog.json',plan)
    def test_all_styles_are_independent_of_stack(self):
        for p in (ROOT/'styles').glob('*.json'):
            with self.subTest(style=p.stem):
                plan,selected=self.plan(style=p.stem)
                self.assertIn('professional-ui',selected) if p.stem=='business' else self.assertNotIn('professional-ui',selected)
                self.assertIn('web-foundations',selected);self.assertNotIn('frontend-implementation',selected)
    def test_dry_run_creates_nothing(self):
        self.apply(self.plan()[0],dry_run=True);self.assertFalse(self.dest.exists())
    def test_repeat_install_preserves_bytes_and_receipt(self):
        plan,_=self.plan();self.apply(plan);before=self.snapshot();self.apply(self.plan()[0]);self.assertEqual(before,self.snapshot())
        receipt=json.loads((self.dest/'.ai-toolkit/installed.json').read_text())
        for file in receipt['files']:self.assertEqual(self.snapshot()[file['path']],file['sha256'])
    def test_agents_conflict_prevents_all_writes(self):
        self.dest.mkdir();(self.dest/'AGENTS.md').write_text('User work');before=self.snapshot()
        with self.assertRaises(ValueError):self.apply(self.plan()[0])
        self.assertEqual(before,self.snapshot())
    def test_customized_skill_is_preserved(self):
        self.apply(self.plan()[0]);p=self.dest/'.agents/skills/web-foundations/SKILL.md';p.write_text('Custom');before=self.snapshot()
        with self.assertRaises(ValueError):self.apply(self.plan()[0])
        self.assertEqual(before,self.snapshot())
    def test_parent_file_is_detected_before_writes(self):
        self.dest.mkdir();(self.dest/'.ai-team').write_text('User work');before=self.snapshot()
        with self.assertRaises(ValueError):self.plan()
        self.assertEqual(before,self.snapshot())
    def test_unknown_skill_and_traversal_are_nonmutating(self):
        with self.assertRaises(ValueError):self.plan(extras=['../../escape'])
        with self.assertRaises(ValueError):self.plan(preset='../escape')
        self.assertFalse(self.dest.exists())
    def test_wordpress_dependency_cannot_be_silently_removed(self):
        with self.assertRaises(ValueError):self.plan(preset='wordpress-plugin',removed=['wordpress-wp-project-triage'])
    def test_screened_skill_requires_opt_in(self):
        with self.assertRaises(ValueError):self.plan(extras=['superpowers-writing-plans'])
        plan,selected=self.plan(extras=['superpowers-writing-plans'],allow_screened=True)
        self.assertIn('.ai-toolkit/REVIEW-REQUIRED.md',plan)
    def test_same_file_created_after_preview_is_never_overwritten(self):
        plan,_=self.plan();target=next(iter(plan.values()))['path'];target.parent.mkdir(parents=True);target.write_text('Concurrent user edit')
        with self.assertRaises(FileExistsError):self.apply(plan)
        self.assertEqual(target.read_text(),'Concurrent user edit')
    def test_config_recreates_selection(self):
        self.apply(self.plan(preset='php',style='glassmorphism')[0]);config=self.dest/'.ai-toolkit/project.json'
        other=self.run_root/'reproduced'
        r=subprocess.run([sys.executable,str(ROOT/'scripts/init-project.py'),'--config',str(config),'--destination',str(other),'--noninteractive','--yes'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual((other/'AGENTS.md').read_bytes(),(self.dest/'AGENTS.md').read_bytes())
    @unittest.skipUnless(shutil.which('pwsh'),'PowerShell wrapper requires pwsh')
    def test_powershell_arguments_are_data_not_shell_code(self):
        brief='A site with $variables, `ticks`, quotes and spaces'
        r=subprocess.run(['pwsh','-NoProfile','-File',str(ROOT/'scripts/init-project.ps1'),'-Destination',str(self.dest),'-Preset','html-css','-Style','funky','-Brief',brief,'-NonInteractive','-Yes'],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr);self.assertIn(brief,(self.dest/'docs/PROJECT-BRIEF.md').read_text())
    def test_missing_confirmation_is_nonmutating(self):
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(ValueError):init.apply_plan(self.plan()[0],noninteractive=True)
        self.assertFalse(self.dest.exists())
    def test_interactive_choices_are_saved_and_installed(self):
        answers='\n'.join(['Member directory','Club members',str(self.dest),'php','glassmorphism','claude','small','sqlite','','','','y',''])
        r=subprocess.run([sys.executable,str(ROOT/'scripts/init-project.py')],input=answers,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        config=json.loads((self.dest/'.ai-toolkit/project.json').read_text())
        self.assertEqual((config['preset'],config['style'],config['database']),('php','glassmorphism','sqlite'))


if __name__=='__main__':unittest.main()
