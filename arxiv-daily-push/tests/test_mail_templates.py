from __future__ import annotations

import unittest
from urllib.parse import unquote, urlparse

from arxiv_daily_push.mail_templates import (
    EMAIL_LEARNING_V1_CONTRACT_ID,
    EMAIL_LEARNING_V1_TEMPLATE_MARKER,
    EMAIL_LEARNING_V1_TEMPLATE_VERSION,
    FORBIDDEN_VISIBLE_MARKERS,
    M1_M4_MAIL_PRODUCTS,
    render_email_learning_v1,
)


GENERATED_AT = "2026-07-01T05:00:00+10:00"


def arxiv_source(stable_id: str, title: str, summary: str, primary: str = "cs.AI") -> dict:
    return {
        "source_id": f"arxiv:{stable_id}",
        "source_type": "arxiv",
        "source_adapter": "arxiv.atom.v1",
        "stable_id": stable_id,
        "title": title,
        "canonical_url": f"https://arxiv.org/abs/{stable_id}",
        "metadata": {
            "arxiv": {
                "summary": summary,
                "primary_category": primary,
                "categories": [primary],
                "authors": ["Ada Example"],
            }
        },
        "content_refs": [{"ref_type": "abstract", "uri": f"https://arxiv.org/abs/{stable_id}"}],
    }


def lesson_with_forbidden_frontstage() -> dict:
    return {
        "language": "zh-CN",
        "frontstage": {
            "first_principles_chain": ["问题定义", "ROI评分", "可观察输出", "失败条件"],
            "domain_mappings": [
                {
                    "paper_variable": "ROI score",
                    "decision_mapping": "不要把 Release 资料包、GitHub Release 或 12秒视频当阅读入口",
                }
            ],
            "evidence_gaps": ["不要把 delivery policy 或 roi_total_score 当正文重点。"],
        },
    }


class MailTemplateTests(unittest.TestCase):
    def test_m1_m4_all_render_email_learning_v1_with_required_links(self) -> None:
        source = arxiv_source(
            "2607.00001",
            "Agent benchmark for portfolio risk automation",
            "A benchmark dataset evaluates agent decisions under market risk and portfolio constraints.",
            "q-fin.PM",
        )

        for mail_product_id in M1_M4_MAIL_PRODUCTS:
            with self.subTest(mail_product_id=mail_product_id):
                rendered = render_email_learning_v1(
                    mail_product_id=mail_product_id,
                    source_item=source,
                    lesson=lesson_with_forbidden_frontstage(),
                    claims=[
                        {
                            "statement": "The abstract reports a benchmark for agent decisions under market risk.",
                            "support_status": "supported",
                        }
                    ],
                    generated_at=GENERATED_AT,
                    date="2026-07-01",
                    run_id="run-email-v1-test",
                    report_id="report-email-v1-test",
                    candidate_queue_summary="已入队候选：1 篇。",
                    queue_items=[
                        {
                            "title": "Market risk simulation benchmark for agent trading",
                            "primary_category": "cs.AI",
                            "reason": "跨域候选，具备可迁移方法或验证价值",
                        }
                    ],
                )

                self.assertEqual(rendered["contract_id"], EMAIL_LEARNING_V1_CONTRACT_ID)
                self.assertEqual(rendered["template_version"], EMAIL_LEARNING_V1_TEMPLATE_VERSION)
                self.assertEqual(rendered["mail_product_id"], mail_product_id)
                self.assertRegex(rendered["subject"], rf"^20260701 -- arXiv Daily Push -- {mail_product_id} -- .+")
                self.assertIn("先把论文讲成人话", rendered["plain"])
                self.assertIn("学习成果导航", rendered["plain"])
                self.assertIn("真正的新知识", rendered["plain"])
                self.assertIn("候选队列摘要", rendered["plain"])
                self.assertIn(EMAIL_LEARNING_V1_TEMPLATE_MARKER, rendered["html"])

                links = rendered["content"]["links"]
                self.assertEqual(links["arxiv_link"], "https://arxiv.org/abs/2607.00001")
                self.assertEqual(links["pdf_link"], "https://arxiv.org/pdf/2607.00001")
                self.assertTrue(links["chatgpt_new_chat"].startswith("https://chatgpt.com/?q="))
                decoded_prompt = unquote(urlparse(links["chatgpt_new_chat"]).query.removeprefix("q="))
                self.assertIn("https://arxiv.org/abs/2607.00001", decoded_prompt)
                self.assertIn("只有高中理科基础", decoded_prompt)

                visible = rendered["plain"] + "\n" + rendered["html"]
                for marker in FORBIDDEN_VISIBLE_MARKERS:
                    self.assertNotIn(marker, visible)

    def test_render_is_specific_to_source_content_and_escapes_html(self) -> None:
        sources = [
            arxiv_source(
                "2607.00002",
                "Portfolio risk automation <script>alert(1)</script>",
                "A market risk framework with explicit evaluation conditions.",
                "q-fin.RM",
            ),
            arxiv_source(
                "2607.00003",
                "Microscopy image generation for semiconductor inspection",
                "A diffusion image dataset improves inspection of tiny defects.",
                "cs.CV",
            ),
            arxiv_source(
                "2607.00004",
                "Control benchmark for energy optimization",
                "A control benchmark evaluates energy systems under operational constraints.",
                "eess.SY",
            ),
        ]

        rendered = [
            render_email_learning_v1(
                mail_product_id="M1",
                source_item=source,
                lesson={"language": "zh-CN"},
                claims=[],
                generated_at=GENERATED_AT,
                date="2026-07-01",
                run_id=f"run-{index}",
            )
            for index, source in enumerate(sources, start=1)
        ]

        titles = {item["content"]["title_zh_plain"] for item in rendered}
        self.assertGreaterEqual(len(titles), 3)
        self.assertNotEqual(rendered[0]["plain"], rendered[1]["plain"])
        self.assertNotIn("<script>alert(1)</script>", rendered[0]["html"])
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rendered[0]["html"])


if __name__ == "__main__":
    unittest.main()
