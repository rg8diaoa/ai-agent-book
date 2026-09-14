"""任务模型路由：model_config.json 的唯一读取入口。

resolve(task) -> {"provider", "base_url", "api_key", "model", "tools"}
校验：route.requires 必须被 model.caps 满足；key 缺失即报错。
"""
import json
import os
from pathlib import Path

_CFG = json.loads(
    (Path(__file__).resolve().parent / "model_config.json").read_text(encoding="utf-8")
)


class RouterError(RuntimeError):
    pass


def resolve(task: str) -> dict:
    route = _CFG["routes"].get(task)
    if route is None:
        raise RouterError(f"未知任务路由 {task!r}，可选：{sorted(_CFG['routes'])}")
    entry = _CFG["models"].get(route["model"])
    if entry is None:
        raise RouterError(f"路由 {task!r} 的模型 {route['model']!r} 未登记在 models 目录")
    missing = sorted(set(route.get("requires", [])) - set(entry.get("caps", [])))
    if missing:
        raise RouterError(f"{route['model']} 缺少 {task} 所需能力 {missing}，caps={entry.get('caps')}")
    provider_id, model_id = route["model"].split("/", 1)
    prov = _CFG["providers"].get(provider_id)
    if prov is None:
        raise RouterError(f"{route['model']} 的厂商 {provider_id!r} 未定义")
    key = os.getenv(prov["api_key_env"], "")
    if not key:
        raise RouterError(f"缺少 {prov['api_key_env']}（写入根 .env）")
    return {
        "provider": provider_id,
        "base_url": route.get("base_url") or prov["base_url"],
        "api_key": key,
        "model": model_id,
        "tools": route.get("tools"),
        "params": route.get("params") or {},
    }
