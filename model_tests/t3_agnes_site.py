"""T3: Agnes 站点归属测试（决定所有 Agnes 配置的 base_url）。

判读：通的那个站填进 .env：AGNES_BASE_URL=<通的那个>。
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
key = os.getenv("AGNES_API_KEY")
if not key:
    raise SystemExit("未设置 AGNES_API_KEY（根 .env），加好后重跑")

for base in ("https://apihub.agnes-ai.com/v1", "https://api.agnes-ai.cn/v1"):
    print(f"\n===== {base} =====")
    try:
        client = OpenAI(api_key=key, base_url=base, timeout=30)
        resp = client.chat.completions.create(
            model="agnes-3.0-flash",
            messages=[{"role": "user", "content": "回复两个字：成功"}],
        )
        print("回复:", resp.choices[0].message.content)
        print("=> 你的 key 归属此站")
    except Exception as e:
        print(f"=> 不通: {type(e).__name__}: {str(e)[:200]}")
