from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


BASE_FILES = {
    "功能清单": ["中文可读评分", "第一眼结论", "当前速读", "用户第一眼应看到的信息", "已实现功能", "明确禁止或尚未完成"],
    "开发记录": ["中文可读评分", "第一眼结论", "当前速读", "安全边界", "当前运行路线", "近期开发事件"],
    "模型参数文件": ["中文可读评分", "第一眼结论", "当前速读", "模型总览", "公式逻辑", "参数表", "Owner 需要关注的参数"],
}


def _chinese_ratio(text: str) -> float:
    meaningful = [char for char in text if not char.isspace()]
    chinese = [char for char in meaningful if "\u4e00" <= char <= "\u9fff"]
    return len(chinese) / len(meaningful)


def test_owner_base_files_use_exact_contract_paths_and_are_chinese():
    for filename, required_sections in BASE_FILES.items():
        exact_path = PROJECT_ROOT / filename
        legacy_md_path = PROJECT_ROOT / f"{filename}.md"

        assert exact_path.exists(), f"缺少三基文件精确路径：{exact_path}"
        assert not legacy_md_path.exists(), f"三基文件不能只落在 .md 旧路径：{legacy_md_path}"

        text = exact_path.read_text(encoding="utf-8")
        assert _chinese_ratio(text) >= 0.30, f"{filename} 中文占比不足"
        assert "中文可读评分: `100/100`" in text, f"{filename} 缺少中文可读评分"
        assert "不能" in text, f"{filename} 必须明确中文安全限制"
        for section in required_sections:
            assert section in text, f"{filename} 缺少关键中文章节：{section}"
