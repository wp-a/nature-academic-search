# Workflow 4：引用文件管理

**目的：** 下载或转换 PubMed、CrossRef 与 arXiv 引用元数据。

## 示例

```bash
nature-academic-search citation --pmid 28344011 --format nbib
nature-academic-search citation --doi 10.1038/nature14539 --format ris
nature-academic-search citation --arxiv 1706.03762 --format bib
nature-academic-search citation --input refs.txt --format ris --output references/
```

支持 `.nbib`、`.ris`、`.bib`、`.enw`。格式说明见
[RIS and BibTeX Format](../ris-bibtex-format.md)。

## 批量输入

```text
PMID:28344011
DOI:10.1038/nature14539
ARXIV:1706.03762
QUERY:TB-Profiler AND Bioinformatics[Journal]
AUTHOR:Dheda TITLE:drug-resistant tuberculosis
```

转换前先核验标识符并去重；转换后检查成功数、失败项与输出格式。来源失败时不得用模型补写缺失元数据。
