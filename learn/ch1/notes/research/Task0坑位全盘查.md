# Task 0 坑位全盘查（学习笔记素材 · 事实层）

> 性质：**事实盘查**（现象 → 根因 → 处置 → 证据），供本人撰写学习笔记引用。
> 规矩：规律提炼与心得观点由本人撰写（AGENTS.md 分工边界）。
> 影像链接：本人截图在 [../assets/](../assets/)；实验证据（json 正典）在 [../../evidence/](../../evidence/)（png 副本本地可重生成，不入库）。
> 分层阅读：叙事层看 [../guides/Task0学习笔记.md](../guides/Task0学习笔记.md) ｜ 命令层看 [../guides/Task0操作手册.md](../guides/Task0操作手册.md) ｜ 本文 = 坑位层。
> 时间：2026-09-14（开营冲刺）｜ 统计：实质坑 7 ｜ 认知项 1

## A. 环境类

### A1 国内网络 git clone 仅 20-30KiB/s ✅解决

- 现象：clone 长时间低速（20-30KiB/s）
- 处置：使用加速代理并配置 git 全局代理配置，速度达 8-9MiB/s
- 证据：[clone 成功](../assets/20260914_step2_clone_ok.png)

### A2 跨盘符硬链接：uv 缓存 C 盘 / 项目 E 盘 ✅解决

- 现象：缓存目录在 C 盘、项目在 E 盘，跨盘符没法硬链接，uv 提示 warning
- 处置：设置 uv 缓存路径到 E 盘 + 链接模式环境变量，复跑验证通过
- 证据：[报错](../assets/20260914_step4_uv_cachewarn.png)｜[处理](../assets/20260914_step4_uv_envfix.png)｜[验证](../assets/20260914_step4_uv_reverify.png)
- 后续：本机沙箱内 uv 写工作区外缓存仍受限（os error 5，AGENTS.md §3 实测备忘），现行一律 `.venv\Scripts\python.exe`

### A3 管道模式子进程 stdout 默认 GBK，上游日志 emoji 抛 UnicodeEncodeError ✅解决

- 现象：执行 context 实验报 GBK 编码错误，被 agent 误当"任务错误"记录
- 根因：上游日志带 emoji；Windows 管道模式下子进程 stdout 默认 GBK，编码失败抛 UnicodeEncodeError
- 处置：run.py 给子进程加强制 `PYTHONIOENCODING=utf-8` 并 UTF-8 解码读回，父进程侧另加 `errors="replace"` 保险
- 证据：[报错](../assets/20260914_step8_gbk_err.png)｜[修复](../assets/20260914_step8_gbk_fix.png)

## B. 上游 / 文档 drift 类

### B1 上游 main.py 对 create_sample_pdf.py 的相对路径假设 ✅解决（上游已还原）

- 现象：示例 PDF 的生成工具报路径错误
- 根因：[chapter1/context/main.py:692](../../../../chapter1/context/main.py)、1023 行以相对路径引用 `create_sample_pdf.py`，依赖"cwd=实验目录"这一隐含假设
- 当时处置：临时改上游两处为基于脚本自身位置的绝对路径；**后按「上游零修改」铁律还原**（判据：`git diff origin/main` 对该文件无差异）
- 根治：run.py 统一以 cwd=实验目录启动（[run.py:55](../../../../learn/ch1/run.py) `cwd = entry.parent`），相对路径天然可达，无需改上游
- 证据：[报错](../assets/20260914_step6_pdfpath_err.png)｜[处理](../assets/20260914_step6_pdfpath_fix.png)｜[命令行验证成功](../assets/20260914_step6_pdfpath_ok.png)

### B2 仓库 README 与实际文件 drift：run_experiment_7_2 vs 8_2 ✅澄清

- 现象：README 引用 `run_experiment_7_2.py`，实际文件为 `run_experiment_8_2.py`
- 处置原则：文档与代码冲突时，以本地代码 + 实测为最终裁判（AGENTS.md §2.1 已记录的先例）
- 证据：AGENTS.md §2.1

## C. 操作类

### C1 未激活 uv、未显式指定 provider ✅解决

- 现象：运行第一章 main.py 连接大模型报错
- 处置：激活后带显式 provider 参数执行，成功连接智普
- 证据：[报错](../assets/20260914_step6_mainpy_err.png)｜[成功](../assets/20260914_step6_mainpy_zhipu_ok.png)
- 后续：现行统一走 run.py 契约注入（env 槽位 + cwd 启动），provider 由路由层 `learn.router.resolve` 决定

## D. 工程类

### D1 适配层 --evidence 模式静默捕获子进程输出 ✅解决

- 现象：执行无流式输出，直到跑完才打印（被 ctrl+c 强制停止）
- 根因：learn 适配层 --evidence 模式会静默捕获子进程全部输出
- 处置：给 run.py 加流式打印
- 证据：[现场](../assets/20260914_step8_nostream_err.png)｜[修复](../assets/20260914_step8_nostream_fix.png)

### D2 证据双轨与影像边界 ℹ️认知

- 结论：`chapter1/**/validation/`（作者基线轨）与 `learn/chN/evidence/`（acceptance_router 第二轨）**永不混同**；本人截图属过程影像，只进 `notes/assets/`，不进 evidence/（后者 json 入库、png 忽略，见 [learn/.gitignore](../../.gitignore)）
- 依据：AGENTS.md §2.5、learn/README.md 目录导航

## 人工复盘（本人已答，非 AI 代写）

1. A1–A3 三个环境坑的共同根因是什么？「权威源」应按什么优先级排序？

   - 没有提前检测环境，但是也没必要，很多问题都是边做边改进，但是需要记录。

   - 实测验证>项目主文档（多数作者习惯先改主文档）>子目录文档（作者忘记同步或他人变更合并后未更新文档）

2. D1 的定位靠"读适配层源码找捕获逻辑"、A3 靠"顺编码链路分析"——这两个方法还能迁移到什么排查场景？

   - 其实都是一个道理，问题溯源，再根本解决，不要想着走捷径。

3. 用自己的话重述 B1 的原则（上游代码的路径/资源假设与运行目录相关，以脚本自身位置为基准），并各举一个 Task 0 之外的新例子。

   - 煞笔AI，什么问题，还没有做Task0以外的，不过其它项目有类似问题，主要看是特意设计还是真bug，真bug必须修复。以后再完善此回答。

