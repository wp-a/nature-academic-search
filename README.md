# Academic Search

Claude Code 的学术搜索技能包，集成 PubMed、CrossRef、arXiv 三大文献数据库。

## 功能

- **多源并发搜索**: 同时查询 CrossRef / PubMed / arXiv，自动合并去重
- **按 ID 获取详情**: 支持 DOI、PMID、arXiv ID 自动识别
- **格式化引用**: APA / Nature / IEEE / Vancouver 等风格
- **MeSH 词表查询**: 构建精准 PubMed 检索式
- **文献管理脚本**: .nbib / .ris / .bib / .enw 格式互转

## 安装

```bash
bash install.sh your-email@example.com
```

## MCP Tools

| Tool | 说明 |
|------|------|
| `search_papers` | 多源并发搜索 |
| `get_paper_by_id` | 按 DOI/PMID/arXiv ID 获取详情 |
| `get_citation` | 格式化引用生成 |
| `lookup_mesh` | MeSH 词表查询 |
