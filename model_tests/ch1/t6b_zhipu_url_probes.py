"""T6b: /api/v1 返回 429 的归因探针——区分"URL 错"还是"该端点只对 Coding Plan 开放"。
A: 无工具裸请求（排除工具因素）  B: paas/v4 下猜测的 responses 路径  C: /api/v1 chat 对照。
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
KEY = os.environ["ZHIPU_API_KEY"]


def probe(name, url, payload):
    print(f"\n===== {name} =====\nPOST {url}")
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {KEY}"}, json=payload, timeout=60)
        print("HTTP", r.status_code)
        print(json.dumps(r.json(), ensure_ascii=False)[:600])
    except Exception as e:
        print(f"异常: {type(e).__name__}: {str(e)[:200]}")


probe("A · /api/v1/responses 裸请求（无工具）",
      "https://open.bigmodel.cn/api/v1/responses",
      {"model": "glm-5.3-flash", "input": "回复两个字：成功"})

probe("B · /api/paas/v4/responses（路径备选猜测）",
      "https://open.bigmodel.cn/api/paas/v4/responses",
      {"model": "glm-5.3-flash", "input": "回复两个字：成功"})

probe("C · /api/v1/chat/completions（协议对照）",
      "https://open.bigmodel.cn/api/v1/chat/completions",
      {"model": "glm-5.3-flash", "messages": [{"role": "user", "content": "回复两个字：成功"}]})
