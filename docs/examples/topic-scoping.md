# 开题检索：大语言模型与医学教育

**实测日期：** 2026-07-31（Asia/Shanghai）  
**工具版本：** Academic Paper Search 0.2.0（历史实测记录）
**查询：** `large language models medical education`  
**每源请求数量：** 3

## 本次真实来源状态

```yaml
entity_type: publication
sources_queried: [crossref, pubmed, arxiv, openalex, europe_pmc]
sources_succeeded: [crossref, arxiv, openalex, europe_pmc]
raw_result_count: 12
result_count: 12
errors:
  - source: pubmed
    kind: rate_limited
    status: 429
```

PubMed returned HTTP 429 during this run. The workflow kept the other four sources and disclosed the gap; this screenshot must not be read as a five-source-complete search.

## 三条可继续核验的线索

| 题名 | 年份 | 稳定标识符 | 本次来源 |
|---|---:|---|---|
| Performance of ChatGPT on USMLE: Potential for AI-assisted medical education using large language models | 2023 | DOI `10.1371/journal.pdig.0000198`; PMID `36812645`; OpenAlex `W4319662928` | OpenAlex |
| How Does ChatGPT Perform on the United States Medical Licensing Examination (USMLE)? | 2023 | DOI `10.2196/45312`; PMID `36753318`; OpenAlex `W4319460874` | OpenAlex |
| Large Language Models in Medical Education: Opportunities, Challenges, and Future Directions | 2023 | DOI `10.2196/48291`; PMID `37261894`; OpenAlex `W4376866715` | OpenAlex |

These are discovery candidates, not an inclusion set. The query had no date, study-design, language, population, or peer-review filter. Citation counts are source-specific and change over time, so they are omitted here.

## 可复制任务

```text
使用 $nature-academic-search 为“生成式 AI 在医学教育中的应用与风险”做开题检索。
先记录检索日期和纳入范围，再使用默认论文源检索；按 DOI、PMID、PMCID、arXiv
和 OpenAlex ID 去重。把正式论文、预印本和未解决记录分开，逐源报告成功、失败与
限流状态。不要把本次初筛描述成系统综述，也不要根据引用次数判断证据质量。
```

![2026-07-31 多源开题检索真实结果](../assets/academic-search-topic-scoping.png)
