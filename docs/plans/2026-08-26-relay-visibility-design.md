# WPIRONMAN Relay Visibility Design

## Goal

让 WPIRONMAN AI 中转入口在 README、安装文档和 Codex/Claude Code 插件发现页更容易被看到和理解，
同时保持 Academic Paper Search 的学术检索主叙事与证据边界。

## Chosen Approach

采用三层入口：

1. **首屏入口**：徽章下方增加紧凑的推荐链接，说明它是可选的 OpenAI-compatible 模型入口，并直达控制台。
2. **安装后行动入口**：在 30 秒开始区域保留一个带“配置 / 进入控制台”动作的高可见度 callout，帮助刚安装的用户完成下一步。
3. **工作流上下文入口**：在 workflow 与安装文档保留环境变量配置，解释中转站只用于模型辅助步骤，不是学术数据源。

插件 manifest 与 Codex `openai.yaml` 会在描述和默认提示中提及可选 WPIRONMAN 配置，但不把密钥写入仓库，
也不把中转设置为运行前置条件。

## Copy Rules

- CTA 使用“进入控制台 / 配置模型入口”等明确动词。
- 每个入口都保留“可选”“模型层”“不是论文来源”的边界说明。
- 不使用未经验证的价格、速度、模型数量、稳定性或效果承诺。
- 不在触发词或 skill 正文中引导用户把中转当作学术数据库。

## Verification

- README 首屏包含可点击的 WPIRONMAN 链接，并且安装、workflow、插件描述均包含一致入口。
- 测试确保入口 URL、边界文案和插件镜像保持同步。
- 运行完整测试、Ruff、技能镜像同步与 `git diff --check`。
