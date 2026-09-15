"""context 实验转换器：三种输入形状 → Report（一律经 core.make_report 校验后返回）。

形状指纹（matches）与分支：
1. list 且首记录含 context_mode —— 第二轨 summary 消融证据（learn/ch1/evidence/*_context_*_results.json）
2. dict 含 arms 与 schema_version —— 上游验收正典（chapter1/context/validation/latest.json、real_*/evidence.json）
3. dict 含 context_mode 与 tool_calls —— 单任务运行（chapter1/context/task_result_*.json）

上游 arms 形状 badge 映射规则（outcome 取值全集见 chapter1/context/run_experiment_1_1.py
arm_outcome L307-L339，verdict 取值全集见 chapter1/context/grounding.py L182-L194；
忠实原文语义，不臆造）：
- outcome="no_terminal_response"（未给出终局响应）→ {"text": "✗", "kind": "fail"}
- outcome="incorrect"（完成但答案未通过 rubric）→ {"text": "✗", "kind": "fail"}
- outcome="unsupported_numbers"（答案含无观测支撑数字）→ {"text": "⚠", "kind": "warn"}
- outcome="correct"（答案通过 rubric）→ {"text": "✓", "kind": "ok"}
- outcome="no_unsupported_numbers"（答案无编造数字，含原则性拒答）→ {"text": "✓", "kind": "ok"}
- outcome 缺失或未知时按 verdict 兜底：ungrounded → {"text": "⚠", "kind": "warn"}、
  no_answer → {"text": "✗", "kind": "fail"}；其余 → {"text": <outcome 原文或"？">, "kind": "na"}
outcome 是上游已折叠的结论词，故 outcome 优先于 verdict。

第二轨 summary badge 规则（与 spec 一致）：completed 为假或 has_final_answer 为假 →
{"text": "✗", "kind": "fail"}；grounding_verdict="ungrounded" → {"text": "⚠", "kind": "warn"}；
否则 {"text": "✓", "kind": "ok"}。

单任务 badge 规则：success 为真 → {"text": "✓", "kind": "ok"}，否则 → {"text": "✗", "kind": "fail"}。

第二轨分支的臂中文名与书图预期文案复用 learn/infra/render_ablation_figure.py 的
ARM_CN / BOOK_EXPECTATION（单一事实源）。未知字段宽容：未映射字段原文落入 kv「其他字段」。
"""

import json
from pathlib import Path

from learn.infra.render_ablation_figure import ARM_CN, BOOK_EXPECTATION
from learn.infra.report.core import make_report

EXP = "context"

_TRUNC_LIMIT = 200

_OUTCOME_BADGE = {
    "no_terminal_response": ("✗", "fail"),
    "incorrect": ("✗", "fail"),
    "unsupported_numbers": ("⚠", "warn"),
    "correct": ("✓", "ok"),
    "no_unsupported_numbers": ("✓", "ok"),
}

_ARM_REPRESENTED = frozenset({
    "mode", "provider", "model", "completed", "elapsed_seconds", "iterations",
    "outcome", "groundedness", "behavior", "final_answer", "reasoning_steps",
    "tool_call_signatures", "tool_calls", "repeated_tool_calls",
})

_SINGLE_HANDLED = frozenset({"context_mode", "tool_calls", "final_answer", "iterations", "success"})


def matches(raw):
    if isinstance(raw, list):
        return bool(raw) and isinstance(raw[0], dict) and "context_mode" in raw[0]
    if isinstance(raw, dict):
        if "arms" in raw and "schema_version" in raw:
            return True
        return "context_mode" in raw and "tool_calls" in raw
    return False


def transform(raw, source_path=None):
    if isinstance(raw, dict):
        if "arms" in raw and "schema_version" in raw:
            return _arms_report(raw)
        if "context_mode" in raw and "tool_calls" in raw:
            return _single_report(raw, source_path)
    if matches(raw):
        return _track2_report(raw, source_path)
    raise ValueError("context 转换器不识别该 json 形状（判据见 matches）")


def _dump(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def _trunc(text):
    if len(text) <= _TRUNC_LIMIT:
        return text
    return text[:_TRUNC_LIMIT] + "…"


def _kv(value):
    if isinstance(value, str):
        return value
    return _dump(value)


def _num(value):
    if value is None:
        return ""
    return str(value)


def _arms_report(raw):
    meta = [
        f"experiment_id: {_kv(raw.get('experiment_id'))}",
        f"canonical_source: {_kv(raw.get('canonical_source'))}",
        f"created_at: {_kv(raw.get('created_at'))}",
    ]
    expected = raw.get("expected_numbers")
    if expected:
        meta.append("expected_numbers: " + ", ".join(_kv(n) for n in expected))
    meta.append("数据源为上游验收正典，非本仓第二轨")
    return make_report({
        "title": "context 实验报告（上游验收数据）",
        "meta": meta,
        "task": raw.get("task"),
        "summary_columns": [
            {"key": "arm", "title": "消融臂"},
            {"key": "provider_model", "title": "provider·model"},
            {"key": "completed", "title": "跑完?", "align": "center"},
            {"key": "elapsed", "title": "耗时(s)", "align": "center"},
            {"key": "iterations", "title": "轮次", "align": "center"},
            {"key": "tool_action_count", "title": "工具调用次数", "align": "center"},
            {"key": "outcome", "title": "结论"},
            {"key": "grounding", "title": "grounding"},
        ],
        "arms": [_arm(a) for a in raw.get("arms") or []],
        "footnotes": [
            "badge 由 outcome 与 groundedness.verdict 推导（映射规则见 learn/infra/report/transforms/context.py 模块 docstring）",
            "推理过程/工具调用签名/工具调用明细为上游 arms 形状全文转录，非计数降级",
        ],
    })


def _arm(a):
    mode = a.get("mode", "?")
    cn = ARM_CN.get(mode, mode)
    groundedness = a.get("groundedness")
    verdict = groundedness.get("verdict") if isinstance(groundedness, dict) else None
    behavior = a.get("behavior") if isinstance(a.get("behavior"), dict) else {}
    return {
        "name": cn,
        "code": mode,
        "badge": _arms_badge(a.get("outcome"), verdict),
        "cells": {
            "arm": f"{cn}（{mode}）",
            "provider_model": f"{_kv(a.get('provider'))}·{_kv(a.get('model'))}",
            "completed": "✓" if a.get("completed") else "✗",
            "elapsed": _num(a.get("elapsed_seconds")),
            "iterations": _num(a.get("iterations")),
            "tool_action_count": _num(behavior.get("tool_action_count")),
            "outcome": _kv(a.get("outcome")),
            "grounding": _kv(verdict),
        },
        "sections": [
            _answer_section(a.get("final_answer")),
            _steps_section("推理过程", a.get("reasoning_steps")),
            _steps_section("工具调用签名", a.get("tool_call_signatures")),
            _tool_table_section(a.get("tool_calls") or []),
            _grounding_kv_section(a, groundedness, behavior),
            {"title": "其他字段", "kind": "kv", "pairs": _other_pairs(a)},
        ],
    }


def _arms_badge(outcome, verdict):
    if outcome in _OUTCOME_BADGE:
        text, kind = _OUTCOME_BADGE[outcome]
        return {"text": text, "kind": kind}
    if verdict == "ungrounded":
        return {"text": "⚠", "kind": "warn"}
    if verdict == "no_answer":
        return {"text": "✗", "kind": "fail"}
    return {"text": outcome if isinstance(outcome, str) and outcome else "？", "kind": "na"}


def _answer_section(final_answer):
    if final_answer:
        return {"title": "最终答案", "kind": "pre", "text": final_answer}
    return {"title": "最终答案", "kind": "note", "text": "无终局答案"}


def _steps_section(title, values):
    if isinstance(values, list):
        items = [v if isinstance(v, str) else _dump(v) for v in values]
        return {"title": title, "kind": "list", "items": items}
    return {"title": title, "kind": "note", "text": _dump(values)}


def _tool_table_section(calls):
    rows = []
    for call in calls:
        if isinstance(call, dict):
            args = call.get("arguments")
            result = call.get("result")
            args_text = _trunc(_dump(args)) if args is not None else ""
            result_text = _trunc(_dump(result)) if result is not None else ""
            summary = args_text + (f" ⇒ {result_text}" if result_text else "")
            rows.append([_kv(call.get("tool_name")), summary, _kv(call.get("timestamp"))])
        else:
            rows.append([_trunc(_kv(call)), "", ""])
    return {"title": "工具调用明细", "kind": "table", "headers": ["工具名", "参数摘要", "时间戳"], "rows": rows}


def _grounding_kv_section(a, groundedness, behavior):
    pairs = [["outcome", _kv(a.get("outcome"))]]
    if isinstance(groundedness, dict):
        for key in ("observation_count", "answer_quantities", "unsupported_quantities", "verdict"):
            if key in groundedness:
                pairs.append([f"groundedness.{key}", _kv(groundedness[key])])
    elif groundedness is not None:
        pairs.append(["groundedness", _kv(groundedness)])
    for key, value in behavior.items():
        pairs.append([f"behavior.{key}", _kv(value)])
    pairs.append(["repeated_tool_calls", _kv(a.get("repeated_tool_calls"))])
    return {"title": "grounding 与行为", "kind": "kv", "pairs": pairs}


def _other_pairs(a):
    return [[key, _trunc(_kv(value))] for key, value in a.items() if key not in _ARM_REPRESENTED]


def _track2_report(records, source_path):
    meta = []
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    else:
        meta.append("数据源：本仓第二轨证据")
    meta.append("第二轨正典 json，模型/路由见证据")
    return make_report({
        "title": "context 消融实验报告（本机实测）",
        "meta": meta,
        "summary_columns": [
            {"key": "arm", "title": "消融臂"},
            {"key": "book_expectation", "title": "书图预期"},
            {"key": "completed", "title": "跑完?", "align": "center"},
            {"key": "elapsed", "title": "耗时", "align": "center"},
            {"key": "iterations", "title": "轮次", "align": "center"},
            {"key": "tool_calls", "title": "工具调用", "align": "center"},
            {"key": "grounding", "title": "grounding 判定"},
            {"key": "unsupported", "title": "编造数字数", "align": "center"},
        ],
        "arms": [_track2_arm(r) for r in records],
        "footnotes": [
            "badge 规则：completed 为假或 has_final_answer 为假 → ✗ 未完成；grounding_verdict=ungrounded → ⚠ 有答案但编数字；否则 ✓ 正常完成",
            "书图预期为教科书概念示意（书图含“无工具定义”臂，代码未设）",
            "本报告为可视化，不入 evidence/",
        ],
    })


def _track2_arm(rec):
    mode = rec.get("context_mode", "?")
    cn = ARM_CN.get(mode, mode)
    unsupported = rec.get("unsupported_quantities") or []
    sections = [
        _track2_answer_section(rec),
        _track2_grounding_section(unsupported),
        {"title": "工具调用记录", "kind": "note", "text": f"记录粒度为计数（{rec.get('num_tool_calls') or 0} 次调用）"},
        {"title": "推理过程", "kind": "note", "text": f"记录粒度为计数（{rec.get('reasoning_steps') or 0} 步）"},
    ]
    if rec.get("error"):
        sections.append({"title": "错误信息", "kind": "kv", "pairs": [["error", _kv(rec["error"])]]})
    return {
        "name": cn,
        "code": mode,
        "badge": _track2_badge(rec),
        "cells": {
            "arm": f"{cn}（{mode}）",
            "book_expectation": BOOK_EXPECTATION.get(mode, "—"),
            "completed": "✓" if rec.get("completed") else "✗",
            "elapsed": _num(rec.get("execution_time")),
            "iterations": _num(rec.get("iterations")),
            "tool_calls": _num(rec.get("num_tool_calls")),
            "grounding": _grounding_cell(rec),
            "unsupported": _unsupported_cell(unsupported),
        },
        "sections": sections,
    }


def _track2_answer_section(rec):
    preview = rec.get("final_answer_preview")
    if preview:
        return {"title": "最终答案", "kind": "pre", "text": preview}
    return {"title": "最终答案", "kind": "note", "text": f"无终局答案（has_final_answer={_kv(rec.get('has_final_answer'))}）"}


def _track2_grounding_section(unsupported):
    if not unsupported:
        return {"title": "grounding 详情", "kind": "note", "text": "未发现编造"}
    rows = [[str(i + 1), _num(q)] for i, q in enumerate(unsupported)]
    return {"title": "grounding 详情", "kind": "table", "headers": ["序号", "编造数字（无观测支撑）"], "rows": rows}


def _grounding_cell(rec):
    verdict = _kv(rec.get("grounding_verdict"))
    if rec.get("grounding_verdict") == "ungrounded":
        return {"text": verdict, "tone": "fail"}
    return verdict


def _unsupported_cell(unsupported):
    text = f"{len(unsupported)} 个（详见臂节）" if unsupported else "0"
    if unsupported:
        return {"text": text, "tone": "fail"}
    return text


def _track2_badge(rec):
    if not rec.get("completed") or not rec.get("has_final_answer"):
        return {"text": "✗", "kind": "fail"}
    if rec.get("grounding_verdict") == "ungrounded":
        return {"text": "⚠", "kind": "warn"}
    return {"text": "✓", "kind": "ok"}


def _single_report(raw, source_path):
    meta = []
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    meta.append(f"context_mode: {_kv(raw.get('context_mode'))}")
    tool_calls = raw.get("tool_calls") or []
    final_answer = raw.get("final_answer")
    return make_report({
        "title": "context 单任务报告",
        "meta": meta,
        "summary_columns": [
            {"key": "mode", "title": "模式"},
            {"key": "elapsed", "title": "耗时"},
            {"key": "iterations", "title": "轮次", "align": "center"},
            {"key": "tool_calls", "title": "工具调用", "align": "center"},
            {"key": "success", "title": "成功", "align": "center"},
        ],
        "arms": [{
            "name": ARM_CN.get(raw.get("context_mode"), raw.get("context_mode", "?")),
            "code": _kv(raw.get("context_mode")) or "?",
            "badge": {"text": "✓", "kind": "ok"} if raw.get("success") else {"text": "✗", "kind": "fail"},
            "cells": {
                "mode": _kv(raw.get("context_mode")),
                "elapsed": _num(raw.get("execution_time")),
                "iterations": _num(raw.get("iterations")),
                "tool_calls": str(len(tool_calls)),
                "success": "✓" if raw.get("success") else "✗",
            },
            "sections": [
                {"title": "最终答案", "kind": "pre", "text": final_answer if final_answer is not None else ""},
                {"title": "工具调用记录", "kind": "list", "items": _single_call_items(tool_calls)},
                {"title": "其他字段", "kind": "kv", "pairs": [
                    [key, _trunc(_kv(value))] for key, value in raw.items() if key not in _SINGLE_HANDLED
                ]},
            ],
        }],
        "footnotes": [],
    })


def _single_call_items(tool_calls):
    items = []
    for i, call in enumerate(tool_calls, 1):
        if isinstance(call, dict):
            items.append({
                "summary": f"第{i}次 · {_kv(call.get('tool_name'))}",
                "body": _dump({"arguments": call.get("arguments"), "result": call.get("result")}),
            })
        else:
            items.append({"summary": f"第{i}次", "body": _dump(call)})
    return items
