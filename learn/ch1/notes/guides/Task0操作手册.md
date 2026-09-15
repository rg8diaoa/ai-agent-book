# Task 0 操作手册

> 用途：复现 Task 0（环境准备 + context 实验）时的对照手册。
> 术语：「当时」= 2026-09-14 开营冲刺的历史命令；「现行」= learn 适配层定型后的标准跑法。
> 分层阅读：叙事层看 [Task0学习笔记](Task0学习笔记.md) ｜ 坑位层看 [../research/Task0坑位全盘查.md](../research/Task0坑位全盘查.md) ｜ 本文 = 命令层。
> 密钥：只存根 `.env`；任何输出 / 截图 / 提交不得含 key 明文。

## 状态总览

| 步骤 | 内容 | 状态 | 关键影像 / 证据 |
|---|---|---|---|
| Step 1 | 基础环境检查 | ✅ 2026-09-14 | [env_check](../assets/20260914_step1_env_check_ok.png) |
| Step 2 | 克隆仓库（配代理） | ✅ 2026-09-14 | [clone_ok](../assets/20260914_step2_clone_ok.png) |
| Step 3 | 安装 uv | ✅（历史路径） | [uv_verify](../assets/20260914_step3_uv_verify.png) |
| Step 4 | 安装第 1 章依赖（跨盘符修复） | ✅ | [reverify](../assets/20260914_step4_uv_reverify.png) |
| Step 5 | 设置 API KEY | ✅ | [gitignore 验证](../assets/20260914_step5_env_gitignore.png) |
| Step 6 | 运行第一章 main.py | ✅ 连接智普成功 | [zhipu_ok](../assets/20260914_step6_mainpy_zhipu_ok.png) |
| Step 7 | 搭建 learn 目录 | ✅ | [learn_dir](../assets/20260914_step7_learn_dir.png) |
| Step 8 | context 实验 | ✅ 消融跑通 | [run_ok](../assets/20260914_step8_context_run_ok.png) + [evidence json](../../evidence/20260915T0021_context_run2_results.json) |
| Step 9 | 其余实验补做（1-2 / 1-3 / 1-4 / 7-1&7-2） | ⏳ 未做 | 待补做后回填 |
| 收尾 | 三件套归档 | ✅ 笔记/坑位已精校 | 本三件套 |

## 环境基线

- Windows + PowerShell；git；Python 3.12（仓库自带 `.venv`）
- **现行铁律：Python 一律 `.venv\Scripts\python.exe`**——本机沙箱内 uv 写工作区外缓存受限（os error 5，AGENTS.md §3 实测）；开营当日经 uv 的历史见坑位 A2
- 根 `.env` key 清单：`ZHIPU_API_KEY`、`AGNES_API_KEY`、`MIMO_API_KEY`、`DASHSCOPE_API_KEY`（各家计费/限制见 [模型能力核对报告](../research/模型能力核对报告.md)）

## Step 1–2：环境检查与克隆

```powershell
git clone <fork 地址>
git remote -v; git log --oneline -5   # 核对 remote 指向与提交历史
```

国内网络低速时先配加速代理 + git 全局代理（坑 A1，具体代理地址🖊️待精校补记）。

## Step 3–4：uv 安装与依赖（历史路径）

当时：uv 安装验证通过 → 跨盘符硬链接 warning → 设置 uv 缓存路径与链接模式后通过（坑 A2）。
🖊️ 待精校：当时设置的具体环境变量值（`UV_CACHE_DIR` / `UV_LINK_MODE`）。

**现行**：仓库已带 `.venv`，直接用 `.venv\Scripts\python.exe`，不再经 uv。

## Step 5：配置 .env（key 永不入库）

```powershell
Copy-Item .env.example .env     # 仓库根执行；Zhipu 模板见 .env.example「Zhipu (GLM)」一节
# 编辑 .env 填入实际 key（不进聊天、不截图明文、不提交）
git check-ignore .env           # 有输出 = 已被排除 ✓
```

## Step 6：连接大模型

历史：直接运行上游 `chapter1/context/main.py`（显式 provider 参数；PDF 路径坑见 B1）。
**现行**（统一入口，上游零修改）：

```powershell
.venv\Scripts\python.exe learn\ch1\run.py --list
.venv\Scripts\python.exe learn\ch1\run.py --exp context --evidence
```

完整用法与契约表见 [learn/README.md 运行适配层](../../README.md)。

## Step 7：learn 目录

结构与约定见 [learn/README.md](../../README.md)；fork 仓库：<https://github.com/rg8diaoa/ai-agent-book>

## Step 8：context 实验

```powershell
.venv\Scripts\python.exe learn\infra\t10_router_smoke.py          # 路由冒烟（改 model_config.json 后必跑）
.venv\Scripts\python.exe learn\ch1\run.py --exp context -- --mode ablation
.venv\Scripts\python.exe learn\infra\acceptance_router.py all     # 第二轨验收
```

**验证**：终端流式输出正常（无静默、无 GBK 报错）→ 消融结果表 / 对比矩阵 / 分析总结依次打印 → `learn\ch1\evidence\` 落 json。

**证据可视化**（可选）：从 evidence json 重生成「书图预期 vs 实测」对照图，产物入 `notes/assets/`（图属可视化，不入 evidence/）：

```powershell
.venv\Scripts\python.exe learn\infra\render_ablation_figure.py --input learn\ch1\evidence\20260915T0021_context_run2_results.json --output learn\ch1\notes\assets\20260915_step8_ablation_expect_vs_actual.svg
```

**中文 HTML 报告**（研究型界面，自动识别输入形状；SVG 速览与本报告互补）：

```powershell
# 本机实测（第二轨 summary 形状）
.venv\Scripts\python.exe learn\infra\render_report.py --input learn\ch1\evidence\20260915T0021_context_run2_results.json --open
# 上游验收 json（arms 形状，作者基线轨数据）也可渲染
.venv\Scripts\python.exe learn\infra\render_report.py --input chapter1\context\validation\latest.json
# 其他实验同理（search-codegen / image-gen-workflow / learning-from-experience 的 validation json）
```

## Step 9：其余实验补做（⏳ 未做，后续继续）

Task 0 截止时仅完成实验 1-1（context）；以下 4 个实验待补做，跑法均已就绪（改过 `model_config.json` 后先跑路由冒烟）：

```powershell
# 实验 1-3 search-codegen（Deep Research 闭环，chapter1/search-codegen/）
.venv\Scripts\python.exe learn\ch1\run.py --exp search-codegen --evidence

# 实验 1-4 image-gen-workflow（图像双路线对照，chapter1/image-gen-workflow/）
.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow -- --route workflow --requirement agi-programmer

# 实验 7-1&7-2 learning-from-experience（Q-learning + LLM 双臂，chapter1/learning-from-experience/）
.venv\Scripts\python.exe learn\ch1\run.py --exp learning-from-experience --evidence

# 实验 1-2 web-search-agent（不在 run.py 适配范围，走路由变体入口）
.venv\Scripts\python.exe learn\ch1\variants\web-search-agent\main_route.py --mode react
```

- `main_route.py` 的 `--mode`：`builtin`（内联快路径）/ `react`（ReAct 轨迹），见 [main_route.py](../../ch1/variants/web-search-agent/main_route.py)。
- 每个实验完成后回填「状态总览」并按证据约定落盘：`--evidence` → `learn\ch1\evidence\`（json 正典），过程截图 → `notes/assets/`（`20260915_step9_<实验名>_slug.png`）。

## 已知 drift 与坑位速查

| 现象 | 处理 |
|---|---|
| git clone 20-30KiB/s | 加速代理 + git 全局代理（A1） |
| 跨盘符硬链接 warning（uv 缓存 C 盘 / 项目 E 盘） | 缓存路径与链接模式指到同盘（A2） |
| 子进程 GBK/emoji UnicodeEncodeError | 强制 `PYTHONIOENCODING=utf-8` + 父进程 `errors="replace"`（A3） |
| 上游 create_sample_pdf.py 相对路径报错 | 用 run.py 启动（cwd=实验目录），不改上游（B1） |
| README 写 run_experiment_7_2 实为 8_2 | 文档与代码冲突以本地代码 + 实测为裁判（B2） |
| 未激活 uv / 未指定 provider | 现行走 `.venv` + run.py 显式路由（C1） |
| --evidence 模式无流式输出 | run.py 已加流式打印（D1） |
