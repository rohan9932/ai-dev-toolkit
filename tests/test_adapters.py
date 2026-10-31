"""Observable project layouts, adapter switching and migration preservation."""
import contextlib,hashlib,io,json,re,shutil,subprocess,sys,unittest
from test_project_workflow import WorkflowFixture,ROOT,manager,init
from adapters import HARNESSES


class AdapterTests(WorkflowFixture,unittest.TestCase):
    def test_all_stack_style_harness_combinations(self):
        for preset in (ROOT/'presets').glob('*.json'):
            for style in (ROOT/'styles').glob('*.json'):
                for harness,host in HARNESSES.items():
                    with self.subTest(preset=preset.stem,style=style.stem,harness=harness):
                        plan=self.plan(preset_id=preset.stem,style_id=style.stem,harness=harness)
                        config=json.loads(plan['.ai-toolkit/project.json']['data'])
                        self.assertEqual(config['harness'],harness)
                        skills=[p for p in plan if p.endswith('/SKILL.md')]
                        self.assertTrue(all(p.startswith(host['skills']+'/') for p in skills))
                        self.assertEqual('CLAUDE.md' in plan,harness=='claude')
                        self.assertEqual('.goosehints' in plan,harness=='goose')
                        self.assertFalse(any(p.endswith('/team.py') or p.endswith('/tools.py') for p in plan))
                        self.assertNotIn('.ai-team/tasks.json',plan)
                        self.assertNotIn('.ai-team/state.json',plan)
                        self.assertNotIn('.ai-toolkit/search-index.json',plan)
    def test_harness_switch_moves_skills_and_rollback_restores(self):
        self.install();before=self.snapshot()
        (self.project/'AGENTS.md').write_bytes((self.project/'AGENTS.md').read_bytes()+b'\nKeep the logo.\n')
        before=self.snapshot()
        changes,_=manager.plan_change(ROOT,self.project,harness='claude')
        with contextlib.redirect_stdout(io.StringIO()):tid=manager.apply(self.project,changes,yes=True)
        self.assertEqual((self.project/'CLAUDE.md').read_text(),'@AGENTS.md\n')
        self.assertFalse(list((self.project/'.agents/skills').rglob('SKILL.md')))
        self.assertTrue(list((self.project/'.claude/skills').rglob('SKILL.md')))
        self.assertIn('Keep the logo.',(self.project/'AGENTS.md').read_text())
        self.assertIn('.claude/skills/',(self.project/'AGENTS.md').read_text())
        self.assertEqual(manager.check(self.project),[])
        with contextlib.redirect_stdout(io.StringIO()):manager.rollback(self.project,tid,yes=True)
        after={p:v for p,v in self.snapshot().items() if not p.startswith('.ai-toolkit/history/')}
        self.assertEqual(before,after)
    def test_cli_switch_and_replay_for_each_harness(self):
        self.install()
        for harness in ('claude','goose','codex'):
            r=subprocess.run([sys.executable,str(ROOT/'toolkit.py'),'skills','update','--project',str(self.project),'--harness',harness,'--yes'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual(manager.check(self.project),[])
            target=self.root/harness
            r=subprocess.run([sys.executable,str(ROOT/'toolkit.py'),'new','--config',str(self.project/'.ai-toolkit/project.json'),'--destination',str(target),'--noninteractive','--yes'],capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue((target/HARNESSES[harness]['skills']).is_dir())
            self.assertEqual((target/'AGENTS.md').read_bytes(),(self.project/'AGENTS.md').read_bytes())
    def test_customized_skill_or_unowned_adapter_blocks_switch(self):
        self.install();p=self.project/'.agents/skills/web-foundations/SKILL.md';p.write_text('My custom skill')
        before=self.snapshot()
        with self.assertRaises(ValueError):manager.plan_change(ROOT,self.project,harness='claude')
        self.assertEqual(before,self.snapshot())
        # A new adapter must not overwrite an existing unrelated instruction file.
        self.project=self.root/'other';self.install();(self.project/'CLAUDE.md').write_text('Private instructions')
        before=self.snapshot()
        with self.assertRaises(ValueError):manager.plan_change(ROOT,self.project,harness='claude')
        self.assertEqual(before,self.snapshot())
    def test_claude_skill_check_detects_custom_edits(self):
        self.install(harness='claude');p=self.project/'.claude/skills/web-foundations/SKILL.md';p.write_text('Custom')
        self.assertEqual(manager.check(self.project),[{'path':'.claude/skills/web-foundations/SKILL.md','status':'customized'}])
    def legacy_project(self):
        self.install();receipt=json.loads((self.project/'.ai-toolkit/installed.json').read_text());files={r['path']:r['sha256'] for r in receipt['files']}
        (self.project/'docs/HANDOFF.md').unlink();files.pop('docs/HANDOFF.md')
        records={'.ai-team/state.json':json.dumps({'summary':'Preview complete','nextTask':'Build signup','evidence':['Keyboard checked']}),
                 '.ai-team/tasks.json':json.dumps({'tasks':[{'id':'signup','status':'doing'}]}),
                 '.ai-team/team.py':'# old task tracker\n','.ai-toolkit/tools.py':'# old runtime helper\n',
                 '.ai-toolkit/search-index.json':'{}',
                 'AGENTS.md':'# Legacy agreements\nUse tools.py resume.\n<!-- toolkit:skills:start -->\nold\n<!-- toolkit:skills:end -->\n'}
        records['.ai-toolkit/base/AGENTS.md']=records['AGENTS.md']
        for rel,content in records.items():
            (self.project/rel).write_bytes(content.encode('utf-8'));files[rel]=hashlib.sha256(content.encode()).hexdigest()
        receipt['files']=[{'path':p,'sha256':h} for p,h in files.items()];receipt['schemaVersion']=3
        (self.project/'.ai-toolkit/installed.json').write_text(json.dumps(receipt))
        return records
    def test_legacy_upgrade_preserves_notes_removes_helpers_and_is_reversible(self):
        records=self.legacy_project();before=self.snapshot();tid,_=self.run_changes()
        self.assertIn('Preview complete',(self.project/'docs/HANDOFF.md').read_text())
        self.assertIn('signup',(self.project/'docs/HANDOFF.md').read_text())
        for rel in ('.ai-team/state.json','.ai-team/tasks.json'):self.assertEqual((self.project/rel).read_text(),records[rel])
        for rel in ('.ai-team/team.py','.ai-toolkit/tools.py','.ai-toolkit/search-index.json'):self.assertFalse((self.project/rel).exists())
        self.assertNotIn('tools.py',(self.project/'AGENTS.md').read_text())
        with contextlib.redirect_stdout(io.StringIO()):manager.rollback(self.project,tid,yes=True)
        self.assertEqual(before,{p:v for p,v in self.snapshot().items() if not p.startswith('.ai-toolkit/history/')})
    def test_legacy_custom_instructions_require_merge(self):
        self.legacy_project();p=self.project/'AGENTS.md';p.write_text(p.read_text()+'\nCustom policy\n');before=self.snapshot()
        with self.assertRaises(ValueError):manager.plan_change(ROOT,self.project)
        self.assertEqual(before,self.snapshot())
    def test_legacy_existing_handoff_is_preserved(self):
        self.legacy_project();p=self.project/'docs/HANDOFF.md';p.write_text('Current user notes')
        self.run_changes();self.assertEqual(p.read_text(),'Current user notes')
    def test_invalid_harness_creates_nothing(self):
        with self.assertRaises(ValueError):self.plan(harness='imaginary')
        self.assertFalse(self.project.exists())
    def test_checkout_kickoff_adapters_stay_in_sync(self):
        self.assertEqual((ROOT/'.agents/skills/project-kickoff/SKILL.md').read_bytes(),(ROOT/'.claude/skills/project-kickoff/SKILL.md').read_bytes())
        self.assertEqual((ROOT/'CLAUDE.md').read_text(),'@AGENTS.md\n')
    @unittest.skipUnless(shutil.which('node'),'WordPress detectors need Node')
    def test_claude_wordpress_commands_resolve_and_run(self):
        self.install(preset_id='wordpress-plugin',harness='claude')
        (self.project/'portfolio.php').write_text('<?php\n/**\n * Plugin Name: Portfolio\n */\n')
        skill=self.project/'.claude/skills/wordpress-wp-plugin-development/SKILL.md'
        commands=re.findall(r'`node ([^`]+\.mjs)`',skill.read_text())
        self.assertEqual(len(commands),2)
        for command in commands:
            self.assertTrue((self.project/command).is_file())
            result=subprocess.run(['node',command],cwd=self.project,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report=json.loads(result.stdout)
            if 'plugins' in report:self.assertEqual(report['plugins'][0]['name'],'Portfolio')
        receipt=json.loads((self.project/'.ai-toolkit/installed.json').read_text())
        self.assertTrue(receipt['adaptations'])
        self.assertEqual(manager.check(self.project),[])
