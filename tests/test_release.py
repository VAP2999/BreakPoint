import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from worker.config import load_env
from worker.export import export

class ReleaseTests(unittest.TestCase):
    def test_env_is_literal_and_existing_environment_wins(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'.env';p.write_text('OPENAI_API_KEY="test-value"\nOPENAI_MODEL=$(echo untouched)\n')
            with patch.dict(os.environ,{'OPENAI_API_KEY':'existing'},clear=True):
                load_env(p)
                self.assertEqual(os.environ['OPENAI_API_KEY'],'existing')
                self.assertEqual(os.environ['OPENAI_MODEL'],'$(echo untouched)')
    def test_invalid_env_never_echoes_value(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'.env';p.write_text('OTHER=private-test-value')
            with self.assertRaises(ValueError) as error:load_env(p)
            self.assertNotIn('private-test-value',str(error.exception))
    def test_export_copies_report_without_env(self):
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)/'source';src.mkdir()
            (src/'report.json').write_text(json.dumps({'schema_version':1,'verdict':'inconclusive','phases':{}}))
            (src/'actions.json').write_text('[]');(src/'.env').write_text('private-test-value')
            dest=Path(folder)/'dest'
            export(src/'report.json',dest)
            self.assertEqual(sorted(p.name for p in dest.iterdir()),['actions.json','report.json'])
    def test_export_rejects_parent_path(self):
        with tempfile.TemporaryDirectory() as folder:
            src=Path(folder)
            (src/'report.json').write_text(json.dumps({'schema_version':1,'verdict':'confirmed','regression':'../outside.py'}))
            (src/'actions.json').write_text('[]')
            with self.assertRaises(ValueError):export(src/'report.json',src/'dest')
