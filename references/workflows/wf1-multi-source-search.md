# Workflow 1：多源文献检索

**目的：** 用稳定的 `search_papers` 工具检索、去重并报告来源状态。

## 步骤

1. 明确主题、日期、类型、结果数、预印本政策和实体类型。
2. publication 默认省略 `sources`，使用五个默认论文源；范围明确时显式传子集。
3. 需要引用图谱补充时设置 `enrich=["semantic_scholar"]`，且只富化有强标识符的记录。
4. trial 使用 `entity_type="trial"`，默认只查询 `clinicaltrials_gov`。
5. 检查 `sources_queried`、`sources_succeeded`、`sources_skipped`、`errors`、
   `raw_result_count` 与 `result_count`。
6. 查看每条记录的 `sources`、`source_records`、`conflicts` 和来源化 `citation_counts`。
7. 对关键种子记录调用 `get_paper_by_id(include_relations=true)`，默认扩展一跳；只有研究问题需要
   滚动追踪时才使用 `depth=2`，并限制 `rows`、`relation_sources`。
8. 按正式论文、预印本、trial、未解决记录分组交付；图谱另存 `graph.json`，保留每条边的
   `observed_by` 和每个来源的成功/跳过/失败状态。

## 错误处理

- 单源失败：保留其他来源结果，只重试失败来源。
- 零结果：先检查查询语法与实体类型，再提出可审计的放宽版本。
- 富化跳过：报告缺少强 ID，不做题名猜测。
- 图谱源缺失：报告 `sources_skipped` 或 `errors`，不能把未支持方向当成零引用。
- trial/publication 混用：修正实体类型和来源，不强制合并。

本项目未连接 Google Scholar、Web of Science、Scopus、Embase、CNKI、万方；需要这些来源时转人工或机构检索。
