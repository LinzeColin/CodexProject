# 测试策略与发布证据

## 测试金字塔

1. **目录/Schema/配置静态测试**：ID 唯一、引用完整、范围、公式、参数、阈值和品牌策略。
2. **单元测试**：实体解析、评分、时间衰减、金额归一、证据状态、图预算。
3. **契约测试**：OpenAPI、事件 Schema、数据库迁移、配置版本。
4. **集成测试**：采集→证据→事实→图查询→评分→快照。
5. **浏览器 E2E**：递归切换、筛选、证据、模型预览/发布/回滚、保存与深链。
6. **非功能测试**：安全、并发、压力、soak、可访问性、视觉回归、备份恢复。

## v5 可执行命令

以下三组必须在独立 OS/CI Job 中执行，不能由一个长生命周期 shell 串联：

```bash
# Job 1：静态与治理
python3 scripts/build_prototype_bundle.py
python3 scripts/generate_package_metadata.py
bash scripts/preflight.sh

# Job 2：浏览器行为、韧性、极限交互与视觉覆盖
bash scripts/run_browser_validation_suite.sh

# Job 3：自主运行器生命周期
bash scripts/test_autonomous_runner_lifecycle.sh
```

浏览器 Job 内部会执行 smoke、stored-XSS/畸形状态、数据集隔离、60 次主体切换、12 次模型发布竞态、键盘关系激活、状态 round-trip 和三视口视觉覆盖。

## 生产性能门槛（待 Phase 0 ADR 最终冻结）

- 常用一跳子图 API P95 <= 800ms，二跳受限查询 P95 <= 2.5s。
- 首次可交互 <= 2.5s（标准研究工作站），交互反馈 <= 100ms。
- 主动画目标 60fps；不得连续出现 >50ms 长任务。
- 单次工作区可见关系默认 <= 40；超额必须聚合或渐进加载。
- 后台任务必须有 lease、幂等键、heartbeat、重试上限和 dead-letter。
- 任何模型发布必须产生唯一 config_version，并能在跨视图一致性测试中通过。

## 测试证据规则

“通过”必须关联命令、时间、环境、输出、Acceptance ID 和相关 commit。截图不能替代结果有效性断言；视觉覆盖率不能替代可用性测试。

## 浏览器测试稳定性

`run_browser_validation_suite.py` 在单个 Chromium 中以隔离 Context 执行 smoke、韧性和视觉覆盖断言；`run_browser_validation_suite.sh` 使用独立 session、PASS sentinel、硬超时和进程组清理，防止 Chromium/Playwright/crashpad 子进程在解释器关闭阶段占用 CI 管道。断言失败不会被重试或掩盖。


## 进程树隔离规则

静态 preflight、浏览器验证和自主 runner 生命周期必须作为三个独立 OS/CI Job 运行。浏览器 Job 由 `run_browser_validation_suite.sh` 监督独立 session 并清理 Playwright/Chromium/crashpad 进程组；runner Job 单独验证锁、检查点、原子输出和缓存清理。分离执行避免两个高进程活动测试共享描述符或互相污染退出状态。
