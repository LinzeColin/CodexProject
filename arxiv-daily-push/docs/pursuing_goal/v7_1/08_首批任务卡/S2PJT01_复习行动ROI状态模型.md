# Task Card：S2PJT01 复习、行动和 ROI 状态模型

## 唯一目标

在 SQLite 中加入可回滚的学习生命周期，不先实现复杂算法。

## 必需实体

ReviewRecord、ActionPlan、CapabilityAsset、ROIExpectation、ConversionEvent、FeedbackRecord。

## 必需状态

REVIEW_DUE、REVIEWED、ACTION_PLANNED、ACTION_COMPLETED、ASSET_CREATED、CONVERSION_RECORDED、MASTERED。

## Stop Gate

迁移前进/回滚、状态历史、计数守恒和旧内容兼容测试通过。
