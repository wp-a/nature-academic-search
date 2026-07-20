# 检索策略

## 从问题到查询

1. 提取研究问题的核心概念。
2. 为每个概念列出同义词、缩写和拼写变体。
3. 生物医学主题用 `lookup_mesh` 核验 MeSH 描述词。
4. 组合布尔查询，并保存未加数据库字段标签的人类可读版本。
5. 只在用户要求或范围需要时增加日期、语言和文献类型过滤。
6. 小批量测试相关性后再增加结果数；修改查询时同时报告原查询和修订查询。

## 来源选择

| 任务 | 建议来源 |
|---|---|
| 生物医学论文 | PubMed + Europe PMC + CrossRef + OpenAlex |
| 跨学科发现 | 默认五论文源 |
| CS、物理、数学预印本 | arXiv + CrossRef + OpenAlex |
| DOI/出版商元数据 | CrossRef |
| 引用图谱补充 | 显式 Semantic Scholar 搜索或强 ID 富化 |
| 试验注册 | ClinicalTrials.gov，`entity_type="trial"` |

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方；这些来源只能作为人工或机构数据库补充。

## 排序

- 默认保留各 API 相关性顺序，并说明来源。
- “最新”按可比较的发表日期排序，同时保留预印本状态。
- 引用指标排序必须选定一个来源字段；不同来源的 `citation_counts` 不相加。
- 系统综述初筛不应使用未经验证的模型自定义综合分数替代正式筛选标准。

## 去重

使用 MCP 返回的强标识符、`sources`、`source_records` 和 `conflicts`。详细规则见
[Dedup Engine](dedup-engine.md)，但实际工具输出优先于文档示例。
