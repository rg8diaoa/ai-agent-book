"""实验转换器包：每实验一个模块，由上级注册表 learn/infra/report/__init__.py 显式注册。

各子模块须暴露三成员：EXP（注册名）、matches(raw)（形状指纹）、
transform(raw, source_path=None)（原始 json → Report，经 core.make_report 校验）。
"""
from learn.infra.report.transforms import context  # noqa: F401
from learn.infra.report.transforms import image_gen_workflow
from learn.infra.report.transforms import learning_from_experience
from learn.infra.report.transforms import search_codegen

__all__ = ["context", "image_gen_workflow", "learning_from_experience", "search_codegen"]
