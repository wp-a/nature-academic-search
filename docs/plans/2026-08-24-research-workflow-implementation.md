# Research Workflow Automation Implementation Plan

## 目标

实现本地、可审计的 YAML 工作流运行器，并提供一个可选的 OpenAI-compatible HTTP 模型适配器。
不新增 MCP 工具，保持四个工具名稳定；CLI 增加 `workflow` 子命令。

## 任务

1. 先写工作流校验、审批门、artifact 清单、模型失败降级和 provider JSON 重试的失败测试。
2. 实现 `WorkflowSpec` 与 `WorkflowRunner`：plan → search → verify → screen → export，保存
   `run.json`、`results.json`、`verification.json`、`screening.csv`、`references.ris`、`report.md`。
3. 实现 `OpenAICompatibleRelay`：支持 HTTP Responses 与 Chat Completions，API key 只来自环境变量，
   JSON 解析失败最多重试一次，401/超时/网关不可用只标记模型步骤 skipped。
4. 把工作流 CLI 接入 Codex/Claude Code 安装后的同一 Python 包；YAML 依赖缺失时给出可操作错误。
5. 更新 README、SKILL、检索工作流和插件镜像，写明中转配置、隐私默认值和审批方式。
6. 运行全量测试、Ruff、构建、镜像同步、差异检查和 GitHub CI。

## 安全与兼容性

- 默认只发送标题、摘要、标识符和用户批准的元数据；全文上传必须显式 `allow_full_text: true`。
- API key 不写入 workflow、run manifest、日志、prompt artifact 或异常文本。
- provider 不可用不阻断 source search、field verification 或 citation export。
- workflow 文件只能写入指定输出目录，禁止路径穿越；导出默认只包含 `verified` 记录。
