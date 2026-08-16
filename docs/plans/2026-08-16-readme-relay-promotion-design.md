# README Relay Promotion Design

## Goal

Add a transparent, low-interruption promotion for the WPIRONMAN AI relay
console without weakening Academic Paper Search's research-tool positioning.

## Placement

Place one GitHub-native `TIP` callout at the end of `30 秒开始`, after the
installation and credential notes and immediately before `数据源如何分工`.
The project purpose, real-result example, and installation instructions remain
ahead of the promotion.

## Copy

```markdown
> [!TIP]
> **推广 · WPIRONMAN AI 中转控制台**
>
> 统一管理模型渠道、密钥、额度与调用入口，让模型服务状态更清晰。
> [进入控制台 →](https://api.wpironman.top)
```

The wording is based on the existing WPIRONMAN project description. It does not
make price, speed, availability, or compatibility guarantees.

## Verification

- Add a README metadata test for the disclosure label, destination URL, and
  placement between the installation and data-source sections.
- Run the targeted test, full test suite, skill synchronization check, diff
  check, and repository CI.
- Preserve the user-owned untracked `uv.lock`.
