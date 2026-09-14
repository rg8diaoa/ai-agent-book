"""T9b: 定位智谱 chat web_search 的引用字段——dump 完整响应结构。"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
zp = OpenAI(api_key=os.environ["ZHIPU_API_KEY"], base_url="https://open.bigmodel.cn/api/paas/v4")
resp = zp.chat.completions.create(
    model="glm-5.3-flash",
    messages=[{"role": "user", "content": "今天北京的天气怎么样？"}],
    tools=[{"type": "web_search",
            "web_search": {"enable": "True", "search_engine": "search_pro",
                           "search_result": "True"}}],
)
dump = json.loads(json.dumps(resp.model_dump(), ensure_ascii=False, default=str))
print("响应顶层字段:", sorted(dump.keys()))
print("choices[0] 字段:", sorted(dump["choices"][0].keys()))
text = json.dumps(dump, ensure_ascii=False)
print("响应总长:", len(text))
print(text[:3500])
