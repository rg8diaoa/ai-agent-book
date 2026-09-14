"""T10: 路由层冒烟——每条路由可解析、能力校验通过、key 已配置。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # infra→learn→ROOT

from dotenv import load_dotenv

load_dotenv()
from learn.router import resolve

for task in ("text_only", "multimodal", "inline_search", "image_workflow", "image_native", "web_search_api", "deep_research"):
    try:
        cfg = resolve(task)
        print(f"{task:14} -> {cfg['provider']}/{cfg['model']}  key:已配置  tools:{bool(cfg['tools'])}")
    except Exception as e:
        print(f"{task:14} -> ❌ {e}")
