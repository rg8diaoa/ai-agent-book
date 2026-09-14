"""T9: chat 内联托管工具普查。
1) zhipu（glm-5.3-flash）：定位 web_search 的引用字段 + 探测 chat 有无 code_interpreter
2) agnes（agnes-3.0-flash）：chat 路径是否有内联 web_search / code_interpreter
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "model_tests" / "infra"))
from openai import OpenAI

from probe_utils import require_key, show_message

# ---- zhipu ----
zp = OpenAI(api_key=require_key("ZHIPU_API_KEY"),
            base_url="https://open.bigmodel.cn/api/paas/v4")
try:
    show_message("zhipu flash · chat web_search", zp.chat.completions.create(
        model="glm-5.3-flash",
        messages=[{"role": "user", "content": "今天北京的天气怎么样？"}],
        tools=[{"type": "web_search",
                "web_search": {"enable": "True", "search_engine": "search_pro",
                               "search_result": "True"}}],
    ))
except Exception as e:
    print("zhipu web_search 异常:", type(e).__name__, str(e)[:250])

try:
    show_message("zhipu flash · chat code_interpreter", zp.chat.completions.create(
        model="glm-5.3-flash",
        messages=[{"role": "user", "content": "用代码计算 123456789 * 987654321 的结果"}],
        tools=[{"type": "code_interpreter"}],
    ))
except Exception as e:
    print("zhipu code_interpreter 异常:", type(e).__name__, str(e)[:250])

# ---- agnes ----
ag = OpenAI(api_key=require_key("AGNES_API_KEY"),
            base_url=os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1"))
for t in ("web_search", "web_search_preview"):
    try:
        show_message(f"agnes chat · {t}", ag.chat.completions.create(
            model="agnes-3.0-flash",
            messages=[{"role": "user", "content": "今天北京的天气怎么样？"}],
            tools=[{"type": t}],
        ))
    except Exception as e:
        print(f"agnes {t} 异常:", type(e).__name__, str(e)[:250])

try:
    show_message("agnes chat · code_interpreter", ag.chat.completions.create(
        model="agnes-3.0-flash",
        messages=[{"role": "user", "content": "用代码计算 123456789 * 987654321 的结果"}],
        tools=[{"type": "code_interpreter"}],
    ))
except Exception as e:
    print("agnes code_interpreter 异常:", type(e).__name__, str(e)[:250])
