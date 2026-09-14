"""T5: 智谱独立搜索 API（web_search_api 路由的执行器验证，方案 C 依赖）。"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()
r = requests.post(
    "https://open.bigmodel.cn/api/paas/v4/web_search",
    headers={"Authorization": f"Bearer {os.environ['ZHIPU_API_KEY']}"},
    json={"search_query": "DeepSeek V4 发布",
          "search_engine": "search_pro_quark", "count": 3},
    timeout=30,
)
print("HTTP", r.status_code)
body = r.json()
print(json.dumps(body, ensure_ascii=False)[:1200])
items = body.get("search_result") or []
print("search_result 条数:", len(items))
