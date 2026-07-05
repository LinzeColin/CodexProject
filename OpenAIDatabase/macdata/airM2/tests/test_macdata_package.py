# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'run_controlled_cycle.py'
spec = importlib.util.spec_from_file_location('macdata_cycle', SCRIPT)
macdata_cycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(macdata_cycle)  # type: ignore


class MacDataPackageTests(unittest.TestCase):
    def test_secret_scanner_blocks_common_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'bad.txt'
            fake_secret = 'OPENAI_' + 'API_KEY=' + 'sk-' + 'abcdefghijklmnopqrstuvwxyz123456'
            p.write_text(fake_secret, encoding='utf-8')
            ok, findings = macdata_cycle.scan_for_secrets([p])
            self.assertFalse(ok)
            self.assertTrue(findings)

    def test_chinese_report_contains_required_sections(self):
        config = json.loads((ROOT / 'config' / 'device_config.json').read_text(encoding='utf-8'))
        metrics = {
            'run_id': f'{config["device_key"]}-test',
            'collected_at_local': '2026-07-05T01:10:00+10:00',
            'hardware': {'model_name': config['device_label_cn'], 'chip_type': ','.join(config['expected_chip_keywords']), 'physical_memory_text': '32 GB' if config['device_key'].startswith('pro') else '8 GB'},
            'pmset': {},
            'storage': {'root_total_gb': 1000, 'root_used_gb': 500, 'root_free_gb': 500, 'root_percent_used': 50},
            'memory': {'physical_memory_gb': 32, 'swap_used_gb': 0.5, 'vm_stat_summary': 'ok'},
            'top_processes': {},
            'git': {},
            'sizes': {},
            'docker': {},
            'brew': {},
            'air_remote_readiness': {},
            'risk': {'storage_level': '绿色', 'swap_level': '绿色', 'battery_capacity_level': '绿色', 'overall_level': '绿色'},
        }
        report = macdata_cycle.render_cn_report(metrics, config)
        self.assertIn('每日明文健康报告', report)
        self.assertIn('收益与 ROI 明文分析', report)
        self.assertIn('优势、劣势、机会、威胁', report)
        self.assertIn('Time Machine：本任务不采集', report)
        self.assertIn('iCloud：本任务不使用', report)

    def test_retention_deletes_only_old_date_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            today = dt.datetime.now().astimezone().date()
            old = today - dt.timedelta(days=5)
            keep = today - dt.timedelta(days=1)
            (base / old.isoformat()).mkdir()
            (base / old.isoformat() / 'x.txt').write_text('x', encoding='utf-8')
            (base / keep.isoformat()).mkdir()
            (base / keep.isoformat() / 'y.txt').write_text('y', encoding='utf-8')
            (base / 'not-a-date').mkdir()
            result = macdata_cycle.cleanup_retention([base], 3, dry_run=False)
            self.assertFalse((base / old.isoformat()).exists())
            self.assertTrue((base / keep.isoformat()).exists())
            self.assertTrue((base / 'not-a-date').exists())
            self.assertGreaterEqual(result['deleted_dirs'], 1)

    def test_project_cache_cleanup_is_bounded(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            cache = repo / 'pkg' / '__pycache__'
            git_dir = repo / '.git' / '__pycache__'
            cache.mkdir(parents=True)
            git_dir.mkdir(parents=True)
            (cache / 'x.pyc').write_text('x', encoding='utf-8')
            (git_dir / 'keep.pyc').write_text('x', encoding='utf-8')
            config = {
                'controlled_development_cleanup': {
                    'project_cache_names': ['__pycache__'],
                    'project_cache_max_deleted_paths': 20,
                }
            }
            result = macdata_cycle.cleanup_project_cache_targets(repo, config)
            self.assertFalse(cache.exists())
            self.assertTrue(git_dir.exists())
            self.assertEqual(result['status'], '已执行项目缓存清理')


if __name__ == '__main__':
    unittest.main()
