# HANDOFF — 会话交接文档

> 用途：新会话 AI 协作者的最小完备上下文。每次重要节点（实验完成/状态变化）由当值会话更新本文件并随学习提交入库。

## 一句话身份

本仓库 = 《深入理解 AI Agent》书课的**个人学习记录 fork**（rg8diaoa/ai-agent-book，上游 bojieli/ai-agent-book）；架构 = **主仓保真（上游文件零修改）+** **`learn/`** **容器（按章编号）+ 运行适配层（契约注入）**。

## 当前任务（2026-09-16 交接）

**协助完成 ch1 的五个实验**（Task 0 已 ✅：环境/探测 t1–t12/路由层/适配层均已落地并发布）：

| 实验                               | 适配器命令                                                                                                          |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| 1-1 context（上下文消融）               | `.venv\Scripts\python.exe learn\ch1\run.py --exp context --evidence -- --mode ablation --cases 3`                                   |
| 1-2 web-search-agent（路由变体）       | 入口在 `learn/ch1/variants/web-search-agent/main_route.py`（builtin/react 两模式）                                     |
| 1-3 search-codegen               | `.venv\Scripts\python.exe learn\ch1\run.py --exp search-codegen --evidence -- --backend dashscope --mode single --request "<任务>"`（⚠️ 缺 backend 透传会失败：上游默认 openai 且 .env 无 OPENAI_API_KEY，2026-09-14 实测）                                    |
| 1-4 image-gen-workflow           | `.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow --evidence -- --route workflow --requirement <id或文本>`（route 勿用 all，会撞不可用的 gemini 路线） |
| 7-1&7-2 learning-from-experience | `.venv\Scripts\python.exe learn\ch1\run.py --exp learning-from-experience --evidence`（llm 轨走 LLM\_PROVIDER=dashscope 契约）  |

## 必读（按序）

1. [AGENTS.md](../AGENTS.md) — 人机协作宪法（分工/密钥/保真/证据分轨，§2.5 是核心，已进入上下文时可不读）
2. [learn/README.md](README.md) — 目录导航 + task↔ch 映射表（课程节奏与截止）
3. [learn/ch1/contracts.py](ch1/contracts.py) — 上游契约表（每个实验的 env 槽位映射，注释含语义）
4. [模型路由与实验替换指南.md](ch1/notes/guides/模型路由与实验替换指南.md) — 路由判据与逐实验适配细节
5. [ch1五实验原理与操作指南.md](ch1/notes/guides/ch1五实验原理与操作指南.md) — 五实验前因后果/原理/逐步命令/证据落点/坑（2026-09-14，执行手册）

## 铁律（违者停手）

1. **主仓保真**：上游文件零修改（判据 `git diff origin/main --name-status` 对上游路径无 M/D）；一切适配走 `learn/ch1/contracts.py` 契约注入
2. **密钥**：只存根 `.env`（永不入库）；脚本仅从环境变量读；输出/日志不得含 key 明文
3. **git**：`commit` 仅在本人明确说"提交"时执行；push 需单独确认
4. **证据分轨**：作者基线（`chapter1/**/validation/`）与路由变体（`learn/ch1/evidence/`）永不混同、变体不冒充基线
5. **笔记**：学习笔记/心得由本人撰写观点，AI 只做格式建议
6. **运行**：`.venv\Scripts\python.exe`（不要 `uv run`——本机沙箱实测限制）

## 状态快照

- Task 0 ✅（09-17 03:00 截止）｜ Task 1 ⏳（09-20 截止，ch2 上下文工程 + ch3 记忆与 RAG）｜ 完整映射见 learn/README.md

- 第二轨验收：builtin 冒烟为 Task 0 探测记录（AI 代办，非实验运行）；react/workflow/native/llm 待本人实验中补跑
- 实验进度：1-1 context 消融已由本人跑通并复跑验证（2026-09-14/15，路由 zhipu/glm-5.3-flash，
  默认单案例五臂，两次运行五臂结局一致；证据：evidence/context_log.txt、
  20260914T162109_run_context.json、20260914_context_ablation_*、20260915T0021_context_run2_*，
  产物均已移出上游 chapter1/context/）；1-2 / 1-3 / 1-4 / 7-1&7-2 未运行；
  原理与逐步命令见 [ch1五实验原理与操作指南.md](ch1/notes/guides/ch1五实验原理与操作指南.md)

- 上游同步：每两周 `git fetch upstream && git merge upstream/main`（零冲突预期）

## 更新约定

实验完成/状态变化时更新"当前任务"与"状态快照"，随学习提交入库。
