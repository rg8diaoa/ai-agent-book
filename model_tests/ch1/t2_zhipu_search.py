"""T2: 智谱 chat web_search 内联测试（glm-5.3 与 glm-5.3-flash 各测一次）。

判读：flash 行通过 → 1-2 快路径（方案 A）可用 flash；flash 报错 → 1-2 走方案 C（与 T2 无关）。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model_tests" / "infra"))
from openai import OpenAI

from probe_utils import head, require_key, show_message

client = OpenAI(api_key=require_key("ZHIPU_API_KEY"),
                base_url="https://open.bigmodel.cn/api/paas/v4")
TOOLS = [{"type": "web_search",
          "web_search": {"enable": "True", "search_engine": "search_pro",
                         "search_result": "True"}}]

for model in ("glm-5.3", "glm-5.3-flash"):
    print(f"\n===== {model} =====")
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "今天北京的天气怎么样？"}],
            tools=TOOLS,
        )
        d = show_message(model, resp, content_limit=500)
        cites = d["choices"][0]["message"].get("annotations") or []
        if cites:
            print("引用样例:", head(cites[0]))
        print("=> 支持内置搜索")
    except Exception as e:
        print(f"=> 不支持: {type(e).__name__}: {str(e)[:300]}")
