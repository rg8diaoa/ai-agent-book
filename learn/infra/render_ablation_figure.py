#!/usr/bin/env python3
"""Render the context ablation evidence (track-2 json) as a static SVG figure.

Reads a track-2 ablation results json (as written by run.py --evidence for the
context experiment, e.g. learn/ch1/evidence/20260915T0021_context_run2_results.json)
and draws an "expectation vs actual" comparison table:
  - one row per ablation arm (arm list mirrors upstream chapter1/context/main.py
    ContextMode enum: FULL / NO_HISTORY / NO_REASONING / NO_TOOL_CALLS / NO_TOOL_RESULTS)
  - "book expectation" column quotes the textbook concept figure (design intent)
  - "actual" columns come verbatim from the evidence json
  - verdict rule: completed==False -> X; grounding ungrounded -> !; else OK

The figure is a *visualization*, not evidence: it is regenerable from the json
canonical and therefore lives under notes/assets/ (image layer), never evidence/.

Usage:
  .venv/Scripts/python.exe learn/infra/render_ablation_figure.py \
      --input learn/ch1/evidence/20260915T0021_context_run2_results.json \
      --output learn/ch1/notes/assets/20260915_step8_ablation_expect_vs_actual.svg
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BOOK_EXPECTATION = {
    "full": "完整基线：✓ 正常工作",
    "no_history": "无历史记录：⚠ 重复操作",
    "no_reasoning": "无思考过程：⚠ 决策不连贯",
    "no_tool_calls": "—（书图概念臂，代码未设）",
    "no_tool_results": "无工具结果：✗ 盲目循环",
}

ARM_CN = {
    "full": "完整上下文",
    "no_history": "无历史记录",
    "no_reasoning": "无思考过程",
    "no_tool_calls": "无工具调用指令",
    "no_tool_results": "无工具结果",
}

COLS = ["消融臂", "书图预期（设计意图）", "跑完?", "耗时", "轮次", "工具调用", "答案数字有观测支撑?", "实测结论"]


def verdict(rec):
    if not rec.get("completed") or not rec.get("has_final_answer"):
        return "✗", "未完成", "#c0392b"
    if rec.get("grounding_verdict") == "ungrounded":
        return "⚠", "有答案但编数字", "#e67e22"
    return "✓", "正常完成", "#1e8449"


def supported(rec):
    v = rec.get("grounding_verdict")
    if v == "ungrounded":
        n = len(rec.get("unsupported_quantities") or [])
        return f"✗ 编造 {n} 个数"
    if v == "no_answer":
        return "— 无答案"
    return "✓ 未发现编造"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(records, source_name):
    row_h, head_h, pad = 52, 40, 12
    widths = [150, 250, 70, 80, 70, 90, 190, 170]
    w = sum(widths) + pad * 2
    h = head_h + row_h * (len(records) + 1) + 96
    x0 = lambda c: pad + sum(widths[:c])  # noqa: E731
    xc = lambda c: x0(c) + widths[c] // 2  # noqa: E731

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        'font-family="Segoe UI, Microsoft YaHei, sans-serif" font-size="14">',
        f'<rect width="{w}" height="{h}" fill="#ffffff"/>',
        f'<text x="{pad}" y="26" font-size="18" font-weight="bold">context 消融实验：书图预期 vs 本机实测</text>',
        f'<text x="{pad}" y="46" font-size="12" fill="#666">数据源：learn/ch1/evidence/{esc(source_name)}（第二轨正典 json，路由 zhipu/glm-5.3-flash）｜'
        "臂定义：chapter1/context/main.py:253-257</text>",
    ]
    y = 64
    for c, title in enumerate(COLS):
        out.append(f'<rect x="{x0(c)}" y="{y}" width="{widths[c]}" height="{head_h}" fill="#2c3e50"/>')
        out.append(
            f'<text x="{xc(c)}" y="{y + head_h / 2 + 5}" text-anchor="middle" fill="#fff" font-weight="bold">{esc(title)}</text>'
        )
    y += head_h
    for i, rec in enumerate(records):
        mode = rec.get("context_mode", "?")
        mark, label, color = verdict(rec)
        band = "#f8f9fa" if i % 2 == 0 else "#ffffff"
        out.append(f'<rect x="{pad}" y="{y}" width="{sum(widths)}" height="{row_h}" fill="{band}"/>')
        cells = [
            f'<tspan font-weight="bold">{esc(ARM_CN.get(mode, mode))}</tspan><tspan fill="#888"> {esc(mode)}</tspan>',
            esc(BOOK_EXPECTATION.get(mode, "—")),
            "✓" if rec.get("completed") else "✗",
            f'{rec.get("execution_time", 0):.1f}s',
            str(rec.get("iterations", "—")),
            str(rec.get("num_tool_calls", "—")),
            esc(supported(rec)),
            f'<tspan fill="{color}" font-weight="bold">{mark}</tspan> {esc(label)}',
        ]
        for c, html in enumerate(cells):
            anchor = "middle" if c in (2, 4, 5) else "start"
            tx = xc(c) if c in (2, 4, 5) else x0(c) + 8
            out.append(
                f'<text x="{tx}" y="{y + row_h / 2 + 5}" text-anchor="{anchor}"'
                f'{" fill=" + chr(34) + color + chr(34) if c == 7 else ""}>{html}</text>'
            )
        y += row_h
    y += 18
    out.append(
        f'<text x="{pad}" y="{y}" font-size="12" fill="#666">实测结论列：✓ 正常完成｜⚠ 有答案但数字无工具观测支撑（幻觉实锤）｜✗ 未完成。'
        "书图预期列为教科书概念示意，臂设计随版本演进（书图含“无工具定义”臂，上游代码未设）。</text>"
    )
    y += 18
    out.append(
        f'<text x="{pad}" y="{y}" font-size="12" fill="#666">本图为可视化（可由 json 重生成，不入 evidence/）：'
        "由 learn/infra/render_ablation_figure.py 生成。</text>"
    )
    out.append("</svg>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="track-2 ablation results json")
    ap.add_argument("--output", required=True, help="output svg path (notes/assets/)")
    args = ap.parse_args()
    records = json.loads(Path(args.input).read_text(encoding="utf-8"))
    svg = render(records, Path(args.input).name)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    print(f"written: {out} ({len(records)} arms)")


if __name__ == "__main__":
    main()
