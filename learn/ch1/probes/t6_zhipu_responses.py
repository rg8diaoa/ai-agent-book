"""T6: 智谱 /api/v1/responses 托管工具探针（web_search + code_interpreter 各一发）。

判读：200 且输出项含 web_search_call / code_interpreter_call 回执 → 智谱会代跑托管工具，
1-3 可全程 glm-5.3-flash + 智谱（百炼不用注册）；否则 1-3 完整验收需百炼或接受无回执学习版。
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
if not os.getenv("ZHIPU_API_KEY"):
    raise SystemExit("未设置 ZHIPU_API_KEY（根 .env）")

BASE = "https://open.bigmodel.cn/api/v1/responses"
HEADERS = {"Authorization": f"Bearer {os.environ['ZHIPU_API_KEY']}"}


def probe(name, payload):
    print(f"\n===== {name} =====")
    try:
        r = requests.post(BASE, headers=HEADERS, json=payload, timeout=180)
        print("HTTP", r.status_code)
        body = r.json()
        print(json.dumps(body, ensure_ascii=False, indent=2)[:2500])
        types = [it.get("type") for it in body.get("output", []) if isinstance(it, dict)]
        print("输出项类型:", types)
        print("含 web_search_call:", "web_search_call" in types)
        print("含 code_interpreter_call:", "code_interpreter_call" in types)
    except Exception as e:
        print(f"异常: {type(e).__name__}: {str(e)[:300]}")


probe("web_search 托管探针", {
    "model": "glm-5.3-flash",
    "input": "请联网搜索：智谱 GLM-5.3-Flash 的发布日期是什么时候？",
    "tools": [{"type": "web_search", "search_context_size": "medium"}],
    "reasoning": {"effort": "low"},
})

probe("code_interpreter 托管探针", {
    "model": "glm-5.3-flash",
    "input": "用代码解释器计算 2 的 20 次方减 123456，并给出结果",
    "tools": [{"type": "code_interpreter", "container": {"type": "auto"}}],
    "reasoning": {"effort": "low"},
})
