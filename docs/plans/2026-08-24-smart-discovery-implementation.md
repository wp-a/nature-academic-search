# Smart Discovery Implementation Plan

> B 阶段实现：在 evidence-grade search 之上增加可复现过滤、源查询翻译与确定性排序。

## 目标

- 用统一 `filters` 对象表达日期、语言、作者和文献类型。
- 对 PubMed、Crossref、OpenAlex、Europe PMC 生成明确的源原生查询；不支持的字段保留为本地后过滤。
- 用固定版本的本地相关性算法排序，并写入排序原因。
- 保留旧的 `type` 参数、四个 MCP 工具名和无过滤调用的结果兼容性。

## 实施任务

1. 先写 `filters.py` 与 `ranking.py` 的失败测试，覆盖规范化、日期校验、源翻译、后过滤、稳定排序和 exact identifier 加权。
2. 实现规范化过滤器与源查询翻译；源不支持的过滤字段必须进入后过滤路径，而不是静默丢弃。
3. 实现确定性排序，固定 `score_version`，使用 `record_id` 作为稳定 tie-breaker，并输出 `ranking_reasons`。
4. 将 `filters` 与 `ranking` 作为可选参数接入 `search_all` 和 `search_papers`，在 `search_run` 中记录规范化过滤器、翻译结果和排序配置。
5. 更新 Crossref、PubMed、OpenAlex、Europe PMC、arXiv 的可选查询参数，并补充 MCP、搜索协调器和源适配器测试。
6. 更新中英文优先文档与插件镜像，运行完整测试、Ruff、镜像同步、差异检查和 GitHub CI。

## 兼容性约束

- 没有传入 `filters` 时不做本地后过滤；旧 `type` 仍只使用原有 Crossref 过滤分支。
- 未请求 `ranking` 且未传入新过滤器时保持源返回顺序；传入过滤器时默认使用 `relevance`。
- 排序分数只描述检索相关性，不代表证据质量、同行评议质量或引用真实性。
- 过滤与排序不读取或写入任何 API key，也不依赖 WPIRONMAN 中转站。
