# HANDOFF · 工具迭代会话分册

> 职责：证据中文报告器（render_report + report/ 包）、SVG 速览、probes/infra 工具链的迭代。
> 路由与铁律见 [../HANDOFF.md](../HANDOFF.md)。

## 工具地图

| 工具 | 位置 | 说明 |
| --- | --- | --- |
| 证据中文报告器 | `learn/infra/render_report.py` + `learn/infra/report/`（core.py 校验 / transforms/ 四实验转换器 / __init__.py 显式注册） | 五形状自动识别 → 中文 HTML（研究型编辑风，动效可降级） |
| SVG 速览 | `learn/infra/render_ablation_figure.py` | context 消融「书图预期 vs 实测」对照图（笔记嵌图用，GitHub 可渲染） |
| 第二轨验收 | `learn/infra/acceptance_router.py` | 变体证据落 `learn/chN/evidence/`（json 入库、png 忽略） |
| 探测样板 | `learn/infra/probe_utils.py` | probes 公共设施（key 只从根 .env） |

## 迭代原则（违者返工）

1. **证据正典**：evidence json 只转录不改写（run.py 转录 = 纯复制零解析）；渲染品不入 evidence/，落 notes/assets/
2. **上游零修改零 import**（chapter1/**、agentbook/**）
3. **渲染内核与 core.py 零实验知识**——实验知识只进 transforms/<exp>.py；加实验 = 新文件 + `report/__init__.py` 注册一行（+ 可选 contracts.artifacts 补声明）
4. **视觉/动效**遵循 spec〈视觉与交互规范〉（研究型编辑风；prefers-reduced-motion 降级；单文件自包含无外部资源）

## 关键文档

- spec 三件套：`.trae/specs/add-evidence-report-renderer/{spec,tasks,checklist}.md`
  （spec 含**数据形状普查**：四实验上游 json 四种形状实证——新形状接入前先普查）
- 设计文档：[证据中文报告器设计-2026-09-16.md](ch1/notes/guides/证据中文报告器设计-2026-09-16.md)
- 验收基线：checklist 27 项全过；核对方法 = **Report 值与源 json 同字段逐值程序比对**（9 样本基线在 tasks.md 实施记录）

## 状态与已知问题（迭代候选）

- 未提交：报告器全套 + 转录机制（工作区 M/untracked，等本人说提交）
- 已知遗留：search_codegen 的 receipts.json 与 evidence.json 同目录关联读取未实现（现需 `--input` 直接指 receipts.json）
- 迭代候选：`--all` 批量渲染 evidence/ 全部 json + 索引页；转换器对上游 schema 演进的兼容测试；报告深色主题（低优先）
- 运行注意：`--open` 会阻塞（serve_forever），沙箱内验证用 `--output` 写文件 + 断言即可，服务留给本人浏览

## 更新约定

工具状态/已知问题随迭代更新本册；新工具入「工具地图」；接入新实验形状前先做数据形状普查并更新 spec。
