"""根 README 基础设施路牌守卫。

本仓是**公开仓**。README 里放了指向本机 `_protected/` 配置总册的「路牌」,
方便接手者(含 ChatGPT/Codex 这类容易乱猜的助手)找到正确入口。

这个守卫做两件事:
1. 正控:路牌区块与三份指引文件的路径必须在,否则接手者会重新乱猜。
2. **负控(更重要)**:README 里绝不允许出现凭据或源站 IP。
   站点都在 Cloudflare 后面,一旦把源站 IP 写进公开仓,等于废掉源站隐藏;
   token/私钥同理,进了公开仓就是泄露。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"

REQUIRED_MARKERS = (
    "基础设施路牌",
    "_protected/alpha_deploy_private/INFRA_CONFIG.md",
    "_protected/alpha_deploy_private/HANDOVER_PROMPT_FOR_CODEX.md",
)

# 禁止出现的东西(公开仓红线)
FORBIDDEN_PATTERNS = (
    (r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "裸 IPv4 地址(源站 IP 会废掉 Cloudflare 源站隐藏)"),
    (r"github_pat_[A-Za-z0-9_]{20,}", "GitHub fine-grained PAT"),
    (r"\bghp_[A-Za-z0-9]{20,}", "GitHub classic PAT"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "私钥内容"),
    (r"\bcfut_[A-Za-z0-9]{20,}", "Cloudflare 用户令牌"),
    (r"(?i)\b(password|passwd|secret|api[_-]?key)\s*[:=]\s*\S+", "内联凭据赋值"),
)

# 版本号之类的点分数字不是 IP;这里只放明确安全的白名单片段
IP_WHITELIST = (
    "0.0.0.0",      # 说明性绑定地址
    "127.0.0.1",    # 本机回环
)


class ReadmeInfraSignpostTest(unittest.TestCase):
    def setUp(self):
        self.text = README.read_text(encoding="utf-8")

    def test_signpost_section_present(self):
        for marker in REQUIRED_MARKERS:
            self.assertIn(
                marker, self.text,
                f"根 README 缺少基础设施路牌要素:{marker}。接手者会因此找不到配置总册。")

    def test_no_credentials_or_origin_ip(self):
        for pattern, label in FORBIDDEN_PATTERNS:
            for m in re.finditer(pattern, self.text):
                hit = m.group(0)
                if pattern.startswith(r"\b(?:\d{1,3}\.)") and hit in IP_WHITELIST:
                    continue
                self.fail(f"根 README(公开仓)出现禁止内容 [{label}]:{hit!r}")

    def test_secrets_live_outside_repo(self):
        """路牌必须明确写出「凭据不进本仓」这条边界,而不是只给路径。"""
        self.assertRegex(
            self.text, r"(永不 commit|不得写进来|不得出现)",
            "路牌必须写明凭据不得进入公开仓的硬性边界。")


if __name__ == "__main__":
    unittest.main()
