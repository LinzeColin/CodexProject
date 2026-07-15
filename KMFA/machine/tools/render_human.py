#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_human.py —— 人类平面渲染器 / 血缘前置门（第三道门）

职责（v1.5 阶段一，骨架）：
  人类平面 文档/ 里除 01_产品需求.md 和 03_口径字典.md（Owner 手写区）外，
  其余 5 个文件都是**渲染产物**，必须由本脚本从机器平面 machine/facts/ 生成。
  在真正渲染之前，本脚本先当"血缘前置门"用：
    - 每个渲染目标声明它依赖哪些事实源；
    - 事实源缺失 → 源优先级链第 1 环未接通 → 本次渲染 FAIL，不写任何文件。

为什么现在必须 FAIL：
  machine/facts/ 目前为空（真实数据尚未只读扫描、抽取、落盘）。
  第 1 环 raw_uploaded_or_authorized_export 未接通，lineage_complete 恒为 false。
  绿的门是假门 —— 只有当事实源齐备且渲染真实产出时，本门才允许变绿。

用法:  python3 machine/tools/render_human.py [--docs 文档] [--machine machine]
退出码: 0=PASS（已渲染 / 事实齐备）  1=FAIL（缺事实源，或渲染逻辑尚未接入）
"""
import argparse
import sys
from pathlib import Path

# Owner 手写区：渲染器只读，永不覆盖。
HANDWRITTEN = {"01_产品需求.md", "03_口径字典.md"}

# 渲染目标 -> 依赖的事实源（相对 machine/）。
# 与各文件头部注释里声明的"事实源"保持一致。
RENDER_TARGETS = {
    "00_我在哪.md": ["facts/status.json", "facts/blockers.json"],
    "02_系统架构.md": ["facts/features.json", "data_contract.yaml", "config.yaml"],
    "04_操作流程.md": ["facts/flows.json"],
    "05_执行与验收.md": ["facts/plan.json", "facts/acceptance.json"],
    "06_运维手册.md": ["config.yaml", "facts/ops.json", "facts/changelog.json"],
}


def missing_sources(machine: Path, sources: list) -> list:
    """返回缺失或为空的事实源列表。"""
    missing = []
    for rel in sources:
        f = machine / rel
        if not f.exists() or f.stat().st_size == 0:
            missing.append(rel)
    return missing


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="文档")
    ap.add_argument("--machine", default="machine")
    args = ap.parse_args()
    docs = Path(args.docs)
    machine = Path(args.machine)

    failures = []

    if not machine.is_dir():
        print(f"FAIL: 找不到机器平面目录 {machine}")
        return 1

    # 逐个渲染目标核对事实源。
    renderable = []
    for name, sources in RENDER_TARGETS.items():
        miss = missing_sources(machine, sources)
        if miss:
            failures.append(
                f"[血缘前置门] {name}: 事实源缺失 {miss}。"
                f"去接通源优先级链第 1 环，把真实数据落盘到 machine/facts/。"
            )
        else:
            renderable.append(name)

    if failures:
        print(f"FAIL —— {len(failures)} 个渲染目标缺事实源（人类平面尚未被渲染）\n")
        for x in failures:
            print("  ✗ " + x)
        print(
            "\n  说明：01_产品需求.md 与 03_口径字典.md 是 Owner 手写区，不在此门内；"
            "其余 5 个文件必须从 machine/facts/ 渲染。当前 facts/ 为空 -> 本门红。"
        )
        return 1

    # 事实源齐备（阶段二之后才会到这里）：真正的渲染逻辑在阶段二接入。
    # 阶段一骨架故意不实现渲染写盘 —— 未实现即不许变绿。
    print(
        "FAIL —— 事实源已齐备，但渲染写盘逻辑尚未接入（阶段二）。\n"
        f"  待渲染目标: {renderable}\n"
        "  在阶段二实现 machine/facts/ -> 文档/ 的字段级渲染后，本门方可变绿。"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
