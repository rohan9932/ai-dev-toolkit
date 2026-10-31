"""Behavior checks for the reviewed, read-only WordPress detectors."""
import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import toolkit_lib
import jsonschema

@unittest.skipUnless(shutil.which('node'),'Node is needed for WordPress detectors')
class DetectorTests(unittest.TestCase):
    def setUp(self):
        test_root=ROOT/'.local/test-runs';test_root.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(prefix='toolkit-detector-',dir=test_root);self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name)
    def run_detector(self,skill,script):
        path=ROOT/'library/community/wordpress'/('wordpress-'+skill)/'scripts'/script
        result=subprocess.run(['node',str(path)],cwd=self.project,capture_output=True,text=True,check=True)
        return json.loads(result.stdout)
    def test_plugin_detection_ignores_installed_skill_examples(self):
        source='<?php\n/**\n * Plugin Name: Test Registration\n * Version: 1.0.0\n */\n'
        (self.project/'plugin.php').write_text(source)
        for directory in ('.agents','.claude'):
            nested=self.project/directory/'skills/example';nested.mkdir(parents=True)
            (nested/'example.php').write_text(source.replace('Test Registration','Example to ignore'))
        report=self.run_detector('wp-plugin-development','detect_plugins.mjs')
        self.assertEqual(report['count'],1);self.assertEqual(report['plugins'][0]['name'],'Test Registration')
        report=self.run_detector('wp-project-triage','detect_wp_project.mjs')
        self.assertIn('wp-plugin',report['project']['kind'])
        schema=json.loads((ROOT/'library/community/wordpress/wordpress-wp-project-triage/references/triage.schema.json').read_text())
        jsonschema.validate(report,schema)
    def test_block_theme_detection_and_empty_project_schema(self):
        report=self.run_detector('wp-project-triage','detect_wp_project.mjs')
        schema=json.loads((ROOT/'library/community/wordpress/wordpress-wp-project-triage/references/triage.schema.json').read_text())
        jsonschema.validate(report,schema)
        (self.project/'theme.json').write_text('{"version":3}')
        (self.project/'templates').mkdir();(self.project/'templates/index.html').write_text('<!-- wp:post-content /-->')
        (self.project/'style.css').write_text('/*\nTheme Name: Test Theme\n*/')
        for directory in ('.agents','.claude'):
            nested=self.project/directory/'skills/example-theme';nested.mkdir(parents=True)
            (nested/'style.css').write_text('/*\nTheme Name: Example to ignore\n*/')
            (nested/'theme.json').write_text('{"version":3}')
        report=self.run_detector('wp-block-themes','detect_block_themes.mjs')
        self.assertEqual(report['count'],1);self.assertTrue(report['themes'][0]['isBlockTheme'])
        report=self.run_detector('wp-project-triage','detect_wp_project.mjs')
        self.assertIn('wp-block-theme',report['project']['kind']);jsonschema.validate(report,schema)
