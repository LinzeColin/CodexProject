"""零 Agent 依赖 / 零 Token 消耗 —— 运行期守卫。

`docs/governance/STANDARD.md` 规定:运行期代码不得调用任何推理接口,系统必须能在没有 agent、
没有模型调用的情况下自己跑下去。规则只写在文档里会随时间被冲淡,这里让它可被机器判定。

守卫做两件事:
1. 契约在位:`docs/governance/STANDARD.md` 必须保留这条规则(防止被整段删掉)。
2. **负控**:扫描仓内**运行期**源码,禁止出现推理接口调用。
   只扫会真正跑起来的代码,跳过文档、测试、治理证据、依赖与缓存目录 ——
   否则本文件里的字面量自己就会把守卫打红。
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "docs" / "governance" / "STANDARD.md"   # AGENTS.md 有 4KB 预算,细则按其指引落在 STANDARD.md

REQUIRED_MARKERS = (
    "零 Agent 依赖",
    "运行期禁止调用任何推理接口",
    "数据靠派生,不靠生成",
)

# 运行期推理接口特征。用拼接构造,避免本文件自身被同类扫描器误判。
BANNED = [
    (re.compile(r"api\." + r"openai\.com", re.I), "OpenAI 接口"),
    (re.compile(r"api\." + r"anthropic\.com", re.I), "Anthropic 接口"),
    (re.compile(r"generativelanguage\." + r"googleapis\.com", re.I), "Gemini 接口"),
    (re.compile(r"api\." + r"cohere\.ai", re.I), "Cohere 接口"),
    (re.compile(r"api\." + r"mistral\.ai", re.I), "Mistral 接口"),
]

CODE_SUFFIXES = {".py", ".js", ".mjs", ".ts", ".tsx", ".sh", ".yaml", ".yml"}

# 跳过:文档、测试、治理证据、依赖、缓存、归档。这些不是运行期代码。
SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv",
    "tests", "docs", "governance", "archive", "Archive", ".github",
    "vendor", "data", "evidence", "fixtures", "_protected",
}

# **显式白名单:开发期 agent 工具**。
# 契约允许 agent 存在于开发期,只禁止它成为运行期的必要零件。
# 这些脚本由 pull_request / workflow_dispatch / schedule 触发,**不进任何生产镜像**
# (已核:无 Dockerfile / compose 引用),因此允许调用推理接口。
# 做成白名单而不是静默跳过 —— 想加新的例外必须改这里,会被 review 看见。
DEV_TIME_ALLOWLIST = {
    "scripts/agent_loop",
}


def is_dev_time(rel: Path) -> bool:
    posix = rel.as_posix()
    return any(posix == a or posix.startswith(a + "/") for a in DEV_TIME_ALLOWLIST)


def iter_runtime_files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix not in CODE_SUFFIXES:
            continue
        rel = p.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if is_dev_time(rel):
            continue
        yield p


class ZeroAgentRuntimeTest(unittest.TestCase):
    def test_contract_present(self):
        self.assertTrue(CONTRACT.exists(), "STANDARD.md 不存在")
        text = CONTRACT.read_text(encoding="utf-8")
        for marker in REQUIRED_MARKERS:
            self.assertIn(
                marker, text,
                f"STANDARD.md 缺少零 Agent/零 Token 契约要素:{marker}。"
                "这条规则被删掉,后来的 agent 就会把模型调用写进运行期。")

    def test_no_inference_api_in_runtime_code(self):
        hits = []
        for path in iter_runtime_files():
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern, label in BANNED:
                if pattern.search(text):
                    hits.append(f"{path.relative_to(ROOT)} -> {label}")
                    break
        self.assertEqual(
            hits, [],
            "运行期代码出现推理接口调用,违反零 Token 契约:\n  " + "\n  ".join(hits) +
            "\n如果这确实是开发期工具(不进生产镜像),把它加进 DEV_TIME_ALLOWLIST 并说明理由。")

    def test_allowlist_paths_still_exist(self):
        """白名单指向的目录若已消失,应清理白名单,避免它变成无人看管的口子。"""
        for a in DEV_TIME_ALLOWLIST:
            self.assertTrue((ROOT / a).exists(),
                            f"白名单项 {a} 已不存在,请从 DEV_TIME_ALLOWLIST 移除")


if __name__ == "__main__":
    unittest.main()
