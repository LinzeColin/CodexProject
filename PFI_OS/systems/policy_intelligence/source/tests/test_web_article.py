from __future__ import annotations

import unittest

from source_registry.web_article import extract_article_text


class WebArticleTest(unittest.TestCase):
    def test_extracts_readable_article_body(self) -> None:
        extraction = extract_article_text(
            """
            <html>
              <head><title>政策研究文章</title></head>
              <body>
                <nav>导航不应进入正文</nav>
                <article>
                  <h1>人工智能政策解读</h1>
                  <p>本文围绕人工智能政策文件，分析产业影响、监管要求和企业机会。</p>
                  <p>政策执行需要关注算力、数据、模型、安全评估和地方配套细则。</p>
                  <p>同时需要比较中央部门、地方政府、行业协会和公开研究机构的观点，识别政策工具、预算安排、项目申报、合规成本和产业链传导节奏。</p>
                </article>
              </body>
            </html>
            """
        )
        self.assertEqual(extraction.status, "article_excerpt_extracted")
        self.assertEqual(extraction.title, "政策研究文章")
        self.assertIn("人工智能政策解读", extraction.text)
        self.assertNotIn("导航", extraction.text)

    def test_detects_captcha_or_paywall_without_excerpt(self) -> None:
        captcha = extract_article_text("<html><body>请完成验证码 安全验证</body></html>")
        paywall = extract_article_text("<html><body>这是一篇会员专享文章，付费阅读后查看。</body></html>")
        self.assertEqual(captcha.status, "article_fetch_blocked:captcha")
        self.assertEqual(paywall.status, "article_fetch_blocked:paywall")


if __name__ == "__main__":
    unittest.main()
