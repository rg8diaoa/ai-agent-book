"""任务模型路由（原 agentbook 外挂层，现为 learn 子包）。"""
from .model_router import resolve, RouterError

__all__ = ["resolve", "RouterError"]
