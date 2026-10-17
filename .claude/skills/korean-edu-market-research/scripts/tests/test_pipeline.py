"""pipeline.py 회귀 테스트. 합성 픽스처(example.com)로 등급 규칙과 판정을 확인한다.

실행: python3 -m unittest discover -s .claude/skills/korean-edu-market-research/scripts/tests
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent / "pipeline.py"
FIXTURE = HERE / "fixture"


def run(*args):
    return subprocess.run([sys.executable, str(PIPELINE), *args], capture_output=True, text=True)


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run_dir = self.tmp / "run"
        shutil.copytree(FIXTURE, self.run_dir)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def merged(self):
        result = run("merge", str(self.run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        findings = json.loads((self.run_dir / "findings.json").read_text(encoding="utf-8"))
        return findings, {c["id"]: c for c in findings["competitors"]}

    def test_validate_flags_schema_violation(self):
        self.assertEqual(run("validate", str(self.run_dir / "raw" / "c1.json")).returncode, 0)
        bad = run("validate", str(self.run_dir / "raw" / "c8.json"))
        self.assertEqual(bad.returncode, 1)
        self.assertIn("필수 필드 없음", bad.stdout)

    def test_grading_rules(self):
        findings, c = self.merged()
        self.assertEqual(c["c1"]["confidence"], "A")
        self.assertEqual(c["c2"]["confidence"], "B")  # 시수 추정
        self.assertIn("hours_estimated", c["c2"]["flags"])
        self.assertEqual(c["c3"]["confidence"], "B")  # 보도자료
        self.assertEqual(c["c4"]["confidence"], "C")  # 2013년 소스
        self.assertIn("stale", c["c4"]["flags"])
        self.assertEqual(c["c4"]["section"], "appendix")
        self.assertEqual(c["c5"]["section"], "appendix")  # 스니펫, 날짜 불명, 시수 없음
        self.assertIn("pph_unavailable", c["c5"]["flags"])
        excluded = {e["name"] for e in findings["excluded"]}
        self.assertIn("테스트 기관 7", excluded)  # 출처 없음
        self.assertIn("테스트 기관 8", excluded)  # 스키마 위반

    def test_price_per_hour_recomputed(self):
        _, c = self.merged()
        self.assertEqual(c["c1"]["price_per_hour_krw"], 7500)
        self.assertEqual(c["c3"]["price_per_hour_krw"], 7000)  # 80 USD × 1400 ÷ 16h
        self.assertIn("pph_recomputed", c["c3"]["flags"])
        self.assertEqual(c["c6"]["price_per_hour_krw"], 0)

    def test_stats(self):
        findings, _ = self.merged()
        s = findings["stats"]
        self.assertEqual(s["body_count"], 4)  # c1, c2, c3, c6
        self.assertEqual(s["total_candidates_analyzed"], 8)
        self.assertEqual(s["verified_ratio"], 0.5)
        self.assertEqual(s["free_count"], 1)
        self.assertEqual(s["pph_median"], 7500)  # 유료 7000, 7500, 20000
        self.assertEqual(s["topik_guarantee_count"], 1)

    def test_render_and_check(self):
        self.merged()
        render = run("render", str(self.run_dir))
        self.assertEqual(render.returncode, 0, render.stderr)
        report = (self.run_dir / "report.md").read_text(encoding="utf-8")
        dashboard = (self.run_dir / "dashboard.html").read_text(encoding="utf-8")
        self.assertIn("경쟁사 자동 선정됨 — 검토 필요", report)
        self.assertIn("완료 판정 미통과", report)  # 출처 확인 비율 50%
        self.assertNotIn("__DATA_JSON__", dashboard)
        self.assertIn("테스트 기관 1", dashboard)
        # 본문 비교표에 C등급이 섞이지 않는다
        table = report.split("## 경쟁사 비교표")[1].split("## 경쟁사 팩트시트")[0]
        self.assertNotIn("테스트 기관 4", table)
        self.assertNotIn("테스트 기관 5", table)
        check = run("check", str(self.run_dir))
        self.assertEqual(check.returncode, 1)
        self.assertIn("[FAIL] 출처 확인 비율", check.stdout)
        self.assertIn("[PASS] 18개월", check.stdout)

    def test_check_passes_when_ratio_met(self):
        for name in ("c4.json", "c5.json", "c7.json", "c8.json"):
            (self.run_dir / "raw" / name).unlink()
        self.merged()
        run("render", str(self.run_dir))
        check = run("check", str(self.run_dir))
        self.assertEqual(check.returncode, 0, check.stdout)

    def test_analysis_refs_must_point_to_body(self):
        analysis_path = self.run_dir / "analysis.json"
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        analysis["gaps"][0]["refs"] = ["c4"]  # 부록 항목
        analysis_path.write_text(json.dumps(analysis, ensure_ascii=False), encoding="utf-8")
        for name in ("c5.json", "c7.json", "c8.json"):
            (self.run_dir / "raw" / name).unlink()
        self.merged()
        run("render", str(self.run_dir))
        check = run("check", str(self.run_dir))
        self.assertEqual(check.returncode, 1)
        self.assertIn("부록(C등급) 항목", check.stdout)


if __name__ == "__main__":
    unittest.main()
