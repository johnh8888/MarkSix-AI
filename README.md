# MarkSix AI V3.2

统一后的模块化版本。

## 工作流

同步历史 → 实时同步 → 数据清洗 → 状态识别 → 动态模块权重 → 号码评分 → Top10/重点3码 → 生肖5肖/平特2肖 → 大小/单双 → 波色单推/双推 → Walk-Forward 最近10/20期 → JSON。

## 已修复

- `config.py` 补齐 `SHORT_WINDOW / MEDIUM_WINDOW / LONG_WINDOW`
- `database.py` 统一提供 `init_database()`、`connect_db()`、`init_db()`
- 所有 core 模块导入接口统一
- Walk-Forward 使用 `目标期 rows[i] + 训练 rows[i+1:]`，严格避免未来数据泄漏
- 删除30/60/100期回测输出，只保留10/20期
- 波色保留单推与双推，并计算双推提升
- 模型评分与内部相对分布分开，不把评分当真实中奖概率
- GitHub Actions 先 compile/import，再运行主程序

> 彩票开奖结果具有随机性。历史回测不能保证未来结果，仅用于统计研究。
