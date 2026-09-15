"""search_codegen 实验（上游实验 1-3）转换器：两种输入形状 → Report（一律经 core.make_report 校验）。

形状指纹（matches）与分支：
1. dict 含 runs 与 acceptance —— 验收证据形状（chapter1/search-codegen/validation/latest.json、
   runs/*/evidence.json；实测顶层键 schema_version/experiment_id/evidence_mode/created_at/
   canonical_source/host/repository/credentials_recorded/independent_asean_reference/runs/
   acceptance/artifact_hashes）
2. dict 含 turns —— 回执转录形状（同 run 目录 receipts.json；实测顶层键 schema_version/
   experiment_id/created_at/note/turns，turns[i]={backend, api_turns}，
   api_turns[i]={request, http_status, response, elapsed_seconds}）

映射规则（2026-07-31 实读 runs/real_20260731T170529Z 得出）：
- 验收证据形状：runs 逐 run 一臂（code=backend，重复时加序号后缀），汇总表列
  后端/请求模型/启动/ASEAN 验收/澄清验收/API 轮数/tokens/耗时(s)；ASEAN 验收=
  asean_validation.passed、澄清验收=clarification.validation.passed、tokens=usage.total_tokens、
  耗时=asean.elapsed_seconds；badge：started 为假或两项验收皆假 → ✗ fail、两项皆真 → ✓ ok、
  部分通过 → ⚠ warn、无判据 → ？ na；另设尾臂「验收总览」（code=acceptance_overview，
  badge 取 acceptance.passed）承载 acceptance（含 per_backend 表）、independent_asean_reference
  （含 coordinates 城市坐标表）、artifact_hashes 折叠节
- 回执转录形状：title 注明「回执转录」，turns 逐 backend 一臂（badge 显示「转录」·na，回执无
  验收语义），api_turns 逐轮 list 节全文转录（summary=轮次·HTTP 状态·耗时，body=原始 JSON 全文）；
  请求模型取首个含 request.model 的轮次
- 数值一律转字符串如实显示（str 原值不加工）；None 按 json 语义显示为 null
- 未知字段宽容：按所在层级落入 kv「其他字段」节（值超 200 字截断）
"""

import json
from pathlib import Path

from learn.infra.report.core import make_report

EXP = "search_codegen"

_TRUNC_LIMIT = 200

_TOP_HANDLED = frozenset({
    "schema_version", "experiment_id", "evidence_mode", "created_at", "canonical_source",
    "host", "repository", "credentials_recorded", "acceptance", "independent_asean_reference",
    "runs", "artifact_hashes",
})

_RUN_HANDLED = frozenset({
    "backend", "started", "base_url", "requested_model", "asean", "asean_validation",
    "clarification", "api_turns", "usage",
})

_TURNS_HANDLED = frozenset({"backend", "api_turns"})


def matches(raw):
    if not isinstance(raw, dict):
        return False
    return ("runs" in raw and "acceptance" in raw) or "turns" in raw


def transform(raw, source_path=None):
    if isinstance(raw, dict):
        if "runs" in raw and "acceptance" in raw:
            return _evidence_report(raw, source_path)
        if "turns" in raw:
            return _receipts_report(raw, source_path)
    raise ValueError("search_codegen 转换器不识别该 json 形状（判据见 matches）")


def _dump(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def _kv(value):
    if isinstance(value, str):
        return value
    return _dump(value)


def _trunc(text):
    if len(text) <= _TRUNC_LIMIT:
        return text
    return text[:_TRUNC_LIMIT] + "…"


def _num(value):
    if value is None:
        return ""
    return str(value)


def _check(value):
    if value is True:
        return "✓"
    if value is False:
        return "✗"
    return ""


def _sub_dict(value):
    return value if isinstance(value, dict) else {}


def _unique_code(base, used):
    code = base
    n = 2
    while code in used:
        code = f"{base}-{n}"
        n += 1
    used.add(code)
    return code


def _other_pairs(obj, handled):
    return [[key, _trunc(_kv(value))] for key, value in obj.items() if key not in handled]


def _evidence_report(raw, source_path):
    meta = [
        f"experiment_id: {_kv(raw.get('experiment_id'))}",
        f"evidence_mode: {_kv(raw.get('evidence_mode'))}",
        f"created_at: {_kv(raw.get('created_at'))}",
        f"canonical_source: {_kv(raw.get('canonical_source'))}",
        f"credentials_recorded: {_kv(raw.get('credentials_recorded'))}",
    ]
    host = _sub_dict(raw.get("host"))
    repo = _sub_dict(raw.get("repository"))
    if host:
        meta.append(f"host: {_kv(host.get('platform'))} · Python {_kv(host.get('python'))}")
    if repo:
        meta.append(f"repository: {_kv(repo.get('commit'))} @ {_kv(repo.get('branch'))}")
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    else:
        meta.append("数据源：上游验收正典（chapter1/**/validation），非本仓第二轨")
    runs = [run for run in (raw.get("runs") or []) if isinstance(run, dict)]
    used = set()
    arms = []
    for run in runs:
        code = _unique_code(_kv(run.get("backend")) or "?", used)
        arms.append(_run_arm(run, code))
    arms.append(_overview_arm(raw, _sub_dict(raw.get("acceptance"))))
    return make_report({
        "title": "search_codegen 实验报告（上游验收数据）",
        "meta": meta,
        "summary_columns": [
            {"key": "backend", "title": "后端"},
            {"key": "model", "title": "请求模型"},
            {"key": "started", "title": "启动", "align": "center"},
            {"key": "asean", "title": "ASEAN 验收", "align": "center"},
            {"key": "clarif", "title": "澄清验收", "align": "center"},
            {"key": "turns", "title": "API 轮数", "align": "center"},
            {"key": "tokens", "title": "tokens", "align": "center"},
            {"key": "elapsed", "title": "耗时(s)", "align": "center"},
        ],
        "arms": arms,
        "footnotes": [
            "badge 规则：started 为假或两项验收皆假 → ✗；两项皆真 → ✓；部分通过 → ⚠（映射规则见 learn/infra/report/transforms/search_codegen.py 模块 docstring）",
            "ASEAN 验收 = asean_validation.passed；澄清验收 = clarification.validation.passed；tokens = usage.total_tokens；耗时 = asean.elapsed_seconds",
            "验收总览臂承载顶层 acceptance 与 independent_asean_reference 折叠节",
        ],
    })


def _run_arm(run, code):
    asean = _sub_dict(run.get("asean"))
    asean_val = _sub_dict(run.get("asean_validation"))
    clarif = _sub_dict(run.get("clarification"))
    clarif_val = _sub_dict(clarif.get("validation"))
    usage = _sub_dict(run.get("usage"))
    api_turns = run.get("api_turns") if isinstance(run.get("api_turns"), list) else []
    asean_passed = asean_val.get("passed")
    clarif_passed = clarif_val.get("passed")
    sections = [
        _asean_section(run, asean, asean_val),
        _clarif_section(clarif, clarif_val),
        _turns_list_section(api_turns),
        {"title": "usage", "kind": "kv", "pairs": [[key, _kv(value)] for key, value in usage.items()]},
    ]
    other = _other_pairs(run, _RUN_HANDLED)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    return {
        "name": code,
        "code": code,
        "badge": _run_badge(run.get("started"), asean_passed, clarif_passed),
        "cells": {
            "backend": code,
            "model": _kv(run.get("requested_model")),
            "started": _check(run.get("started")),
            "asean": _check(asean_passed),
            "clarif": _check(clarif_passed),
            "turns": _num(len(api_turns)),
            "tokens": _num(usage.get("total_tokens")),
            "elapsed": _num(asean.get("elapsed_seconds")),
        },
        "sections": sections,
    }


def _run_badge(started, asean_passed, clarif_passed):
    if started is False or (asean_passed is False and clarif_passed is False):
        return {"text": "✗", "kind": "fail"}
    if asean_passed is True and clarif_passed is True:
        return {"text": "✓", "kind": "ok"}
    if asean_passed is True or clarif_passed is True:
        return {"text": "⚠", "kind": "warn"}
    return {"text": "？", "kind": "na"}


def _asean_section(run, asean, asean_val):
    pairs = [
        ["requested_model", _kv(run.get("requested_model"))],
        ["base_url", _kv(run.get("base_url"))],
        ["asean.success", _kv(asean.get("success"))],
        ["asean.provider", _kv(asean.get("provider"))],
        ["asean.model", _kv(asean.get("model"))],
        ["asean.elapsed_seconds", _num(asean.get("elapsed_seconds"))],
    ]
    if asean.get("error") is not None:
        pairs.append(["asean.error", _trunc(_kv(asean.get("error")))])
    tool_calls = asean.get("tool_calls") if isinstance(asean.get("tool_calls"), list) else None
    if tool_calls is not None:
        pairs.append(["asean.tool_calls_count", _num(len(tool_calls))])
    citations = asean.get("citations") if isinstance(asean.get("citations"), list) else None
    if citations is not None:
        pairs.append(["asean.citations_count", _num(len(citations))])
    checks = _sub_dict(asean_val.get("checks"))
    for key in checks:
        pairs.append([f"asean_validation.checks.{key}", _check(checks[key]) or _kv(checks[key])])
    pairs.append(["asean_validation.passed", _kv(asean_val.get("passed"))])
    if asean_val.get("independent_reference") is not None:
        pairs.append(["asean_validation.independent_reference", _kv(asean_val.get("independent_reference"))])
    if asean_val.get("output_types") is not None:
        pairs.append(["asean_validation.output_types", _kv(asean_val.get("output_types"))])
    return {"title": "ASEAN 任务与校验", "kind": "kv", "pairs": pairs}


def _clarif_section(clarif, clarif_val):
    pairs = [["ambiguous_task", _kv(clarif.get("ambiguous_task"))]]
    first = _sub_dict(clarif.get("first"))
    if first:
        pairs.append(["clarification.first.success", _kv(first.get("success"))])
        pairs.append(["clarification.first.elapsed_seconds", _num(first.get("elapsed_seconds"))])
        if first.get("error") is not None:
            pairs.append(["clarification.first.error", _trunc(_kv(first.get("error")))])
    if clarif.get("user_reply") is not None:
        pairs.append(["clarification.user_reply", _kv(clarif.get("user_reply"))])
    if clarif.get("second") is not None:
        pairs.append(["clarification.second", "第二轮回执存在，全文见「API 回执逐轮」"])
    checks = _sub_dict(clarif_val.get("checks"))
    for key in checks:
        pairs.append([f"clarification.validation.checks.{key}", _check(checks[key]) or _kv(checks[key])])
    pairs.append(["clarification.validation.passed", _kv(clarif_val.get("passed"))])
    return {"title": "澄清任务与校验", "kind": "kv", "pairs": pairs}


def _turns_list_section(turns):
    items = []
    for i, turn in enumerate(turns, 1):
        if isinstance(turn, dict):
            summary = f"第{i}轮 · HTTP {_kv(turn.get('http_status'))}"
            if turn.get("elapsed_seconds") is not None:
                summary += f" · {_num(turn.get('elapsed_seconds'))}s"
            items.append({"summary": summary, "body": _dump(turn)})
        else:
            items.append({"summary": f"第{i}轮", "body": _dump(turn)})
    return {"title": "API 回执逐轮", "kind": "list", "items": items}


def _overview_arm(raw, acceptance):
    sections = []
    pairs = []
    for key in ("policy", "acceptance_backend", "eligible_acceptance_backends",
                "eligible_backends_attempted", "openrouter_is_diagnostic_not_acceptance", "passed"):
        if key in acceptance:
            pairs.append([key, _kv(acceptance[key])])
    if acceptance.get("reference_docs") is not None:
        pairs.append(["reference_docs", _kv(acceptance.get("reference_docs"))])
    sections.append({"title": "acceptance", "kind": "kv", "pairs": pairs})
    sections.append(_per_backend_section(_sub_dict(acceptance.get("per_backend"))))
    ref = raw.get("independent_asean_reference")
    if isinstance(ref, dict):
        sections.append({"title": "independent_asean_reference", "kind": "kv",
                         "pairs": [[key, _kv(value)] for key, value in ref.items() if key != "coordinates"]})
        coords = ref.get("coordinates")
        if isinstance(coords, dict):
            sections.append({"title": "independent_asean_reference.coordinates", "kind": "table",
                             "headers": ["城市", "坐标"],
                             "rows": [[city, _kv(value)] for city, value in coords.items()]})
    elif ref is not None:
        sections.append({"title": "independent_asean_reference", "kind": "pre", "text": _kv(ref)})
    else:
        sections.append({"title": "independent_asean_reference", "kind": "note", "text": "无独立参照数据"})
    hashes = raw.get("artifact_hashes")
    if isinstance(hashes, dict) and hashes:
        sections.append({"title": "artifact_hashes", "kind": "kv",
                         "pairs": [[key, _kv(value)] for key, value in hashes.items()]})
    other = _other_pairs(raw, _TOP_HANDLED)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    passed = acceptance.get("passed")
    if passed is True:
        badge = {"text": "✓", "kind": "ok"}
    elif passed is False:
        badge = {"text": "✗", "kind": "fail"}
    else:
        badge = {"text": "？", "kind": "na"}
    return {
        "name": "验收总览",
        "code": "acceptance_overview",
        "badge": badge,
        "cells": {"backend": "总览"},
        "sections": sections,
    }


def _per_backend_section(per_backend):
    if not per_backend:
        return {"title": "acceptance.per_backend", "kind": "note", "text": "无 per_backend 数据"}
    rows = []
    for name, info in per_backend.items():
        if isinstance(info, dict):
            rows.append([
                name,
                _check(info.get("started")) or _kv(info.get("started")),
                _kv(info.get("requested_model")),
                _check(info.get("asean_passed")) or _kv(info.get("asean_passed")),
                _check(info.get("clarification_passed")) or _kv(info.get("clarification_passed")),
            ])
        else:
            rows.append([name, _kv(info), "", "", ""])
    return {"title": "acceptance.per_backend", "kind": "table",
            "headers": ["后端", "启动", "请求模型", "ASEAN 验收", "澄清验收"], "rows": rows}


def _receipts_report(raw, source_path):
    meta = [
        f"schema_version: {_kv(raw.get('schema_version'))}",
        f"experiment_id: {_kv(raw.get('experiment_id'))}",
        f"created_at: {_kv(raw.get('created_at'))}",
    ]
    if raw.get("note") is not None:
        meta.append(f"note: {_kv(raw.get('note'))}")
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    else:
        meta.append("数据源：上游逐轮回执 receipts.json（credential-free 原样转录）")
    groups = [group for group in (raw.get("turns") or []) if isinstance(group, dict)]
    used = set()
    arms = []
    for group in groups:
        api_turns = group.get("api_turns") if isinstance(group.get("api_turns"), list) else []
        code = _unique_code(_kv(group.get("backend")) or "?", used)
        statuses = " / ".join(_kv(t.get("http_status")) for t in api_turns if isinstance(t, dict))
        sections = [
            _turns_list_section(api_turns),
        ]
        other = _other_pairs(group, _TURNS_HANDLED)
        if other:
            sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
        arms.append({
            "name": code,
            "code": code,
            "badge": {"text": "转录", "kind": "na"},
            "cells": {
                "backend": code,
                "model": _request_model(api_turns),
                "turns": _num(len(api_turns)),
                "status": statuses,
            },
            "sections": sections,
        })
    return make_report({
        "title": "search_codegen 回执转录报告（provider 逐轮回执）",
        "meta": meta,
        "summary_columns": [
            {"key": "backend", "title": "后端"},
            {"key": "model", "title": "请求模型"},
            {"key": "turns", "title": "API 轮数", "align": "center"},
            {"key": "status", "title": "HTTP 状态（逐轮）", "align": "center"},
        ],
        "arms": arms,
        "footnotes": [
            "回执为上游 receipts.json 原样转录（credential-free），无验收语义，badge 显示「转录」（na）",
            "各轮 body 为原始 JSON 全文转录",
        ],
    })


def _request_model(api_turns):
    for turn in api_turns:
        if isinstance(turn, dict) and isinstance(turn.get("request"), dict):
            model = turn["request"].get("model")
            if model is not None:
                return _kv(model)
    return ""
