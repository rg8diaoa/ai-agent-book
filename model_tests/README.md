# model_tests — 能力探测与第二轨验收（AI 代办区）

> 分工见 [AGENTS.md](../AGENTS.md) §1；测试结论判读见指南 §五 测试存档。

## 目录

| 位置 | 内容 |
|---|---|
| `ch1/` | 第一章（task0）能力探测 t1–t12（编号沿用指南 §五 存档与核对报告引用） |
| `infra/` | 跨实验基础设施：`acceptance_router.py`（第二轨验收采集）、`probe_utils.py`（探测公共设施）、`t10_router_smoke.py`（路由层冒烟，改 `model_config.json` 后必跑） |
| `evidence_variant/` | 第二轨证据输出（acceptance_router 自动写入；json 入库、png 已 gitignore） |

## 新增探测的约定

1. **归属**：属于哪章放 `chN/`；新章直接建目录，编号从 t1 重新起，文档引用写 `chN/tX`。
2. **样板**：优先复用 `infra/probe_utils.py`（`require_key / load_env / dump / head / post_json / responses_receipt_types / show_message`），不复制"调用+dump"代码。
3. **密钥**：只从根 `.env` 读（`probe_utils.require_key`）；任何输出不含 key 明文。
4. **可判读**：打印 provider/model/HTTP 状态/关键字段；不落盘临时文件。
5. **路径**：`chN/` 与 `infra/` 下的脚本取仓库根一律 `ROOT = Path(__file__).resolve().parents[2]`。

## 常跑命令

```powershell
.venv\Scripts\python.exe model_tests\infra\t10_router_smoke.py      # 路由冒烟（改 model_config.json 后必跑）
.venv\Scripts\python.exe model_tests\infra\acceptance_router.py all # 第二轨验收（V1–V6 通过后）
```
