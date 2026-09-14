"""T7b: Agnes /responses 托管工具复测——用正确的工具名 web_search_preview，并强制调用。"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.environ.get("AGNES_API_KEY")
if not key:
    raise SystemExit("未设置 AGNES_API_KEY")
base = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1")
HEADERS = {"Authorization": f"Bearer {key}"}


def probe(name, payload):
    print(f"\n===== {name} =====")
    try:
        r = requests.post(f"{base}/responses", headers=HEADERS, json=payload, timeout=180)
        print("HTTP", r.status_code)
        try:
            body = r.json()
        except Exception:
            print(r.text[:500])
            return
        out = body.get("output") or []
        types = [it.get("type") for it in out if isinstance(it, dict)]
        print("输出项类型:", types)
        print("含 web_search_call:", "web_search_call" in types)
        print("含 code_interpreter_call:", "code_interpreter_call" in types)
        for it in out:
            if isinstance(it, dict) and it.get("type") not in ("reasoning", "message"):
                print("非 message 项样例:", json.dumps(it, ensure_ascii=False)[:800])
        msg = [it for it in out if isinstance(it, dict) and it.get("type") == "message"]
        if msg:
            text = "".join(c.get("text", "") for c in msg[0].get("content", []))
            print("答案片段:", text[:300])
    except Exception as e:
        print(f"异常: {type(e).__name__}: {str(e)[:250]}")


probe("web_search_preview 托管", {
    "model": "agnes-3.0-flash",
    "input": "今天北京的天气怎么样？请用搜索工具查证后回答。",
    "tools": [{"type": "web_search_preview"}],
})

probe("code_interpreter 强制（tool_choice=required + 指令要求必须执行）", {
    "model": "agnes-3.0-flash",
    "input": "必须使用 code_interpreter 工具执行代码来计算 2 的 64 次方，禁止心算，把代码和执行结果都给我。",
    "tools": [{"type": "code_interpreter", "container": {"type": "auto"}}],
    "tool_choice": "required",
})
