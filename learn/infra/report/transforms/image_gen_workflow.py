"""image_gen_workflow 实验（上游实验 1-4）转换器：runs+requirements 形状 → Report（一律经 core.make_report 校验）。

形状指纹（matches）：dict 含 runs 与 requirements → True（chapter1/image-gen-workflow/validation/
latest.json、real_*/evidence.json；实测顶层键 schema_version/experiment_id/evidence_mode/
created_at/canonical_source/credential_source_env/credential_value_recorded/host/repository/
requirements/runs/notes）。

映射规则（2026-08-21 实读 real_20260821T040450Z 得出）：
- runs 逐 run 一臂（code=f"{requirement_id}@{route}"，重复时加序号后缀；实测 5 需求 × 3 路线
  = 15 run，route ∈ workflow/native/native_gptimage）；汇总表列 需求/路线/provider·model/
  产出图像/图像大小(B)/节点数/耗时(ms)/错误；provider·model 取各 node.call 的 provider·model
  去重拼接，耗时(ms) 为各 node.call.latency_ms 之和（上游无 run 级耗时字段，为派生值，
  节点均无数值时留空）
- badge：image 存在且 error 为空 → ✓ ok，否则 ✗ fail
- 每 run 折叠节：原始输入（pre）、rewrite 字段（kv，实测键 prompt/negative_prompt/style_notes）、
  节点调用明细（list，summary=节点序·名称·provider·model·status·latency，body=原始 JSON 全文，
  含 raw_output）、image 落盘信息（kv，实测键 path/sha256/bytes/mime）、错误（error 非空时 kv）
- 尾臂「说明」（badge —·na）承载 requirements（list 逐条全文）与 notes（长文本合并 pre）
- credential_source_env 仅记录环境变量名（credential_value_recorded=False，无密钥明文）
- 数值一律转字符串如实显示；未知字段宽容落入 kv「其他字段」节（值超 200 字截断）
"""

import json
from pathlib import Path

from learn.infra.report.core import make_report

EXP = "image_gen_workflow"

_TRUNC_LIMIT = 200

_TOP_HANDLED = frozenset({
    "schema_version", "experiment_id", "evidence_mode", "created_at", "canonical_source",
    "credential_source_env", "credential_value_recorded", "host", "repository",
    "requirements", "runs", "notes",
})

_RUN_HANDLED = frozenset({"requirement_id", "route", "input", "rewrite", "nodes", "image", "error"})


def matches(raw):
    return isinstance(raw, dict) and "runs" in raw and "requirements" in raw


def transform(raw, source_path=None):
    if matches(raw):
        return _report(raw, source_path)
    raise ValueError("image_gen_workflow 转换器不识别该 json 形状（判据见 matches）")


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


def _report(raw, source_path):
    meta = [
        f"experiment_id: {_kv(raw.get('experiment_id'))}",
        f"evidence_mode: {_kv(raw.get('evidence_mode'))}",
        f"created_at: {_kv(raw.get('created_at'))}",
        f"canonical_source: {_kv(raw.get('canonical_source'))}",
    ]
    env_names = raw.get("credential_source_env")
    if isinstance(env_names, list):
        meta.append(f"credential_source_env: {'、'.join(_kv(n) for n in env_names)}"
                    f"（credential_value_recorded={_kv(raw.get('credential_value_recorded'))}）")
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
        code = _unique_code(f"{_kv(run.get('requirement_id'))}@{_kv(run.get('route'))}", used)
        arms.append(_run_arm(run, code))
    arms.append(_notes_arm(raw))
    return make_report({
        "title": "image_gen_workflow 实验报告（上游验收数据）",
        "meta": meta,
        "summary_columns": [
            {"key": "requirement", "title": "需求"},
            {"key": "route", "title": "路线"},
            {"key": "provider_model", "title": "provider·model"},
            {"key": "image", "title": "产出图像", "align": "center"},
            {"key": "image_bytes", "title": "图像大小(B)", "align": "center"},
            {"key": "nodes", "title": "节点数", "align": "center"},
            {"key": "latency", "title": "耗时(ms)", "align": "center"},
            {"key": "error", "title": "错误"},
        ],
        "arms": arms,
        "footnotes": [
            "badge 规则：产出 image 且无 error → ✓，否则 ✗（映射规则见 learn/infra/report/transforms/image_gen_workflow.py 模块 docstring）",
            "耗时(ms) 为各节点 call.latency_ms 之和、provider·model 为各节点调用去重拼接（均为派生值，上游无 run 级字段）",
            "credential_source_env 仅记录环境变量名，credential_value_recorded=False 表示未记录密钥值",
        ],
    })


def _run_arm(run, code):
    rewrite = _sub_dict(run.get("rewrite"))
    nodes = run.get("nodes") if isinstance(run.get("nodes"), list) else []
    image = _sub_dict(run.get("image"))
    error = run.get("error")
    ok = bool(image) and not error
    sections = [
        {"title": "原始输入", "kind": "pre", "text": _kv(run.get("input"))},
        {"title": "rewrite（改写后提示词）", "kind": "kv",
         "pairs": [[key, _kv(value)] for key, value in rewrite.items()]},
        _nodes_list_section(nodes),
    ]
    if image:
        sections.append({"title": "image 落盘信息", "kind": "kv",
                         "pairs": [[key, _kv(value)] for key, value in image.items()]})
    else:
        sections.append({"title": "image 落盘信息", "kind": "note", "text": "无 image（未产出图像）"})
    if error is not None:
        sections.append({"title": "错误", "kind": "kv", "pairs": [["error", _kv(error)]]})
    other = _other_pairs(run, _RUN_HANDLED)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    return {
        "name": code,
        "code": code,
        "badge": {"text": "✓", "kind": "ok"} if ok else {"text": "✗", "kind": "fail"},
        "cells": {
            "requirement": _kv(run.get("requirement_id")),
            "route": _kv(run.get("route")),
            "provider_model": _provider_model(nodes),
            "image": "✓" if image else "✗",
            "image_bytes": _num(image.get("bytes")),
            "nodes": _num(len(nodes)),
            "latency": _total_latency(nodes),
            "error": "" if error is None else _kv(error),
        },
        "sections": sections,
    }


def _provider_model(nodes):
    labels = []
    for node in nodes:
        call = _sub_dict(node.get("call")) if isinstance(node, dict) else {}
        label = f"{_kv(call.get('provider'))}·{_kv(call.get('model'))}"
        if label not in labels:
            labels.append(label)
    return " / ".join(labels)


def _total_latency(nodes):
    total = 0.0
    found = False
    for node in nodes:
        call = _sub_dict(node.get("call")) if isinstance(node, dict) else {}
        value = call.get("latency_ms")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += value
            found = True
    return str(total) if found else ""


def _nodes_list_section(nodes):
    items = []
    for i, node in enumerate(nodes, 1):
        if isinstance(node, dict):
            call = _sub_dict(node.get("call"))
            summary = (f"节点{i} · {_kv(node.get('node'))} · {_kv(call.get('provider'))}"
                       f"·{_kv(call.get('model'))} · {_kv(call.get('status'))} · {_num(call.get('latency_ms'))}ms")
            items.append({"summary": summary, "body": _dump(node)})
        else:
            items.append({"summary": f"节点{i}", "body": _dump(node)})
    return {"title": "节点调用明细", "kind": "list", "items": items}


def _notes_arm(raw):
    sections = []
    reqs = raw.get("requirements")
    if isinstance(reqs, list):
        items = []
        for i, req in enumerate(reqs, 1):
            if isinstance(req, dict):
                items.append({
                    "summary": f"{_kv(req.get('id'))}（{_kv(req.get('category'))}）",
                    "body": _dump(req),
                })
            else:
                items.append({"summary": f"需求{i}", "body": _dump(req)})
        sections.append({"title": "requirements（画图需求）", "kind": "list", "items": items})
    notes = raw.get("notes")
    if isinstance(notes, list) and notes:
        sections.append({"title": "notes（实验备注）", "kind": "pre",
                         "text": "\n\n".join(note if isinstance(note, str) else _dump(note) for note in notes)})
    elif notes is not None:
        sections.append({"title": "notes（实验备注）", "kind": "pre", "text": _kv(notes)})
    other = _other_pairs(raw, _TOP_HANDLED)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    return {
        "name": "说明",
        "code": "notes_overview",
        "badge": {"text": "—", "kind": "na"},
        "cells": {"requirement": "—"},
        "sections": sections,
    }
