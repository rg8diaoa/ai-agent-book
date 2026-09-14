"""1-2 路由版主入口：--mode builtin（内联快路径）或 react（ReAct 轨迹）。

builtin: 单次调用，消费 inline_search 路由（服务端内联搜索，引用在顶层 web_search 字段）
react:   多轮编排，脑=text_only 路由、执行器=web_search_api 路由（客户端 ReAct，轨迹可见）
原 main.py / agent.py（kimi + Moonshot Formula）为验收锚定，一字未动。
"""
import argparse
import json
import time

import requests
from dotenv import load_dotenv
from openai import OpenAI

from agentbook.model_router import resolve

load_dotenv()

SYSTEM = (
    "你是联网搜索助手。先思考需要什么信息，再调用 web_search 工具，"
    "可多轮搜索；信息足够后综合给出带来源编号的答案。"
)
TOOLS = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "联网搜索，返回网页标题、摘要与链接列表",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "搜索关键词"}},
            "required": ["query"],
        },
    },
}]


def run_builtin(question: str, timeout: float) -> dict:
    """内联快路径：模型与搜索工具全部来自 inline_search 路由。"""
    cfg = resolve("inline_search")
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"], timeout=timeout)
    started = time.time()
    resp = client.chat.completions.create(
        model=cfg["model"],
        messages=[{"role": "user", "content": question}],
        tools=cfg["tools"],
    )
    dump = json.loads(json.dumps(resp.model_dump(), ensure_ascii=False, default=str))
    return {
        "mode": "builtin",
        "route": "inline_search",
        "provider": cfg["provider"],
        "model": cfg["model"],
        "question": question,
        "answer": resp.choices[0].message.content or "",
        "citations": dump.get("web_search") or [],
        "latency_s": round(time.time() - started, 1),
    }


def do_search(query: str, timeout: float) -> str:
    """执行器：web_search_api 路由（智谱独立搜索端点，T5 实测）。"""
    search = resolve("web_search_api")
    r = requests.post(
        f"{search['base_url']}/web_search",
        headers={"Authorization": f"Bearer {search['api_key']}"},
        json={"search_query": query, "search_engine": "search_pro_quark", "count": 5},
        timeout=timeout,
    )
    r.raise_for_status()
    items = r.json().get("search_result", [])
    if not items:
        return "(无结果)"
    return "\n".join(
        f"{i + 1}. {it.get('title', '')} | {it.get('link', '')}\n   {it.get('content', '')[:200]}"
        for i, it in enumerate(items)
    )


def run_react(question: str, max_rounds: int, timeout: float) -> dict:
    """轨迹版：脑=text_only 路由、执行器=web_search_api 路由（客户端 ReAct）。"""
    brain = resolve("text_only")
    client = OpenAI(api_key=brain["api_key"], base_url=brain["base_url"], timeout=timeout)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    trace = []
    started = time.time()
    for rnd in range(1, max_rounds + 1):
        resp = client.chat.completions.create(model=brain["model"], messages=messages, tools=TOOLS)
        choice = resp.choices[0]
        reasoning = getattr(choice.message, "reasoning_content", None)
        if reasoning:
            print(f"💭 [{rnd}] {str(reasoning)[:300]}")
        if choice.finish_reason != "tool_calls":
            return {
                "mode": "react",
                "route": "text_only + web_search_api",
                "provider": brain["provider"],
                "model": brain["model"],
                "question": question,
                "rounds": trace,
                "answer": choice.message.content or "",
                "latency_s": round(time.time() - started, 1),
            }
        messages.append({
            "role": "assistant",
            "content": choice.message.content or "",
            "tool_calls": [
                {"id": tc.id, "type": "function",
                 "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in choice.message.tool_calls
            ],
        })
        round_entry = {"round": rnd, "reasoning_head": str(reasoning or "")[:200], "tool_calls": []}
        for tc in choice.message.tool_calls:
            call_args = json.loads(tc.function.arguments or "{}")
            query = call_args.get("query", "")
            print(f"🔧 [{rnd}] web_search(query={query})")
            result = do_search(query, timeout)
            print(f"👀 [{rnd}] {result[:200]}...")
            round_entry["tool_calls"].append({"query": query, "result_head": result[:300]})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
        trace.append(round_entry)
    return {
        "mode": "react",
        "route": "text_only + web_search_api",
        "provider": brain["provider"],
        "model": brain["model"],
        "question": question,
        "rounds": trace,
        "answer": "(达到最大轮数，未得到最终答案)",
        "latency_s": round(time.time() - started, 1),
    }


def main():
    p = argparse.ArgumentParser(description="1-2 路由版（builtin=内联快路径 / react=ReAct 轨迹）")
    p.add_argument("question")
    p.add_argument("--mode", choices=["builtin", "react"], default="builtin")
    p.add_argument("--max-rounds", type=int, default=5)
    p.add_argument("--timeout", type=float, default=180.0)
    a = p.parse_args()
    if a.mode == "builtin":
        r = run_builtin(a.question, a.timeout)
    else:
        r = run_react(a.question, a.max_rounds, a.timeout)
    print(f"\n✅ 答案:\n{r['answer']}")
    if r["mode"] == "builtin":
        print(f"\n👀 来源（顶层 web_search，共 {len(r['citations'])} 条）:")
        print(json.dumps(r["citations"], ensure_ascii=False, indent=2)[:1500])


if __name__ == "__main__":
    main()
