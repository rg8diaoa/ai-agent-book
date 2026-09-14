"""probe_utils — 探测脚本公共设施（learn/infra）。

learn/chN/probes/ 下新探测的样板：
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))   # probes→chN→learn→ROOT
    from learn.infra.probe_utils import require_key, post_json, responses_receipt_types, head

职责：密钥装载与断言 / SDK 响应 json 化 / 截断打印 / HTTP POST 探针 / 回执类型提取。
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    """装载根 .env（显式路径，chN/ 子目录深度下也能找到）。"""
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")


def require_key(name: str) -> str:
    """断言 key 存在并返回；缺失即 SystemExit（探测脚本惯例：缺 key 不开跑）。"""
    load_env()
    value = os.getenv(name, "")
    if not value:
        raise SystemExit(f"未设置 {name}（根 .env）")
    return value


def head(value, limit: int = 300) -> str:
    """截断为可打印短串（str 直接截，其它类型先 json 化）。"""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    return text if len(text) <= limit else text[:limit] + f"...(len={len(text)})"


def dump(resp) -> dict:
    """OpenAI SDK 响应 → json 安全 dict（datetime 等转 str）。"""
    return json.loads(json.dumps(resp.model_dump(), ensure_ascii=False, default=str))


def post_json(url: str, *, key: str = None, payload: dict = None, timeout: int = 120):
    """POST JSON 探针：返回 (status_code, body_dict_or_None, raw_text)。"""
    import requests

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    r = requests.post(url, headers=headers, json=payload or {}, timeout=timeout)
    try:
        return r.status_code, r.json(), r.text
    except ValueError:
        return r.status_code, None, r.text


def responses_receipt_types(body: dict) -> list:
    """/responses 输出项类型清单（T7/T8 判读托管回执用）。"""
    out = body.get("output") or []
    return [it.get("type") for it in out if isinstance(it, dict)]


def show_message(tag: str, resp,
                 fields=("annotations", "web_search", "web_search_result",
                         "search_result", "citations", "tool_calls"),
                 content_limit: int = 150) -> dict:
    """打印 chat 响应的 content 片段 + message 顶层字段 + 指定引用字段，返回 json 安全 dump。"""
    d = dump(resp)
    m = d["choices"][0]["message"]
    print(f"\n===== {tag} =====")
    print("content 片段:", head(m.get("content") or "(空)", content_limit))
    print("message 顶层字段:", sorted(k for k in m.keys() if m.get(k) not in (None, "", [])))
    for k in fields:
        if m.get(k):
            print(f"  ↳ {k}:", head(m[k], 400))
    return d
