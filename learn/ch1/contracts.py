"""上游实验契约表（ch1）：路由解析结果 → 上游实验读取的环境变量槽位。

要点：
- 变量名是上游代码定义的"契约槽位"，与实际厂商无关（如 KIMI_API_KEY 语义 =
  上游"改写节点"的 key 槽位）；真实 provider/model 由证据 json 记录。
- 上游共享注册表 agentbook/providers/registry.py 的 key_vars / base_url_var
  均支持 env 覆盖（providers/models.py:72）。
- apply_env(exp) 先装载根 .env，把契约写入 os.environ 并返回该 dict
  （进程内 import 与 subprocess 两种用法统一，调用方无需自备 load_dotenv）。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # ROOT

from learn.router import resolve


def env_image_gen_workflow() -> dict:
    """1-4 image-gen-workflow：上游 config.py 直读 KIMI_*/DASHSCOPE_*/OPENAI_*。"""
    t = resolve("text_only")
    w = resolve("image_workflow")
    n = resolve("image_native")
    return {
        # 改写节点槽位（上游读 KIMI_*）
        "KIMI_API_KEY": t["api_key"],
        "KIMI_BASE_URL": t["base_url"],
        "REWRITE_MODEL": t["model"],
        # 工作流生图槽位（异步任务式，base_url 由路由覆盖）
        "DASHSCOPE_API_KEY": w["api_key"],
        "DASHSCOPE_BASE_URL": w["base_url"],
        "WANX_MODEL": w["model"],
        # 原生生图槽位
        "OPENAI_API_KEY": n["api_key"],
        "OPENAI_BASE_URL": n["base_url"],
        "GPT_IMAGE_MODEL": n["model"],
        # 上游 validate() 仅查非空；原生路线 C 不在变体轨道
        "GEMINI_API_KEY": "placeholder-not-used",
    }


def env_search_codegen() -> dict:
    """1-3 search-codegen：上游 config.py dashscope 分支读 DASHSCOPE_*。"""
    cfg = resolve("deep_research")
    return {
        "DASHSCOPE_API_KEY": cfg["api_key"],
        "DASHSCOPE_BASE_URL": cfg["base_url"],
        "DASHSCOPE_MODEL": cfg["model"],
    }


def env_learning_from_experience() -> dict:
    """7-2 learning-from-experience：上游 llm_agent.py 的 LLM_PROVIDER=dashscope
    分支走 agentbook.providers 注册表（key_vars=DASHSCOPE_API_KEY、
    base_url_var=DASHSCOPE_BASE_URL，见 registry.py:34-35）。"""
    cfg = resolve("text_only")
    env = {
        "LLM_PROVIDER": "dashscope",
        "DASHSCOPE_API_KEY": cfg["api_key"],
        "DASHSCOPE_MODEL": cfg["model"],
    }
    if cfg["base_url"]:
        env["DASHSCOPE_BASE_URL"] = cfg["base_url"]
    return env


def contract_context() -> dict:
    """1-1 context：上游 main.py --provider 走注册表 resolve_backend。
    返回 {"env": …, "args": …}；args 为透传给上游 main.py 的默认参数。"""
    cfg = resolve("text_only")
    provider = cfg["provider"]          # 期望 "zhipu"；若上游 SUPPORTED_PROVIDERS 不含，
    return {                            # 回退 openrouter 通用槽（见 learn/README.md）。
        "env": {
            "ZHIPU_API_KEY": cfg["api_key"],
            "ZHIPU_BASE_URL": cfg["base_url"],
            "MODEL_NAME": cfg["model"],
        },
        "args": ["--provider", provider, "--model", cfg["model"]],
    }


_CONTRACTS = {
    "image-gen-workflow": {"env": env_image_gen_workflow},
    "search-codegen": {"env": env_search_codegen},
    "learning-from-experience": {"env": env_learning_from_experience},
    "context": {"env": lambda: contract_context()["env"],
                "args": lambda: contract_context()["args"]},
}


def apply_env(exp: str) -> dict:
    """装载根 .env 后，把实验 exp 的契约 env 写入 os.environ，返回该 env dict。"""
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    env = _CONTRACTS[exp]["env"]()
    os.environ.update(env)
    return env


def default_args(exp: str) -> list:
    """实验 exp 的默认透传参数（无则空表）。"""
    fn = _CONTRACTS[exp].get("args")
    return fn() if fn else []


def experiments() -> list:
    return sorted(_CONTRACTS)
