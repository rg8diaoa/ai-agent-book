# learn/ — 个人学习记录容器

> 本目录是**个人学习记录**（非书官方内容）：按章编号组织的学习笔记、能力探测、
> 第二轨验收证据与**运行适配层**。上游文件（书稿、实验代码、配置）保持原样零修改——
> 对上游实验的一切适配经 `learn/ch1/contracts.py` 契约注入完成（主仓保真、适配外置）。

## 授权与声明

- 原书《深入理解 AI Agent：设计原理与工程实践》版权归 Bojie Li 所有，协议 Apache-2.0（见根 [LICENSE](../LICENSE)）。
- 上游文件保持上游原样；本 fork 对上游已有文件**零修改**（`git diff origin/main --name-status` 对上游路径无 M/D）。
- `learn/**` 为本人新增内容 © 本人，随本仓库以 Apache-2.0 提供。
- 密钥只存根 `.env`（不入库）；任何脚本仅从环境变量读 key。

## 目录导航

| 位置 | 内容 |
|---|---|
| `chN/notes/{guides,research}/` | 学习文档（操作手册轨 / 证据核对轨） |
| `chN/probes/` | 能力探测脚本（每章编号从 t1 重新起） |
| `chN/evidence/` | 第二轨证据（acceptance_router / run.py 写入；json 入库、png 忽略） |
| `chN/variants/` | 纯新增变体入口（如 web-search-agent/main_route.py） |
| `chN/contracts.py`、`chN/run.py` | 运行适配层（上游契约槽位注入 + 统一启动器） |
| `router/` | 任务模型路由（`model_config.json` + `model_router.py`） |
| `infra/` | 探测公共设施（probe_utils）+ 第二轨验收（acceptance_router）+ 路由冒烟（t10） |

## task ↔ ch 映射表（课程节奏）

> 开营 2026-09-14 ｜ 任务周期 09-17 → 10-05（19 天）｜ ⚠️ **未按时完成 Task 会被报离群**，且截止时间均为**凌晨 03:00**，请提前完成。
> Task→章节按任务主题与书目录对应，如有出入以课程官方任务卡为准。

| Task | 主题 | 对应章节 | 截止 | 状态 | 产物位置 |
|---|---|---|---|---|---|
| Task 0 | Agent 基础与环境准备 | ch1（实验 1-1 / 1-2 / 1-3 / 1-4 / 7-1&7-2）+ 探测 t1–t12 | 09-17 | ✅ | `ch1/notes/`、`ch1/probes/`、`router/`、`infra/` |
| Task 1 | 上下文工程与 Memory / RAG | ch2（上下文工程）+ ch3（用户记忆与知识库） | 09-20 | ⏳ | `ch2/`、`ch3/`（待建） |
| Task 2 | Tools 与 MCP | ch4（工具与 MCP 协议） | 09-23 | ⏳ | `ch4/`（待建） |
| Task 3 | Coding Agent 与 Agent 交互 | ch5（Coding Agent 与通用 Agent）+ ch6（交互扩展） | 09-26 | ⏳ | `ch5/`、`ch6/`（待建） |
| Task 4 | Agent Evaluation 与模型能力优化 | ch7（评估）+ ch8（模型后训练） | 09-29 | ⏳ | `ch7/`、`ch8/`（待建） |
| Task 5 | Agent 持续进化与 Multi-Agent | ch9（持续进化）+ ch10（多 Agent 协作） | 10-02 | ⏳ | `ch9/`、`ch10/`（待建） |
| Task 6 | 共学总结 | 跨章总结 | 10-05 | ⏳ | 总结笔记（位置待定） |
| learn-repo | 建仓与整改 | 仓库级（learn 容器结构、适配层、保真机制） | — | ✅ | 本 README + `ch1/notes/guides/学习记录仓整改与发布方案.md` |

## 运行适配层

```powershell
# 列出实验（零 API）
.venv\Scripts\python.exe learn\ch1\run.py --list
# 跑某实验（上游脚本原样运行；契约注入 env，cwd=实验目录）
.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow -- --route workflow --requirement agi-programmer
# 带证据落盘
.venv\Scripts\python.exe learn\ch1\run.py --exp search-codegen --evidence
```

- 契约表：`ch1/contracts.py`（每个实验的"上游槽位 ↔ 路由任务"映射，变量名 = 上游代码要读的槽位，与实际厂商无关；真实 provider/model 记录在证据 json）。
- 上游共享注册表 `agentbook/providers/registry.py` 的 `key_vars`/`base_url_var` 均支持 env 覆盖（`providers/models.py:72`）。
- context 实验若上游 `SUPPORTED_PROVIDERS` 不含路由 provider 名，回退 openrouter 通用槽：
  `--provider openrouter --model openai/<model>` + `OPENROUTER_API_KEY`。

## 常跑命令（探测与验收）

```powershell
.venv\Scripts\python.exe learn\infra\t10_router_smoke.py       # 路由冒烟（改 model_config.json 后必跑）
.venv\Scripts\python.exe learn\ch1\probes\t2_zhipu_search.py   # 探针抽检
.venv\Scripts\python.exe learn\infra\acceptance_router.py all  # 第二轨验收
```

## 新增探测的约定

1. **归属**：属于哪章放 `learn/chN/probes/`；编号从 t1 重新起，文档引用写 `chN/tX`。
2. **样板**：复用 `learn/infra/probe_utils.py`；引导行统一 `sys.path.insert(0, str(Path(__file__).resolve().parents[3]))` + `from learn.infra.probe_utils import …`。
3. **密钥**：只从根 `.env` 读（`probe_utils.require_key`）；输出不含 key 明文。
4. **路径**：取仓库根一律 `ROOT = Path(__file__).resolve().parents[N]`（N = 文件到根的目录层级）。
