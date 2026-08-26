# AI 幻觉引用核验：让 DOI 回到真实论文

**实测日期：** 2026-07-31（Asia/Shanghai）  
**工具版本：** Academic Paper Search 0.2.0（历史实测记录）
**核验标识符：** `10.1038/nature14539`

## 待核验声称

为了演示冲突检测，假设收到下面这条引用：

> Smith et al. (2024). Large language models for clinical diagnosis. Nature. DOI: 10.1038/nature14539.

这不是一条真实引用，而是故意构造的待核验输入。

## DOI 实际解析结果

```yaml
title: Deep learning
authors: [Yann LeCun, Yoshua Bengio, Geoffrey Hinton]
year: 2015
journal: Nature
volume: "521"
issue: "7553"
pages: 436-444
doi: 10.1038/nature14539
source: crossref
```

## 判定

`mismatch`：DOI 可以解析，但题名、作者和年份都不支持待核验声称。正确做法是保留 CrossRef 返回的真实元数据，并要求提供原始来源；不能因为 DOI 存在就把错误题名标成 `verified`。

这个步骤只证明标识符与元数据是否一致，不证明论文内容支持某个科学论断。引用进入正式稿件前仍应核对出版社页面或原文。

## 可复制任务

```text
使用 $nature-academic-search 核验下面的参考文献。先从 DOI / PMID / PMCID / arXiv ID
取回原始元数据，再逐项比较题名、作者、年份和期刊。输出 verified、mismatch、
not_found 或 manual_needed，并解释冲突；不要用搜索结果自动补成一条看似完整的引用。

待核验引用：<在这里粘贴引用>
```

![2026-07-31 DOI 与题名冲突真实核验结果](../assets/academic-search-citation-verification.png)
