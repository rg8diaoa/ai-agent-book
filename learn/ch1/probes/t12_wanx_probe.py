"""T12: image_workflow 路由（wanx 异步任务式）连通探测：提交→轮询→下载全流程。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "chapter1" / "image-gen-workflow"))
from pipeline import generate_image_wanx

image_bytes, mime, recs = generate_image_wanx(
    "a red apple on a white wooden table, soft daylight", ""
)
print("OK bytes:", len(image_bytes), "mime:", mime)
print("calls:", [(r.get("provider"), r.get("model")) for r in recs])
