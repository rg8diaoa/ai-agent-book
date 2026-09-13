"""T1（可选）: MiMo 官方托管 web_search 测试。

前置：控制台开通"联网服务插件"；.env 加 MIMO_API_KEY。
判读：答案含今天日期/天气 + 响应可找到引用 → 通过（1-2 内联备选）。
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
if not os.getenv("MIMO_API_KEY"):
    raise SystemExit("未设置 MIMO_API_KEY（根 .env），加好后重跑")

client = OpenAI(
    api_key=os.environ["MIMO_API_KEY"],
    base_url="https://api.xiaomimimo.com/v1",
)
resp = client.chat.completions.create(
    model="mimo-v2.5-pro",
    messages=[{"role": "user", "content": "今天北京的天气怎么样？"}],
    tools=[{"type": "web_search", "max_keyword": 3, "force_search": True, "limit": 1}],
    extra_body={"thinking": {"type": "disabled"}},
)
msg = resp.choices[0].message
print("答案:", (msg.content or "(空)")[:500])
print("完整响应（找引用字段位置）:")
print(json.dumps(resp.model_dump(), ensure_ascii=False, default=str)[:3000])
