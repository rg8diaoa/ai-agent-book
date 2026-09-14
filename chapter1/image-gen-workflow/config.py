"""
配置文件 - 实验 1-4 文生图工作流与原生图像生成的对照

三条外部依赖：
- 改写节点 LLM：Kimi（Moonshot，OpenAI 兼容接口）
- 工作流路线生图工具：DashScope 通义万相（异步任务接口）
  注：实验设计首选 SiliconFlow 托管的 FLUX.1 / Stable Diffusion 系列，
  实测该账号 FLUX/SD 模型已下线（Model disabled）且余额为 0，
  故正式运行改用 DashScope 国际站的 wan2.2-t2i-flash（经典扩散式文生图模型，
  接受 SD 风格提示词与负面提示词）。详见 README「模型选型实录」。
- 原生路线：gemini-3-pro-image（书稿所称 Nano Banana 2）及 OpenAI gpt-image-2
"""

import os
from typing import List

from dotenv import load_dotenv

# 从工作目录向上查找最近的 .env，仓库根目录放一份即可服务所有章节
load_dotenv()

from agentbook.model_router import resolve


class Config:
    """配置类（所有密钥只从环境变量读取，不写入任何文件）"""

    # ---- 改写节点：任务路由 ----
    _text_only = resolve("text_only")
    TEXT_ONLY_PROVIDER: str = _text_only["provider"]
    TEXT_ONLY_API_KEY: str = _text_only["api_key"]
    TEXT_ONLY_BASE_URL: str = _text_only["base_url"]
    TEXT_ONLY_MODEL: str = _text_only["model"]

    # ---- 工作流路线生图：任务路由（异步任务式 API，base_url 由路由覆盖）----
    _image_workflow = resolve("image_workflow")
    IMAGE_WORKFLOW_PROVIDER: str = _image_workflow["provider"]
    IMAGE_WORKFLOW_API_KEY: str = _image_workflow["api_key"]
    IMAGE_WORKFLOW_BASE_URL: str = _image_workflow["base_url"]
    IMAGE_WORKFLOW_MODEL: str = _image_workflow["model"]
    IMAGE_WORKFLOW_SIZE: str = _image_workflow["params"].get("size", "1024*1024")

    # ---- 工作流路线生图工具（首选，实测不可用）：SiliconFlow ----
    SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
    SILICONFLOW_BASE_URL: str = os.getenv(
        "SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1"
    )
    SILICONFLOW_IMAGE_MODEL: str = os.getenv(
        "SILICONFLOW_IMAGE_MODEL", "black-forest-labs/FLUX.1-schnell"
    )

    # ---- 原生路线 A：Gemini 3 Pro Image（书稿所称 Nano Banana 2）----
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_IMAGE_MODEL: str = os.getenv(
        "GEMINI_IMAGE_MODEL", "gemini-3-pro-image"
    )

    # ---- 生图节点（原生路线）：任务路由 ----
    _image_native = resolve("image_native")
    IMAGE_NATIVE_PROVIDER: str = _image_native["provider"]
    IMAGE_NATIVE_API_KEY: str = _image_native["api_key"]
    IMAGE_NATIVE_BASE_URL: str = _image_native["base_url"]
    IMAGE_NATIVE_MODEL: str = _image_native["model"]

    # ---- 运行参数 ----
    TASK_POLL_INTERVAL: float = float(os.getenv("TASK_POLL_INTERVAL", "5"))
    TASK_POLL_TIMEOUT: float = float(os.getenv("TASK_POLL_TIMEOUT", "180"))

    @classmethod
    def required_env(cls) -> List[str]:
        return ["TEXT_ONLY_API_KEY", "IMAGE_NATIVE_API_KEY"]

    @classmethod
    def validate(cls) -> bool:
        missing = [name for name in cls.required_env() if not getattr(cls, name)]
        if missing:
            print(f"错误: 缺少环境变量: {', '.join(missing)}")
            print("请参考 env.example 配置后重试。")
            return False
        return True
