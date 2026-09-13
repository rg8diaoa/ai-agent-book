# AGENTS.md — 人机协作规则（学习期）

> 依据：与指导老师确认的分工原则（2026-09-13）。对本仓库工作的任何 AI agent 生效（TRAE / Codex / Claude Code 等）。
> 核心理念：学习 agent 开发要有自己的思想，课程实验本身必须本人完成；**但使用 agent 本身也是一种能力**，不涉及课程实验本身的准备工作应委托 AI 代办。

## 1. 分工边界

| 类别 | 谁做 | 例子 |
|---|---|---|
| 实验代码与配置（`chapter1/**`、`agentbook/**` 等课程目录的修改） | **本人** | 加 provider 分支、改实验配置、跑 `run_experiment_*.py`、实验代码改造 |
| 学习笔记 / 心得（`docs/cc_learn/**`） | **本人撰写**；AI 只做格式建议，不代写观点 | CC_Task0学习心得 |
| 能力探测与测试（`model_tests/**`） | **AI 可全代办** | T 系列模型能力测试、API 形态验证、运行测试并判读 |
| 资料核对与文档（`*.md` 指南/报告） | AI 起草、本人审定 | 每条结论必须带 文件:行号 或官方 URL；不确定先实测 |
| git 提交 | 仅在本人明确说"提交"时执行 | push 需单独确认 |

## 2. AI 行为准则

1. **结论可验证**：涉及代码 / 模型能力的结论给出 文件:行号 或官方文档 URL；文档与代码冲突、或各平台说法矛盾时，以本地代码 + 实测为最终裁判（本仓库已有先例：README 写 `run_experiment_7_2.py` 实为 `run_experiment_8_2.py`）。
2. **不代替思考**：机制类问题解释原理 + 给验证路径，不直接给"做完的作业"。
3. **密钥安全**：key 只存根 `.env`（已被 .gitignore 忽略）；任何回复、日志、提交中不得出现密钥明文；查看 `.env` 只提取变量名，不输出值。
4. **测试脚本**（`model_tests/**`）只从环境变量读 key，不得硬编码。
5. **改动最小**：课程实验原文件尽量不动——替换类实现放独立脚本（如 1-2 的 `main_react_search.py`），保证与上游仓库可对照、可回退。

## 3. 环境备忘（实测得出，供后续 agent 免踩坑）

- Python 一律走项目虚拟环境：`.venv\Scripts\python.exe`；**不要用 `uv run`**——沙箱不允许 uv 写工作区外的缓存目录（`E:\Documents\.uv-cache`，os error 5）。
- 根 `.env` 当前 key 清单：`ZHIPU_API_KEY`（GLM Coding Plan key；2026-09-13 时已到期，影响 `/api/v1` 端点，paas/v4 不受影响）。待本人补充：`AGNES_API_KEY`（+`AGNES_BASE_URL`）、`MIMO_API_KEY`。
- `.venv` 内已装：openai / requests / python-dotenv。
- 仓库 README 与实际文件偶有 drift（如 `run_experiment_8_2.py`），行号引用允许 ±几行偏差。

## 4. 规则指针

- 模型替换与测试手册：[实验前大模型替换指南.md](实验前大模型替换指南.md)（T 测试 → R 替换 → V 验证；§0.1 定稿、§5.1 决策树）
- 结论证据库：[ch1实验核对报告.md](ch1实验核对报告.md)（A/B/N 编号，全部带引用与验证路径）
- 课程背景：[chapter1/README.md](chapter1/README.md)（实验 1-1 / 1-2 / 1-3 / 1-4 / 7-1&7-2）
- 测试脚本：`model_tests/`（t1_mimo · t2_zhipu_search · t3_agnes_site · t4_agnes_image · t6_zhipu_responses）

## 5. 记忆机制（当前方案）

- 本文件 = 跨工具协作宪法；TRAE 侧由 `.trae/rules/project_rules.md` 薄指针引用（单份规则源，避免双份漂移）。
- 实验进度 / 测试状态**不写进规则文件**——以 git log + 指南与报告两份 md 为准（文档即记忆）。
