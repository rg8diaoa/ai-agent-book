# HANDOFF — 会话交接主路由

> 用途：多会话协作的交接入口。铁律（密钥/保真/commit 纪矩/分工边界）由 [AGENTS.md](../AGENTS.md)
> 自动注入每个会话，本文件只承载「会话路由」与「跨会话共享状态」；各会话的详细上下文在 handoffs/ 分册。

## 一句话身份

本仓库 = 《深入理解 AI Agent》书课的**个人学习记录 fork**（rg8diaoa/ai-agent-book，上游 bojieli/ai-agent-book）；
架构 = **主仓保真（上游文件零修改）+ `learn/` 容器（按章编号）+ 运行适配层（契约注入）+ 证据中文报告器（learn/infra/report/）**。

## 会话路由表

| 会话类型 | 开工先读 | 职责边界 | 状态更新责任 |
|---|---|---|---|
| 工具迭代（报告器 / probes / infra 工具链） | [handoffs/tool.md](handoffs/tool.md) | 迭代 render_report、转换器、探测脚本；不改上游 | tool.md 的「状态与已知问题」节 |
| 实验指导（带做实验 / 答疑） | [handoffs/experiment.md](handoffs/experiment.md) | 五实验运行、坑位与概念答疑、证据落盘验收 | experiment.md 的「实验进度」节 |
| 其他（笔记整理 / git 提交 / 仓库维护） | 本文件 + AGENTS.md | 低频杂务；规矩见 AGENTS.md | 本文件共享状态对应行 |

规则：各会话**只更新自己的分册**与主文件中属于自己的状态行；共享状态行（课程节奏/上游同步）任意会话可更新，保持一行一事。

## 跨会话共享状态

- 课程节奏：Task 0 ✅（09-17 03:00 截止；2026-09-16 交付笔记三件套 + 证据中文报告器）｜
  Task 1 ⏳（09-20 截止，ch2 上下文工程 + ch3 记忆与 RAG）｜ 完整映射见 [learn/README.md](README.md)
- 上游同步：每两周 `git fetch upstream && git merge upstream/main`（零冲突预期）
- 工作区基线：`git diff origin/main --name-status` 对上游路径必须无 M/D；
  CRLF 幽灵 M（`git diff` 内容为零的 M 状态）可用 `git restore <file>` 清除，勿混入提交
- 证据双轨：作者基线（chapter1/**/validation/）与第二轨（learn/chN/evidence/）永不混同；
  本人截图属过程影像，只进 notes/assets/

## 更新约定

- 各分册由对应会话随状态更新；主文件仅维护路由表与共享状态
- 提交纪律：commit 仅在本人明确说「提交」时执行；push 需单独确认
