# 去重与合并规则

实际实现位于统一搜索层；本页解释输出，不替代代码和测试。

## 实体命名空间

publication 与 trial 永远分开。即使题名和年份相同，也不能跨 `entity_type` 合并。

## 强标识符

在同一实体类型内，优先使用规范化标识符：

1. DOI（去掉 `https://doi.org/`，转小写）。
2. PMID、PMCID。
3. arXiv ID（去版本号）。
4. OpenAlex ID、Semantic Scholar paper ID。
5. trial 使用 NCT ID。

共享强标识符的记录可合并。标识符冲突写入 `conflicts`，不得静默覆盖。

## 弱回退

没有共享强标识符时，使用标准化题名与年份作为保守回退。年份不同或实体类型不同则保持为独立记录。
弱匹配只能帮助折叠明显重复项，不能证明引用或版本关系。

## 合并结果

- `sources`：贡献记录的来源列表。
- `source_records`：每个来源的原始 ID 与 URL。
- `conflicts`：被保留值与冲突来源值。
- `citation_counts`：按来源保存的引用次数。
- `citation_count_source`：兼容字段 `citation_count` 当前采用的来源。
- `record_id`：最终合并记录的稳定本地 ID；优先由规范化强标识符生成，没有强标识符时由
  实体类型、题名、年份和首位作者生成哈希。

不同来源的引用次数口径不能相加。代表记录保持首次结果顺序，补齐缺失字段并保留来源溯源。
