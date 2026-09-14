"""T11: DashScope 按量 key 最小探测（经路由 deep_research）。不跑实验本体。"""
from agentbook.model_router import resolve
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
cfg = resolve("deep_research")
client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"], timeout=120)
resp = client.chat.completions.create(
    model=cfg["model"],
    messages=[{"role": "user", "content": "回复两个字：成功"}],
    max_tokens=512,
)
print("OK model:", resp.model)
print("回复:", (resp.choices[0].message.content or "(空，思考型模型可能只输出思考)")[:100])
print("finish_reason:", resp.choices[0].finish_reason)
