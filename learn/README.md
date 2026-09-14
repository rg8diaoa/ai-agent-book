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

## task ↔ ch 映射表

| task | 覆盖章节/实验 | 产物位置 |
|---|---|---|
| task0 模型路由准备 | ch1 全部实验（1-1 context / 1-2 web-search-agent / 1-3 search-codegen / 1-4 image-gen-workflow / 7-1&7-2 learning-from-experience）+ 探测 t1–t12 | `ch1/notes/`、`ch1/probes/`、`router/`、`infra/` |
| learn-repo 建仓与整改 | 仓库级（learn 容器结构、适配层、保真机制） | 本 README + `ch1/notes/guides/学习记录仓整改与发布方案.md` |

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
