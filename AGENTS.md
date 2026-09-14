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
5. **行为保真 + 加法扩展 + 证据分轨**：课程实验原文件的原 flag/默认行为不变；扩展一律用加法（新 flag 如 1-1 `--provider router`、新分支如 7-2 router、新脚本如 1-2 `main_route.py`）；验收证据分两轨——作者基线（`chapter1/**/validation/` + 锚定 runner）与路由变体（`model_tests/infra/acceptance_router.py` 产出的 `evidence_variant_*`）永不混同、变体不冒充基线。
6. **产物归位**：学习/研究类 md 产物一律写入 `docs/cc_learn/<task-id>/{guides,research}/`（guides=操作手册，research=证据核对），不在仓库根或其它目录散落。
7. **命名规范**：实验代码的配置字段前缀 = 任务路由名大写（如 `IMAGE_WORKFLOW_API_KEY` ← 路由 `image_workflow`）；字段名回答"配置从哪来"，函数名回答"拿来干什么"；模型/厂商名禁止进入代码标识符（模型身份只存在于 `agentbook/model_config.json`）。

## 3. 环境备忘（实测得出，供后续 agent 免踩坑）

- Python 一律走项目虚拟环境：`.venv\Scripts\python.exe`；**不要用 `uv run`**——沙箱不允许 uv 写工作区外的缓存目录（`E:\Documents\.uv-cache`，os error 5）。
- 根 `.env` 当前 key 清单：`ZHIPU_API_KEY`（按量计费；`/api/v1` Responses 端点仅对 Coding Plan 开放）、`AGNES_API_KEY`（归属 `https://apihub.agnes-ai.com/v1`）、`MIMO_API_KEY`（chat 内联搜索可用）、`DASHSCOPE_API_KEY`（百炼按量已充值，托管工具按量可用，T11 实测连通）。待补：`DEEPSEEK_API_KEY`（可选备胎）。
- `.venv` 内已装：openai / requests / python-dotenv。
- 仓库 README 与实际文件偶有 drift（如 `run_experiment_8_2.py`），行号引用允许 ±几行偏差。

## 4. 规则指针

- 模型路由与实验替换手册：[模型路由与实验替换指南.md](docs/cc_learn/task0/guides/模型路由与实验替换指南.md)（判据总表 → 路由层搭建 model_config.json / model_router.py → 逐实验接线 → 执行顺序清单）；实验代码引用路由一律 `from agentbook.model_router import resolve`，禁止出现厂商名/URL/key
- 结论证据库：[模型能力核对报告.md](docs/cc_learn/task0/research/模型能力核对报告.md)（A/B/N 编号，全部带引用与验证路径）
- 课程背景：[chapter1/README.md](chapter1/README.md)（实验 1-1 / 1-2 / 1-3 / 1-4 / 7-1&7-2）
- 测试脚本：`model_tests/`（`ch1/` = t1–t12 探测；`infra/` = acceptance_router 第二轨验收 + probe_utils 公共设施 + t10 路由冒烟；`evidence_variant/` = 第二轨证据；目录与命名约定见 model_tests/README.md）

## 5. 记忆机制（当前方案）

- 本文件 = 跨工具协作宪法；TRAE 侧由 `.trae/rules/project_rules.md` 薄指针引用（单份规则源，避免双份漂移）。
- 实验进度 / 测试状态**不写进规则文件**——以 git log + 指南与报告两份 md 为准（文档即记忆）。
