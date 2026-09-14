"""T7: Agnes /responses 托管工具探针（决定 1-3 能否走 Agnes 而不用百炼）。
裸请求 + web_search + code_interpreter 三发；看输出项里有没有托管回执。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model_tests" / "infra"))
from probe_utils import head, post_json, require_key, responses_receipt_types

key = require_key("AGNES_API_KEY")
base = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")


def probe(name, payload):
    print(f"\n===== {name} =====")
    try:
        status, body, raw = post_json(f"{base}/responses", key=key, payload=payload, timeout=120)
        print("HTTP", status)
        if body is None:
            print(raw[:500])
            return
        print(head(body, 2200))
        types = responses_receipt_types(body)
        print("输出项类型:", types)
        print("含 web_search_call:", "web_search_call" in types)
        print("含 code_interpreter_call:", "code_interpreter_call" in types)
    except Exception as e:
        print(f"异常: {type(e).__name__}: {str(e)[:250]}")


probe("裸请求（协议形状）", {"model": "agnes-3.0-flash", "input": "回复两个字：成功"})

probe("web_search 托管", {
    "model": "agnes-3.0-flash",
    "input": "请联网搜索：Agnes AI 是哪家公司的产品？",
    "tools": [{"type": "web_search", "search_context_size": "medium"}],
})

probe("code_interpreter 托管", {
    "model": "agnes-3.0-flash",
    "input": "用代码解释器计算 123456789 * 987654321 的结果",
    "tools": [{"type": "code_interpreter", "container": {"type": "auto"}}],
})
