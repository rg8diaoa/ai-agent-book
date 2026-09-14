"""T8: MiMo /responses 托管工具探针（官方日志称 2026-06-23 兼容 Responses API）。
四发一次跑完：裸请求看协议形状；web_search / web_search_preview 两种命名各一发；
code_interpreter 一发。判读同 T7：看输出项里有没有 web_search_call / code_interpreter_call 回执。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model_tests" / "infra"))
from probe_utils import head, post_json, require_key, responses_receipt_types

key = require_key("MIMO_API_KEY")
base = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")


def probe(name, payload):
    print(f"\n===== {name} =====")
    try:
        status, body, raw = post_json(f"{base}/responses", key=key, payload=payload, timeout=120)
        print("HTTP", status)
        if body is None:
            print(raw[:600])
            return
        if status != 200:
            print(head(body, 600))
            return
        out = body.get("output") or []
        types = responses_receipt_types(body)
        print("输出项类型:", types)
        print("含 web_search_call:", "web_search_call" in types)
        print("含 code_interpreter_call:", "code_interpreter_call" in types)
        for it in out:
            if isinstance(it, dict) and it.get("type") not in ("reasoning", "message"):
                print("非 message 项样例:", head(it, 800))
        msg = [it for it in out if isinstance(it, dict) and it.get("type") == "message"]
        if msg:
            text = "".join(c.get("text", "") for c in msg[0].get("content", []))
            print("答案片段:", text[:300])
    except Exception as e:
        print(f"异常: {type(e).__name__}: {str(e)[:250]}")


probe("裸请求（协议形状）", {"model": "mimo-v2.5-pro", "input": "回复两个字：成功"})

probe("web_search 托管", {
    "model": "mimo-v2.5-pro",
    "input": "今天北京的天气怎么样？请用搜索工具查证后回答。",
    "tools": [{"type": "web_search"}],
})

probe("web_search_preview 托管", {
    "model": "mimo-v2.5-pro",
    "input": "今天北京的天气怎么样？请用搜索工具查证后回答。",
    "tools": [{"type": "web_search_preview"}],
})

probe("code_interpreter 托管", {
    "model": "mimo-v2.5-pro",
    "input": "用代码解释器计算 123456789 * 987654321 的结果",
    "tools": [{"type": "code_interpreter"}],
})
