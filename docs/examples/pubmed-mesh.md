# PubMed / MeSH：先核对主题词，再组合检索式

**实测日期：** 2026-07-31（Asia/Shanghai）  
**工具版本：** Academic Paper Search 0.2.0  
**查询词：** `Artificial Intelligence`、`Education, Medical`

## NCBI MeSH 真实返回

```yaml
- input: Artificial Intelligence
  descriptors:
    - name: Artificial Intelligence
      mesh_id: D001185
    - name: Generative Artificial Intelligence
      mesh_id: D000098842
- input: Education, Medical
  descriptors:
    - name: Education, Medical
      mesh_id: D004501
```

## 基于词表结果构造的起始检索式

```text
("Artificial Intelligence"[MeSH Terms]
 OR "Generative Artificial Intelligence"[MeSH Terms])
AND "Education, Medical"[MeSH Terms]
```

MeSH lookup returned the descriptors and IDs above. The Boolean expression is a researcher-constructed starting strategy, not an NCBI-generated final strategy. A real review should add synonyms/free text, date and study-design constraints, then record the complete PubMed query and retrieval date.

## 可复制任务

```text
使用 $nature-academic-search 为“生成式 AI 与医学教育”构建 PubMed 起始检索式。
先分别调用 lookup_mesh 核对 Artificial Intelligence、Generative Artificial Intelligence
和 Education, Medical 的规范主题词与 MeSH ID；再把 MeSH 与题名/摘要自由词分组组合。
输出每个主题词的核验结果、最终检索式和仍需人工调整的边界，不要把关键词直接猜成 MeSH。
```

![2026-07-31 PubMed MeSH 真实查询结果](../assets/academic-search-pubmed-mesh.png)
