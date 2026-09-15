"""learning_from_experience 实验（上游实验 7-2）转换器：三种输入形状 → Report（一律经 core.make_report 校验）。

形状指纹（matches，三支互斥；实读 chapter1/learning-from-experience/validation/ 得出）：
1. dict 含 artifact 与 acceptance_complete 且不含 q_learning —— 验收指针形状
   （latest.json 实测仅 4 键：experiment_id/artifact/acceptance_complete/finalized_at）
2. dict 含 llm 与 rl —— 实验结果形状（<run>/experiment_results.json，实测顶层仅 {llm, rl}）
3. dict 含 q_learning 或 llm_result_summary —— 验收证据形状（<run>/evidence.json，实测 22 个
   异构顶层键：schema_version/experiment_id/title/campaign_started_at/evidence_finalized_at/
   git_revision/runtime/execution_manifest/backend/provider_response_models/usage/q_learning/
   k3_first_attempt/protocol_gates/acceptance_complete/manuscript_observation_matches/
   result_mismatches/interpretation/artifacts/artifact_sha256/postprocessor_source_sha256/
   llm_result_summary）

映射规则：
- 指针形状 → 引导 Report：单臂 note「该文件为验收指针，真证据在 artifact 字段指向的目录，
  请改用其下 evidence.json / experiment_results.json 渲染」，badge {"text": "—", "kind": "na"}
- 结果形状 → rl/llm 各一臂；badge 判据 rl 臂取 eval_victory_rate、llm 臂取 training_victory_rate
  （llm 无评估轮）：1.0 → ✓ ok、0 → ✗ fail、其余数值 → ⚠ warn、缺失 → ？ na；
  learning_curve 全量 table（实测 10 行 {episode, victory_rate, q_table_size, epsilon}）；
  episode_rewards/episode_lengths/training_trajectories 大数组按 v1 约定只给计数与首条样例，
  轨迹另给逐步计数与首步全文样例
- 证据形状 → 单臂 kv 汇总 + 分节：q_learning（kv + learning_curve table）、
  llm_result_summary 与 k3_first_attempt（kv + 动作序列 list 全文）、usage（kv）、
  protocol_gates（table 逐门 ✓/✗）、manuscript_observation_matches（kv）+ result_mismatches
  （list）、interpretation（pre 全文）、执行与出处（kv）；badge 取 acceptance_complete
- llm_experiences.json（experiences/api_records 形状）不在指纹内，v1 不路由（如实说明）
- 数值一律转字符串如实显示；未知字段宽容落入 kv「其他字段」节（值超 200 字截断）
"""

import json
from pathlib import Path

from learn.infra.report.core import make_report

EXP = "learning_from_experience"

_TRUNC_LIMIT = 200

_POINTER_HANDLED = frozenset({"experiment_id", "artifact", "acceptance_complete", "finalized_at"})

_EVIDENCE_HANDLED = frozenset({
    "schema_version", "experiment_id", "title", "campaign_started_at", "evidence_finalized_at",
    "git_revision", "runtime", "execution_manifest", "backend", "provider_response_models",
    "usage", "q_learning", "k3_first_attempt", "protocol_gates", "acceptance_complete",
    "manuscript_observation_matches", "result_mismatches", "interpretation", "artifacts",
    "artifact_sha256", "postprocessor_source_sha256", "llm_result_summary",
})

_RL_ARRAY_KEYS = frozenset({"learning_curve", "episode_rewards", "episode_lengths"})
_LLM_ARRAY_KEYS = frozenset({"episode_rewards", "episode_lengths", "training_trajectories"})


def matches(raw):
    if not isinstance(raw, dict):
        return False
    if "artifact" in raw and "acceptance_complete" in raw and "q_learning" not in raw:
        return True
    if "llm" in raw and "rl" in raw:
        return True
    return "q_learning" in raw or "llm_result_summary" in raw


def transform(raw, source_path=None):
    if isinstance(raw, dict):
        if "artifact" in raw and "acceptance_complete" in raw and "q_learning" not in raw:
            return _pointer_report(raw, source_path)
        if "llm" in raw and "rl" in raw:
            return _results_report(raw, source_path)
        if "q_learning" in raw or "llm_result_summary" in raw:
            return _evidence_report(raw, source_path)
    raise ValueError("learning_from_experience 转换器不识别该 json 形状（判据见 matches）")


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


def _scalar_keys(obj):
    return {key for key, value in obj.items() if not isinstance(value, (list, dict))}


def _scalar_pairs(obj):
    return [[key, _kv(value)] for key, value in obj.items() if not isinstance(value, (list, dict))]


def _scalar_pairs_prefixed(obj, prefix):
    return [[prefix + key, _kv(value)]
            for key, value in obj.items() if not isinstance(value, (list, dict))]


def _other_pairs(obj, handled):
    return [[key, _trunc(_kv(value))] for key, value in obj.items() if key not in handled]


def _array_overview(obj, keys):
    pairs = []
    for key in keys:
        if key not in obj:
            continue
        value = obj[key]
        if isinstance(value, list):
            head = f"{len(value)} 个值，首条 {_dump(value[0])}" if value else "空数组"
            pairs.append([key, head])
        else:
            pairs.append([key, _kv(value)])
    return pairs


def _curve_table(curve, title):
    first = curve[0] if isinstance(curve[0], dict) else None
    headers = list(first.keys()) if first is not None else ["值"]
    rows = []
    for item in curve:
        if isinstance(item, dict):
            rows.append([_kv(item.get(h)) for h in headers])
        else:
            rows.append([_kv(item)])
    return {"title": title, "kind": "table", "headers": headers, "rows": rows}


def _rate_badge(rate):
    if isinstance(rate, (int, float)) and not isinstance(rate, bool):
        if rate >= 1.0:
            return {"text": "✓", "kind": "ok"}
        if rate <= 0.0:
            return {"text": "✗", "kind": "fail"}
        return {"text": "⚠", "kind": "warn"}
    return {"text": "？", "kind": "na"}


def _pointer_report(raw, source_path):
    meta = [
        f"experiment_id: {_kv(raw.get('experiment_id'))}",
        f"artifact: {_kv(raw.get('artifact'))}",
        f"acceptance_complete: {_kv(raw.get('acceptance_complete'))}",
        f"finalized_at: {_kv(raw.get('finalized_at'))}",
    ]
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    sections = [{
        "title": "如何渲染真证据",
        "kind": "note",
        "text": (f"该文件为验收指针，真证据在 artifact 字段指向的目录，请改用其下 "
                 f"evidence.json / experiment_results.json 渲染（artifact = {_kv(raw.get('artifact'))}）"),
    }]
    other = _other_pairs(raw, _POINTER_HANDLED)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    return make_report({
        "title": "learning_from_experience 验收指针报告",
        "meta": meta,
        "summary_columns": [{"key": "status", "title": "状态"}],
        "arms": [{
            "name": "验收指针",
            "code": "pointer",
            "badge": {"text": "—", "kind": "na"},
            "cells": {"status": "仅指针，无实验数据"},
            "sections": sections,
        }],
        "footnotes": ["指针文件不含实验数据；acceptance_complete 仅表示验收流程完结"],
    })


def _results_report(raw, source_path):
    rl = _sub_dict(raw.get("rl"))
    llm = _sub_dict(raw.get("llm"))
    meta = []
    if llm:
        meta.append(f"llm: {_kv(llm.get('provider'))}·{_kv(llm.get('model'))}")
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    else:
        meta.append("数据源：上游实验产物 experiment_results.json")
    return make_report({
        "title": "learning_from_experience 实验报告（实验结果 experiment_results.json）",
        "meta": meta,
        "summary_columns": [
            {"key": "method", "title": "方法"},
            {"key": "episodes", "title": "回合数", "align": "center"},
            {"key": "train_rate", "title": "训练胜率", "align": "center"},
            {"key": "eval_rate", "title": "评估胜率", "align": "center"},
            {"key": "avg_steps", "title": "平均步数", "align": "center"},
            {"key": "avg_reward", "title": "平均奖励", "align": "center"},
            {"key": "tokens", "title": "tokens", "align": "center"},
            {"key": "time", "title": "耗时(s)", "align": "center"},
        ],
        "arms": [_rl_arm(rl), _llm_arm(llm)],
        "footnotes": [
            "badge 判据：rl 臂取 eval_victory_rate、llm 臂取 training_victory_rate（llm 无评估轮）；1.0 → ✓、0 → ✗、其余数值 → ⚠（映射规则见 learn/infra/report/transforms/learning_from_experience.py 模块 docstring）",
            "episode_rewards/episode_lengths/training_trajectories 大数组按 v1 约定只给计数与首条样例",
        ],
    })


def _rl_arm(rl):
    sections = [{"title": "rl 字段汇总", "kind": "kv", "pairs": _scalar_pairs(rl)}]
    curve = rl.get("learning_curve")
    if isinstance(curve, list) and curve:
        sections.append(_curve_table(curve, "learning_curve（训练曲线）"))
    sections.append({"title": "episode 数组概览", "kind": "kv",
                     "pairs": _array_overview(rl, ("episode_rewards", "episode_lengths"))})
    other = _other_pairs(rl, _scalar_keys(rl) | _RL_ARRAY_KEYS)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    return {
        "name": _kv(rl.get("method")) or "rl",
        "code": "rl",
        "badge": _rate_badge(rl.get("eval_victory_rate")),
        "cells": {
            "method": _kv(rl.get("method")),
            "episodes": _num(rl.get("training_episodes")),
            "train_rate": _num(rl.get("training_victory_rate")),
            "eval_rate": _num(rl.get("eval_victory_rate")),
            "avg_steps": _num(rl.get("eval_avg_steps")),
            "avg_reward": _num(rl.get("eval_avg_reward")),
            "tokens": "",
            "time": _num(rl.get("training_time")),
        },
        "sections": sections,
    }


def _llm_arm(llm):
    sections = [{"title": "llm 字段汇总", "kind": "kv", "pairs": _scalar_pairs(llm)}]
    sections.append({"title": "episode 数组概览", "kind": "kv",
                     "pairs": _array_overview(llm, ("episode_rewards", "episode_lengths"))})
    trajectories = llm.get("training_trajectories")
    if isinstance(trajectories, list) and trajectories:
        sections.extend(_trajectory_sections(trajectories))
    other = _other_pairs(llm, _scalar_keys(llm) | _LLM_ARRAY_KEYS)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    return {
        "name": _kv(llm.get("method")) or "llm",
        "code": "llm",
        "badge": _rate_badge(llm.get("training_victory_rate")),
        "cells": {
            "method": _kv(llm.get("method")),
            "episodes": _num(llm.get("training_episodes")),
            "train_rate": _num(llm.get("training_victory_rate")),
            "eval_rate": _num(llm.get("eval_victory_rate")),
            "avg_steps": _num(llm.get("eval_avg_steps")),
            "avg_reward": _num(llm.get("eval_avg_reward")),
            "tokens": _num(llm.get("total_tokens")),
            "time": _num(llm.get("training_time")),
        },
        "sections": sections,
    }


def _trajectory_sections(trajectories):
    out = []
    for i, traj in enumerate(trajectories, 1):
        if not isinstance(traj, dict):
            out.append({"title": f"轨迹{i}", "kind": "pre", "text": _dump(traj)})
            continue
        steps = traj.get("trajectory") if isinstance(traj.get("trajectory"), list) else None
        pairs = [[key, _kv(value)] for key, value in traj.items() if key != "trajectory"]
        if steps is not None:
            pairs.append(["trajectory 步数", _num(len(steps))])
        out.append({"title": f"训练轨迹{i}（phase={_kv(traj.get('phase'))}）", "kind": "kv", "pairs": pairs})
        if steps:
            out.append({"title": f"轨迹{i} 首步样例", "kind": "pre", "text": _dump(steps[0])})
    return out


def _evidence_report(raw, source_path):
    backend = _sub_dict(raw.get("backend"))
    q = _sub_dict(raw.get("q_learning"))
    llm_summary = _sub_dict(raw.get("llm_result_summary"))
    k3 = _sub_dict(raw.get("k3_first_attempt"))
    gates = _sub_dict(raw.get("protocol_gates"))
    observed = _sub_dict(raw.get("manuscript_observation_matches"))
    mismatches = raw.get("result_mismatches")
    acceptance = raw.get("acceptance_complete")
    meta = [
        f"experiment_id: {_kv(raw.get('experiment_id'))}",
        f"git_revision: {_kv(raw.get('git_revision'))}",
        f"campaign_started_at: {_kv(raw.get('campaign_started_at'))}",
        f"evidence_finalized_at: {_kv(raw.get('evidence_finalized_at'))}",
        f"backend: {_kv(backend.get('provider'))}·{_kv(backend.get('model'))}",
        f"acceptance_complete: {_kv(acceptance)}",
    ]
    if source_path:
        meta.append(f"数据源：{Path(source_path).name}")
    else:
        meta.append("数据源：上游验收证据 evidence.json")
    sections = []
    q_pairs = _scalar_pairs(q)
    if q_pairs:
        sections.append({"title": "q_learning（Q-Learning 基线）", "kind": "kv", "pairs": q_pairs})
    curve = q.get("learning_curve")
    if isinstance(curve, list) and curve:
        sections.append(_curve_table(curve, "q_learning.learning_curve（训练曲线）"))
    llm_pairs = _scalar_pairs(llm_summary) + _scalar_pairs_prefixed(k3, "k3_first_attempt.")
    if llm_pairs:
        sections.append({"title": "llm_result_summary 与首次尝试（k3_first_attempt）", "kind": "kv",
                         "pairs": llm_pairs})
    actions = k3.get("actions")
    if isinstance(actions, list) and actions:
        sections.append({"title": f"首次尝试动作序列（{len(actions)} 步）", "kind": "list",
                         "items": [a if isinstance(a, str) else _dump(a) for a in actions]})
    usage = _sub_dict(raw.get("usage"))
    if usage:
        sections.append({"title": "usage", "kind": "kv",
                         "pairs": [[key, _kv(value)] for key, value in usage.items()]})
    if gates:
        sections.append({"title": "protocol_gates（协议门）", "kind": "table",
                         "headers": ["协议门", "结果"],
                         "rows": [[key, _check(value) or _kv(value)] for key, value in gates.items()]})
    obs_pairs = [[key, _check(value) or _kv(value)] for key, value in observed.items()]
    if obs_pairs:
        sections.append({"title": "与书稿观察的对照（manuscript_observation_matches）",
                         "kind": "kv", "pairs": obs_pairs})
    if isinstance(mismatches, list) and mismatches:
        sections.append({"title": "结果差异（result_mismatches）", "kind": "list",
                         "items": [m if isinstance(m, str) else _dump(m) for m in mismatches]})
    interp = raw.get("interpretation")
    if interp is not None:
        sections.append({"title": "interpretation（解读）", "kind": "pre", "text": _kv(interp)})
    provenance = [[key, _kv(raw.get(key))] for key in (
        "schema_version", "title", "runtime", "execution_manifest", "provider_response_models",
        "artifacts", "artifact_sha256", "postprocessor_source_sha256") if key in raw]
    if provenance:
        sections.append({"title": "执行与出处", "kind": "kv", "pairs": provenance})
    other = _other_pairs(raw, _EVIDENCE_HANDLED)
    if other:
        sections.append({"title": "其他字段", "kind": "kv", "pairs": other})
    if acceptance is True:
        badge = {"text": "✓", "kind": "ok"}
    elif acceptance is False:
        badge = {"text": "✗", "kind": "fail"}
    else:
        badge = {"text": "？", "kind": "na"}
    return make_report({
        "title": "learning_from_experience 实验报告（验收证据 evidence.json）",
        "meta": meta,
        "task": raw.get("title") if isinstance(raw.get("title"), str) else None,
        "summary_columns": [
            {"key": "subject", "title": "对象"},
            {"key": "acceptance", "title": "验收", "align": "center"},
            {"key": "provider_model", "title": "provider·model"},
        ],
        "arms": [{
            "name": "验收证据",
            "code": "evidence",
            "badge": badge,
            "cells": {
                "subject": "Q-Learning（RL 基线）对比 LLM 首次尝试",
                "acceptance": _check(acceptance),
                "provider_model": f"{_kv(backend.get('provider'))}·{_kv(backend.get('model'))}",
            },
            "sections": sections,
        }],
        "footnotes": [
            "badge 取 acceptance_complete；protocol_gates 与 manuscript_observation_matches 逐项 ✓/✗ 原样转录",
            "q_learning/llm_result_summary/k3_first_attempt/usage 为上游原值 kv 转录，数值不加工",
            "llm_experiences.json（experiences/api_records 形状）不在本转换器指纹内，v1 不路由",
        ],
    })
