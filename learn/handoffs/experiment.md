# HANDOFF · 实验指导会话分册

> 职责：带做 ch1 五实验、坑位与概念答疑、证据落盘验收。路由与铁律见 [../HANDOFF.md](../HANDOFF.md)。

## 必读（按序）

1. [learn/README.md](../README.md) — 目录导航 + task↔ch 映射表（课程节奏与截止）
2. [learn/ch1/contracts.py](../ch1/contracts.py) — 上游契约表（env 槽位映射，注释含语义）
3. [ch1五实验原理与操作指南.md](notes/guides/ch1五实验原理与操作指南.md) — 五实验前因后果/原理/逐步命令/证据落点/坑
4. [Task0操作手册.md](notes/guides/Task0操作手册.md) — Step 1–8 已做步骤与命令 + Step 9 未做清单
5. [Task0坑位全盘查.md](notes/research/Task0坑位全盘查.md) — A/B/C/D 坑位速查（现象→根因→处置→证据）

## 五实验命令表（适配层统一入口，上游零修改）

| 实验 | 适配器命令 |
| --- | --- |
| 1-1 context（上下文消融） | `.venv\Scripts\python.exe learn\ch1\run.py --exp context --evidence -- --mode ablation --cases 3` |
| 1-2 web-search-agent（路由变体） | 入口在 `learn/ch1/variants/web-search-agent/main_route.py`（builtin/react 两模式） |
| 1-3 search-codegen | `.venv\Scripts\python.exe learn\ch1\run.py --exp search-codegen --evidence -- --backend dashscope --mode single --request "<任务>"`（⚠️ 缺 backend 透传会失败：上游默认 openai 且 .env 无 OPENAI_API_KEY，2026-09-14 实测） |
| 1-4 image-gen-workflow | `.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow --evidence -- --route workflow --requirement <id或文本>`（route 勿用 all，会撞不可用的 gemini 路线） |
| 7-1&7-2 learning-from-experience | `.venv\Scripts\python.exe learn\ch1\run.py --exp learning-from-experience --evidence`（llm 轨走 LLM_PROVIDER=dashscope 契约） |

## 实验进度

- 1-1 context 消融 ✅（2026-09-14/15，路由 zhipu/glm-5.3-flash，默认单案例五臂，两次运行五臂结局一致）：
  证据 `evidence/context_log.txt`、`20260914T162109_run_context.json`、`20260914_context_ablation_*`、
  `20260915T0021_context_run2_results.json`（产物均已移出上游 chapter1/context/）
- 1-2 / 1-3 / 1-4 / 7-1&7-2 ⏳ 未运行（补做顺序与注意事项见操作手册 Step 9）
- 消融实验答疑：2026-09-16 已初步解答（设计示意图 vs 实验证据之分、五臂 outcome→badge 映射、
  grounding/编造数字判读、`validation/latest.json` 为作者验收组装品而非实验原生输出）；后续疑问在本册挂账：
  - （暂无）

## 证据与渲染工具

- 渲染：`.venv\Scripts\python.exe learn\infra\render_report.py --input <json> --open`（五形状自动识别；SVG 速览见 render_ablation_figure.py；详见操作手册 Step 8）
- 转录：`run.py --evidence` 结束时自动转录上游产物进 evidence/（contracts.artifacts 声明，纯复制零解析）

## 更新约定

实验完成/状态变化时更新「实验进度」节；坑位结论写 `notes/research/`（规律提炼与心得观点由本人撰写）。
