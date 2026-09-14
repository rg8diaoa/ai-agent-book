"""T4: Agnes 文生图测试（决定 1-4 生图方案）。

判读：HTTP 200 且返回含 data[0].url 或 b64_json → 通过，1-4 走 R3 方案 A；
429 → 免费层 1K 有效 20 RPM，稍等重试。
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv("AGNES_API_KEY")
if not key:
    raise SystemExit("未设置 AGNES_API_KEY（根 .env），加好后重跑")

bases = [os.environ["AGNES_BASE_URL"]] if os.getenv("AGNES_BASE_URL") else [
    "https://apihub.agnes-ai.com/v1", "https://api.agnes-ai.cn/v1",
]

for base in bases:
    print(f"\n===== {base} =====")
    try:
        r = requests.post(
            f"{base}/images/generations",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": "agnes-image-2.0-flash",
                  "prompt": "a red apple on a white wooden table, soft daylight",
                  "size": "1024x1024"},
            timeout=180,
        )
        print("HTTP", r.status_code)
        body = r.json()
        text = json.dumps(body, ensure_ascii=False)
        print(text[:1200])
        item = (body.get("data") or [{}])[0]
        if item.get("url") or item.get("b64_json"):
            print("=> 生图成功，字段:", "url" if item.get("url") else "b64_json")
            break
    except Exception as e:
        print(f"异常: {type(e).__name__}: {str(e)[:200]}")
