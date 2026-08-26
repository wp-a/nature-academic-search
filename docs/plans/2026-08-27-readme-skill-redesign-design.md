# README 与 Skill 重构设计

## 背景

项目已经具备多源检索、字段级引用核验、MeSH 策略、引文图谱、声明式 workflow、RIS/BibTeX 导出和可选 WPIRONMAN 中转，但 README 仍按功能累加，中文科研用户需要较长阅读才能完成第一次成功调用。

## 目标

1. 用中文科研用户熟悉的任务路径组织 README：理解价值、安装、复制任务、查看真实结果、深入边界。
2. 将真实案例从 3 个扩展为 6 个场景：开题检索、AI 幻觉引用核验、PubMed/MeSH、上下游引文追踪、综述批量导出、临床试验关联核验。
3. 充分展示现有三张真实截图，同时明确截图日期、工具版本和不可外推的边界。
4. 让 SKILL.md 成为 Codex/Claude Code 的稳定执行规范：触发条件、工具路由、来源状态、图谱契约、WPIRONMAN 隐私边界。
5. 不改变 MCP 工具名、安装标识和现有技术行为。

## 信息架构

README 首屏依次包含价值主张、能力矩阵、30 秒安装、最短调用示例；随后展示六个中文场景；最后放数据源、WPIRONMAN、中间产物、边界和深入文档链接。

SKILL 保持短而可检索，按任务路由、来源角色、执行流程、结果契约、引文图谱、workflow 和证据规则组织；详细案例仍链接到 references 与 docs/examples。

## WPIRONMAN 说明

中转站必须被描述为可选的 OpenAI-compatible 模型入口，不是论文数据库，也不替代 Crossref、PubMed、OpenAlex、Europe PMC 或 Semantic Scholar。README 提供最小环境变量配置、适合的 plan/screen 场景、隐私默认值、失败降级和控制台链接；禁止暗示中转能提升学术来源覆盖或绕过数据库限制。

## 验证

- README 的既有关键短语、中文场景和边界断言测试继续通过。
- 根目录 SKILL 与插件镜像保持字节一致。
- `scripts/sync_skill.py --check`、Ruff、全量 pytest 和 wheel 构建通过。
