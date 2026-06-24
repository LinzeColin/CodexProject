from __future__ import annotations
import json, subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
 def test_validator_passes(self):
  p=subprocess.run([sys.executable,str(ROOT/'tools/validate_task_pack.py'),'--root',str(ROOT)],capture_output=True,text=True)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr)
 def test_probe_evidence_is_explicitly_limited(self):
  d=json.loads((ROOT/'evidence/probe_results_v7_1.json').read_text(encoding='utf-8'))
  self.assertIn('not a full repository test run',d['scope'])
  self.assertGreaterEqual(d['summary']['failed'],1)
 def test_unique_next_task(self):
  s=(ROOT/'HANDOFF/00_下一Agent先读.md').read_text(encoding='utf-8')
  self.assertIn('S2PAT05',s)
if __name__=='__main__': unittest.main()
