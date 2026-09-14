# ch1 五实验：前因后果、原理与操作指南

> 定位：学习者本人执行手册（AI 起草、本人审定；结论均带 文件:行号 引用，行号允许 ±几行偏差）。
> 分工依据：实验由本人运行，AI 负责讲解、命令准备与结果判读辅助（[AGENTS.md §1](../../../../AGENTS.md)）。
> 日期：2026-09-14 ｜ Task 0 截止：09-17 03:00（见 [learn/README.md 映射表](../../../README.md)）。

---

## 0. 运行前三查（一次性）

1. **解释器**：一律 `.venv\Scripts\python.exe`（不要 `uv run`，[AGENTS.md §3](../../../../AGENTS.md)）。
2. **依赖实测（2026-09-14）**：openai / requests / dotenv / pypdf / tabulate / matplotlib 均 OK；
   `google-genai` 未安装——**不影响本指南全部命令**（1-4 的 gemini 路线本就不在变体轨道，
   且它是函数内 lazy import，`chapter1/image-gen-workflow/pipeline.py:242`）。
3. **密钥**：只存根 `.env`，现有变量名：`DASHSCOPE_API_KEY`、`DASHSCOPE_BASE_URL`、
   `ZHIPU_API_KEY`、`AGNES_API_KEY`、`MIMO_API_KEY`（无 `OPENAI_API_KEY`/`MOONSHOT_API_KEY`，
   这决定了 1-2/1-3 必须走路由变体——见各实验说明）。

## 0.5 三层适配结构（理解后再跑）

```
你的命令
  └─ learn/ch1/run.py            统一启动器：契约注入 env + cwd=实验目录 + 原样跑上游入口（run.py:50-55）
       └─ learn/ch1/contracts.py 契约表：路由解析结果 → 上游代码要读的 env 槽位（contracts.py:92-99）
            └─ learn/router/     路由层：model_config.json 决定每个任务用哪家哪个模型（model_config.json:21-32）
```

三条铁则：
1. **槽位名 ≠ 厂商**：`KIMI_*`/`DASHSCOPE_*` 是上游代码定义的槽位名，真实 provider/model 只记录在证据 json
   （例：[contracts.py:26-29](../../contracts.py) 把智谱的 key/url 填进 `KIMI_*` 槽位，因为上游 1-4 改写节点读 `KIMI_*`）。
2. **base_url 支持 env 覆盖**：上游注册表 `key_vars`/`base_url_var` 均可被环境变量覆盖
   （`agentbook/providers/models.py:72`；dashscope 条目见 `agentbook/providers/registry.py:26-36`）。
3. **上游零修改**：所有适配经契约注入，判据 `git diff origin/main --name-status` 对上游路径无 M/D。

运行须知：`run.py --evidence` 会**实时流式转发**子进程输出并照常落盘证据 json
（2026-09-14 修复，原为静默捕获、终端长时间无输出易被误判卡死）；Ctrl+C 会 kill 子进程、
不写证据、无孤儿进程。子进程已被强制 `PYTHONIOENCODING=utf-8`（2026-09-14 修复：
Windows 管道模式下子进程默认 GBK 编码，上游 verbose 日志的 emoji（如 agent.py:619 的 📤）
会抛 `UnicodeEncodeError`——注意此时 API 调用本身是成功的，坏在打印；真终端无此问题，
因为控制台走 Unicode 通道）。

路由表速查（[model_config.json:21-32](../../../router/model_config.json)）：

| 路由 | 模型 | 服务的实验 |
|---|---|---|
| `text_only` | zhipu/glm-5.3-flash | 1-1、1-4 改写节点、7-2 LLM 轨 |
| `inline_search` | zhipu/glm-5.3-flash + web_search 工具 | 1-2 builtin |
| `web_search_api` | zhipu（独立 /web_search 端点） | 1-2 react 执行器 |
| `image_workflow` | dashscope/wan2.2-t2i-flash | 1-4 生图节点 |
| `image_native` | agnes/agnes-image-2.0-flash | 1-4 原生路线 B |
| `deep_research` | dashscope/qwen3.7-plus | 1-3 |

## 0.8 执行顺序总表（成本从低到高）

| 步 | 实验 | 命令（详见各节） | 证据落点 |
|---|---|---|---|
| ① | 预检 | `run.py --list` | —（零 API） |
| ② | 1-2 | 亲自跑变体两模式 + `acceptance_router.py builtin` / `react` | `learn/ch1/evidence/` |
| ③ | 7-1 | `run.py --exp learning-from-experience -- --mode qlearning --seed 42` | stdout + results/ |
| ④ | 7-2 | `run.py --exp learning-from-experience --evidence` | `learn/ch1/evidence/` |
| ⑤ | 1-1 | `run.py --exp context --evidence -- --mode ablation --cases 3` | `learn/ch1/evidence/` |
| ⑥ | 1-4 | `run.py --exp image-gen-workflow --evidence -- --route …` ×2 + acceptance | `learn/ch1/evidence/` |
| ⑦ | 1-3 | `run.py --exp search-codegen --evidence -- --backend dashscope --mode single …` | `learn/ch1/evidence/` |

每个实验完成后：确认证据 json 在 `learn/ch1/evidence/` → 判读结果（AI 可协助）→
心得本人撰写 → 更新 [HANDOFF.md](../../../HANDOFF.md) 状态快照 → commit 仅在明确说"提交"时执行。

---

## 1. 实验 1-1 context（上下文消融）

### 1.1 前因后果

全书方法论地基：**消融实验（ablation study）**。同一任务跑 5 次，每次只去掉上下文的一个成分，
观察行为退化。它证明"agent 的能力不在模型里，而在喂给模型的上下文里"。

### 1.2 原理与实现走读

- 五种模式（`chapter1/context/agent.py:44-50`）：`full` / `no_history` / `no_reasoning` /
  `no_tool_calls` / `no_tool_results`。
- 主循环是标准 **ReAct**（`agent.py:703-959`）：每轮把完整 messages 发给模型 → 返回 `tool_calls`
  则执行本地工具（parse_pdf / convert_currency / calculate / code_interpreter，`agent.py:75-377`）
  → 结果追加回 messages。
- 四个消融臂动的刀：
  - `no_history`：请求只保留 system + 最新 user（`agent.py:662-694`）→ 模型每轮失忆，预期原地打转；
  - `no_reasoning`：历史里剥掉 `reasoning_content`（`agent.py:536-553`）；
  - `no_tool_calls`：请求不带 `tools` 定义（`agent.py:767-769`）→ 模型没工具可用；
  - `no_tool_results`：工具消息替换为空串（`agent.py:879-895`；两种口径见 `agent.py:33-41`）
    → 最阴险：模型看得见"工具消息存在"却看不到内容，**预期它凭记忆编造汇率数字**。
- **grounding 判定**（`chapter1/context/main.py:38-58`）：结局三态
  `completed` / `unsupported_numbers`（答案含任何观测都不支持的数字=编造）/ `no_terminal_response`。
  "有礼貌地答完"≠成功——心得最该展开的点。

### 1.3 操作步骤（落证据）

```powershell
# 主推：3 个本地化案例（跳过需联网抓 GitHub PDF 的默认案例，依据 main.py:791-809）
.venv\Scripts\python.exe learn\ch1\run.py --exp context --evidence -- --mode ablation --cases 3

# 备选：书稿默认的 Multinational Budget 案例（需访问 raw.githubusercontent.com，网络不通用上面的）
.venv\Scripts\python.exe learn\ch1\run.py --exp context --evidence -- --mode ablation
```

适配器自动透传 `--provider zhipu --model glm-5.3-flash`（contracts.py:68-80；
zhipu 在上游注册表 `agentbook/providers/registry.py:66-71`，`SUPPORTED_PROVIDERS` 于 :142 汇总）。

产物：`chapter1/context/` 下 `ablation_results.json`、`ablation_study_report.md`、
`ablation_study_results.png`；证据 json 落 `learn/ch1/evidence/<ts>_run_context.json`。

### 1.4 预期观察

- 对比矩阵五臂的 `✓/⚠/✗` 与 iterations / tool_calls / grounding 列；
- `no_history` 是否重复同一动作；`no_tool_results` 是否 `⚠ unsupported_numbers`；
- 实测备注：glm-5.3-flash 若不返回 `reasoning_content`，`no_reasoning` 臂退化为"无操作臂"
  ——这本身是值得记录的发现（不同模型表现不同，无标准答案）。

---

## 2. 实验 1-2 web-search-agent（ReAct + 联网搜索）

### 2.1 前因后果

演示"模型即 Agent"：不加外部编排框架，模型自己决定何时搜索、搜几轮、何时收束。
上游 `chapter1/web-search-agent/main.py`（Kimi K3 + Moonshot Formula 托管搜索）为验收锚定，
**一字不动**；因 `.env` 无 `MOONSHOT_API_KEY`，走 Task 0 备好的路由变体入口
`learn/ch1/variants/web-search-agent/main_route.py`。

### 2.2 原理与实现走读（两种"模型用搜索"形态对照）

- **builtin 服务端内联**（`main_route.py:41-61`）：`inline_search` 路由的模型自带 web_search，
  一次调用出答案，引用挂响应顶层 `web_search` 字段。快，但过程黑盒。
- **react 客户端编排**（`main_route.py:83-135`）：脑 = `text_only`，执行器 = `web_search_api`
  （独立搜索端点，`main_route.py:64-80`）。每轮打印 💭思考 → 🔧搜索词 → 👀结果，最多 5 轮，
  轨迹全可见、可干预。

### 2.3 操作步骤（本人运行 + 落证据）

> **澄清（2026-09-14）**：Task 0 探测期曾由 AI 代办跑过一次 builtin 路由冒烟
> （原文件 20260914T105129_builtin.json，现已删除），它只证明"管道通"，**不是实验运行**。
> 五个实验本人均未运行过——1-2 的两个模式都由你亲自跑，验收器产生的带新时间戳的
> 证据才算你的记录。

第一遍·学习性运行（轨迹全程可见，可反复换问题玩）：

```powershell
.venv\Scripts\python.exe learn\ch1\variants\web-search-agent\main_route.py "现在比特币的价格是多少美元？" --mode builtin
.venv\Scripts\python.exe learn\ch1\variants\web-search-agent\main_route.py "2026 年图灵奖得主是谁？其主要贡献是什么？" --mode react --max-rounds 5
```

第二遍·正式证据（验收器会重新执行一次并写入 `learn/ch1/evidence/<新时间戳>_<target>.json`）：

```powershell
.venv\Scripts\python.exe learn\infra\acceptance_router.py builtin
.venv\Scripts\python.exe learn\infra\acceptance_router.py react
```

### 2.4 预期观察

- 两种形态在延迟、引用可溯性、多轮纠错能力上的差异；
- react 模式下模型搜索词如何随轮次演进（越搜越准还是发散）。

---

## 3. 实验 1-3 search-codegen（托管 Deep Research）⚠️ 有坑

### 3.1 前因后果

1-2 的工具在客户端执行；1-3 的 `web_search` / `code_interpreter` 是 Responses API 的
**托管工具**——搜索和 Python 沙箱都在 provider 服务端跑。范式变化：**验收只能依据 provider
返回的工具回执**（`web_search_call` / `code_interpreter_call` 条目），"文本里说自己用了
Python"不算数（`chapter1/search-codegen/README.md:51-55`）。第二场景专测**意图澄清**：
模糊请求先问清数据源与指标再动手，靠 `previous_response_id` 续接。

### 3.2 原理与实现走读

- backend 解析：`chapter1/search-codegen/config.py:51-65` 的 `resolve()`；`--backend` 默认
  `Config.BACKEND = os.getenv("BACKEND", "openai")`（`config.py:38`）。
- dashscope 后端走 `{DASHSCOPE_BASE_URL}/responses` 且必须流式（README:34-49；
  网关对静默 60s 的非流式请求直接掐断）。
- 作者验收结论（README:74-97）：官方 GPT-5.6 路径配额阻塞，**阿里云百炼 qwen3.7-plus
  实测通过全部验收门**——即 `deep_research` 路由（书稿基准：吉隆坡–新加坡 ≈316.35 km）。

### 3.3 ⚠️ 坑：HANDOFF 原命令直接跑会失败（2026-09-14 实测复现）

实测运行 `run.py --exp search-codegen` 的输出（exit 1，失败发生在任何 API 调用之前）：

```
Error: no API key for openai
❌ 配置错误！
请配置所选 backend 对应的 OPENAI_API_KEY / OPENROUTER_API_KEY / DASHSCOPE_API_KEY
```

原因链：契约只注入 `DASHSCOPE_API_KEY/BASE_URL/MODEL` 三个变量（contracts.py:43-50），
上游 `--backend` 默认 openai（config.py:38），`.env` 无 `OPENAI_API_KEY` → 校验失败
`sys.exit(1)`（`chapter1/search-codegen/main.py:416-421`）。且默认交互模式在 `--evidence`
（stdin 为 EOF）下会空转到 1800s 超时。**必须透传 backend 与 single 模式**（见 3.4）。

### 3.4 操作步骤（落证据）

```powershell
# 场景一：东盟首都（搜索 + 代码执行闭环）
.venv\Scripts\python.exe learn\ch1\run.py --exp search-codegen --evidence -- --backend dashscope --mode single --request "东盟 10 国首都之间，距离最近的两个首都是？给出你的详细分析推理过程。" --output asean_result.json

# 场景二：模糊请求测澄清（首轮应不调任何工具、先反问）
.venv\Scripts\python.exe learn\ch1\run.py --exp search-codegen --evidence -- --backend dashscope --mode single --request "搜索最近一年比特币的价格，计算收益率、最大回撤等重要指标"
```

注：契约注入的 `DASHSCOPE_BASE_URL` 为国内站 `dashscope.aliyuncs.com`（model_config.json:7），
上游 config 默认国际站——国内站已被 Task 0 探针 t11 实测可用。

### 3.5 预期观察

- 场景一结果含 `web_search_call` 与 `code_interpreter_call` 回执、可点击引用、正确最近首都对；
- 场景二首轮零工具调用、列出澄清问题；用户补充后（交互模式）才执行搜索+计算。

---

## 4. 实验 1-4 image-gen-workflow（工作流 vs 原生）

### 4.1 前因后果

最有工程哲学味的实验：老一代文生图模型吃不下口语化中文，业界搭"改写节点"翻译人话——
**外置适配层**；新一代原生多模态模型直接理解人话出图。同一句话走两条路线，回答：
适配层是必要的工程，还是将被模型内化的历史包袱？书稿经典发现
（`chapter1/image-gen-workflow/README.md:124-150`）：改写节点干三件事（翻译、具象化、
自作主张定风格），海报用例里它把用户指定文案丢进 negative_prompt——忠实度反而输给原生路线。

### 4.2 原理与实现走读

- workflow 路线 = 改写节点（OpenAI 兼容 chat，`pipeline.py:110-142`）→ 万相异步任务
  （提交/轮询/下载，`pipeline.py:150-227`）；
- native_gptimage 路线 = `images/generations` 一次出图（`pipeline.py:299-341`）；
- 契约注入后的实际栈（contracts.py:20-40）：改写 = zhipu glm-5.3-flash（占 `KIMI_*` 槽）、
  生图 = wan2.2-t2i-flash（`DASHSCOPE_*` 槽，base_url 覆盖为国内站 `…/api/v1`）、
  原生 B = agnes-image-2.0-flash（`OPENAI_*` 槽）；
- gemini 原生路线不在变体轨道（`GEMINI_API_KEY` 为占位符 + google-genai 未装）。

### 4.3 操作步骤（落证据）⚠️ 不能用默认 `--route all`

`ALL_ROUTES = ["workflow", "native", "native_gptimage"]`（`chapter1/image-gen-workflow/main.py:130`），
`all` 会撞上不可用的 `native`（gemini）路线。

```powershell
# 宽泛需求主用例：两路线对照
.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow --evidence -- --route workflow --requirement agi-programmer
.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow --evidence -- --route native_gptimage --requirement agi-programmer

# 进阶对照：具体需求（海报文案用例最能看出改写节点的取舍）
.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow --evidence -- --route workflow --requirement headphone-poster
.venv\Scripts\python.exe learn\ch1\run.py --exp image-gen-workflow --evidence -- --route native_gptimage --requirement headphone-poster

# 第二轨补跑（标准证据；acceptance_router.py:118-123）
.venv\Scripts\python.exe learn\infra\acceptance_router.py workflow --requirement agi-programmer
.venv\Scripts\python.exe learn\infra\acceptance_router.py native --requirement agi-programmer
```

图片落 `chapter1/image-gen-workflow/outputs/<run_id>/images/`（该目录 .gitignore 已忽略 outputs/）。

### 4.4 ⚠️ 证据分轨提醒（铁律 4）

上游脚本每次运行会把 manifest 写进 `chapter1/image-gen-workflow/validation/real_<run_id>/`
（`main.py:177-183`）。**变体运行写进去的 manifest 属第二轨性质，不得混同作者基线**：
变体证据以 `learn/ch1/evidence/` 的 json 为准；这些副作用目录判读完后建议删除
（ outputs/ 可留，validation/real_<变体 run_id>/ 建议清掉或明确标注为变体副作用）。

### 4.5 预期观察

- 改写输出的 `prompt / negative_prompt / style_notes` 对照原始需求找"翻译/具象化/自作主张"；
- 万相响应的 `actual_prompt` 字段——服务端自己又扩写了一次（"托管服务也开始内置改写层"的活证据）；
- 两条路线的图对原始需求的满足度（宽泛需求看具象化增益，具体需求看忠实度）。

---

## 5. 实验 7-1 & 7-2 learning-from-experience（RL vs LLM）

### 5.1 前因后果

复刻 Shunyu Yao《The Second Half》核心论点。寻宝游戏有**隐藏机制**（颜色锁、武器相克、
合成系统、药水，`chapter1/learning-from-experience/README.md:66-72`），agent 只能从试错悟规则。
两种学习机制同台：7-1 = **表格型 Q-learning**（10000 局，ε-greedy，黑盒状态-动作表）；
7-2 = **LLM 上下文学习**（经验入 prompt 靠推理泛化，20 局）。验证四件事
（README:20-23）：样本效率、泛化方式、先验知识作用、隐藏机制发现路径。

### 5.2 原理与实现走读

- Q-learning 完全离线零 API（秒级跑完），`rl_agent.py` 维护 Q 表；
- LLM 轨：经验存为 `(state, action, feedback, reward, success)` 五元组
  （`chapter1/learning-from-experience/llm_agent.py:51-58`），决策时把近期成功模式注入 prompt；
- provider 解析：`LLM_PROVIDER=dashscope` 分支走注册表（`llm_agent.py:86-101`）——契约把
  zhipu 的 key/url/model 注入 `DASHSCOPE_*` 槽位（contracts.py:53-65），**名为 dashscope、
  实调智谱 glm-5.3-flash**。

### 5.3 操作步骤（落证据）

```powershell
# 7-1 先行：零成本看 Q-learning 学习曲线
.venv\Scripts\python.exe learn\ch1\run.py --exp learning-from-experience -- --mode qlearning --seed 42

# 7-2 完整对照（Q-learning 10000 局 + LLM 20 局 + 100 局贪心评估；默认 mode=both）
.venv\Scripts\python.exe learn\ch1\run.py --exp learning-from-experience --evidence

# 第二轨补跑（1 局 LLM 冒烟，acceptance_router.py:126-139）
.venv\Scripts\python.exe learn\infra\acceptance_router.py llm
```

产物在 `chapter1/learning-from-experience/results/`（学习曲线表、rl_agent.pkl、llm_experiences 等）。
若 LLM 20 局太慢，可先 `-- --mode llm --llm-episodes 3` 缩规模看原理。

### 5.4 预期观察

- Q-learning 曲线第几局开始稳定获胜（黑盒的代价 = 样本量）；
- LLM 推理文本是否**用语言归纳出隐藏机制**（如"红钥匙开警卫室的门"）；
- 20 局 vs 10000 局的样本效率对比；作者基线参照：
  `chapter1/learning-from-experience/validation/20260730_011704/`（Kimi 17 步成功）。

---

## 6. 收尾清单（每个实验完成后）

1. 证据确认：`learn/ch1/evidence/` 出现本次 `<ts>_run_<exp>.json` 或 `<ts>_<target>.json`，
   里面 `kind: "variant"`、记录真实 provider/model；
2. 分轨检查：变体运行在 `chapter1/**/validation/` 留下的副作用目录（1-4 必有）已删除或标注；
3. 心得本人撰写（AI 只做格式建议，不代写观点）；
4. 更新 [HANDOFF.md](../../../HANDOFF.md) 的"当前任务/状态快照"；
5. `commit` 仅在明确说"提交"时执行；push 需单独确认。

## 7. 成本提示（以各控制台与实测为准）

- glm-5.3-flash：flash 档，1-1/1-2/7-2 大量调用也便宜；
- wan2.2-t2i-flash / agnes-image-2.0-flash：按张计费，1-4 每次运行 1-2 张；
- qwen3.7-plus（1-3）：最贵最慢，放最后，单场景一次通过即可。
