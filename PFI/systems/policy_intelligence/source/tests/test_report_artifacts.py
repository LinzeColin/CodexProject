from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from source_registry.cli import main as cli_main
from source_registry.content_db import begin_run, complete_run, connect_content, init_content_database
from source_registry.quality_gates import build_quality_gate_status
from source_registry.report_artifacts import (
    inspect_report_artifacts,
    render_report_artifact_dashboard,
    write_report_artifact_dashboard,
)


class ReportArtifactsTest(unittest.TestCase):
    def test_inspect_report_artifacts_extracts_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _write_report_fixture(Path(tmp))
            check = inspect_report_artifacts(report)
        self.assertTrue(check["report_exists"])
        self.assertEqual(check["primary_report_suffix"], ".pdf")
        self.assertGreaterEqual(check["pdf_page_count"], 10)
        self.assertEqual(check["report_document_count"], 1)
        self.assertEqual(check["deep_chapter_count"], 10)
        self.assertTrue(check["toc_present"])
        self.assertFalse(check["blank_risk"])
        self.assertGreaterEqual(check["business_value_density_score"], 95)
        self.assertGreaterEqual(check["summary"]["passed_count"], 10)

    def test_quality_gates_use_artifact_metrics_from_monitor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = _write_report_fixture(root)
            monitor = {
                "quality_gate": {"external_reference_count": 5, "external_platform_count": 2},
                "report": {"path": str(report), "exists": True},
                "latest_run": {},
            }
            status = build_quality_gate_status(monitor_status=monitor)
        rows = {item["id"]: item for item in status["gate_results"]}
        self.assertEqual(rows["single_document_scope"]["status"], "passed")
        self.assertEqual(rows["deep_analysis_chapters"]["status"], "passed")
        self.assertEqual(rows["pdf_body_pages"]["status"], "passed")
        self.assertEqual(status["summary"]["failed_count"], 0)

    def test_render_dashboard_contains_check_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = _write_report_fixture(Path(tmp))
            rendered = render_report_artifact_dashboard(inspect_report_artifacts(report))
        self.assertIn("报告产物自检 dashboard", rendered)
        self.assertIn("自检结果", rendered)
        self.assertIn("PDF 页数不少于 10", rendered)
        self.assertIn("商务高价值信息密度", rendered)
        self.assertNotIn("SESSDATA=", rendered)

    def test_reference_section_prefers_body_section_over_toc(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = _write_report_fixture(root)
            html = report.with_suffix(".html").read_text(encoding="utf-8")
            html = html.replace(
                '<nav class="toc"><a href="#doc-1">目录</a></nav>',
                '<nav class="toc"><a href="#interpretations">外部研究与解读资料来源</a>'
                '<a href="#queue">待生产研究报告队列</a></nav>',
            ).replace(
                "<h2>外部研究与解读资料来源</h2>",
                '<section id="interpretations"><h2>外部研究与解读资料来源</h2>',
            ).replace(
                "<h2>待生产研究报告队列</h2>",
                '</section><h2 id="queue">待生产研究报告队列</h2>',
            )
            report.with_suffix(".html").write_text(html, encoding="utf-8")
            check = inspect_report_artifacts(report)
        self.assertGreater(check["reference_section_char_count"], 20)

    def test_write_report_artifact_dashboard_creates_html(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = _write_report_fixture(root)
            output = root / "report_check.html"
            result = write_report_artifact_dashboard(output, report_path=report)
            self.assertEqual(result, str(output))
            self.assertTrue(output.exists())

    def test_cli_report_check_defaults_to_latest_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = _write_report_fixture(root / "reports")
            content_db = root / "policy_documents.sqlite"
            conn = connect_content(content_db)
            init_content_database(conn)
            begin_run(conn, "2026060401", "automation")
            complete_run(
                conn,
                "2026060401",
                "completed",
                str(report),
                {
                    "sources_considered": 1,
                    "pages_fetched": 1,
                    "documents_discovered": 1,
                    "new_documents": 1,
                    "analyzed_documents": 1,
                },
            )
            conn.close()
            output = root / "report_check.html"
            out = io.StringIO()
            with redirect_stdout(out):
                code = cli_main(
                    [
                        "--db",
                        str(root / "source_registry.sqlite"),
                        "report-check",
                        "--content-db",
                        str(content_db),
                        "--output",
                        str(output),
                        "--json",
                    ]
                )
            self.assertEqual(code, 0)
            payload = json.loads(out.getvalue())
            self.assertEqual(payload["dashboard_path"], str(output))
            self.assertEqual(payload["report_document_count"], 1)
            self.assertTrue(output.exists())


def _write_report_fixture(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    pdf = root / "20260604_测试政策_研究报告.pdf"
    pdf.write_bytes((b"%PDF-1.4\n" + b"/Type /Page\n" * 10 + b"0" * 2000 + b"\n%%EOF"))
    chapter_points = [
        "政策对象覆盖审批、流通、零售和监管协同，直接影响企业准入节奏与合规成本。",
        "责任主体包括监管部门、经营主体和第三方服务机构，边界清晰有助于降低执行争议。",
        "时间节点应拆分为受理、验收、整改和复核四类，便于建立项目排期和风险预警。",
        "关键条款需要映射到证照、人员、场所、系统和台账，形成可检查的落地清单。",
        "行业影响集中在连锁化、数字化和合规运营能力，弱管理主体会面临更高整改压力。",
        "地方执行差异应关注窗口口径、材料模板和现场验收标准，避免跨区域复制失真。",
        "企业应优先核验主体资质、质量负责人、经营范围和信息系统留痕，降低处罚概率。",
        "投资判断重点是监管确定性、门店扩张弹性、合规投入强度和区域政策配套。",
        "监测指标包括新办许可、变更许可、行政处罚、抽检结果和公开征求意见进展。",
        "后续跟踪应围绕配套细则、问答口径、典型案例和监管通报，动态更新报告结论。",
    ]
    chapters = "".join(
        f'<section class="deep-chapter"><h3>{index}. 章节</h3><p>{point}</p></section>'
        for index, point in enumerate(chapter_points, start=1)
    )
    html = (
        '<html><body><nav class="toc"><a href="#doc-1">目录</a></nav>'
        '<h1>中国政策文件单文件研究分析报告</h1>'
        '<p>本报告研究文件数：1</p>'
        '<h2>研究质量与交付状态</h2><p>规则化质量门槛</p>'
        '<article class="doc-card" id="doc-1">'
        f"{chapters}"
        "</article>"
        "<h2>外部研究与解读资料来源</h2><p>参考 1。参考 2。参考 3。</p>"
        "<h2>待生产研究报告队列</h2>"
        "</body></html>"
    )
    pdf.with_suffix(".html").write_text(html, encoding="utf-8")
    pdf.with_suffix(".md").write_text("# 报告\n本报告研究文件数：1\n", encoding="utf-8")
    pdf.with_name(f"{pdf.stem}_dashboard.html").write_text("<html>dashboard</html>", encoding="utf-8")
    return pdf


if __name__ == "__main__":
    unittest.main()
