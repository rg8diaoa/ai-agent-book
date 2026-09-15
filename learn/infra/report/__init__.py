"""报告器注册表：实验名 → 转换器模块的显式 dict。

契约：每个已注册的转换器模块必须暴露三个成员——
- EXP：str，实验标识（与注册键一致）
- matches(raw) -> bool：按字段指纹判断源 json 是否归此转换器
- transform(raw, source_path=None) -> dict：把源 json 转为 Report 形状（经 core.make_report 校验）

transforms 子模块尚未全部落地（并行开发），getattr 跳过缺失模块是刻意的并行安全设计：
注册表只含当前可导入的转换器，新增实验只需新增转换器文件并在 _ENTRIES 补一行。
"""

_ENTRIES = ["context", "search_codegen", "image_gen_workflow", "learning_from_experience"]

def _load():
    from learn.infra.report import transforms
    out = {}
    for name in _ENTRIES:
        mod = getattr(transforms, name, None)
        if mod is not None:
            out[name] = mod
    return out

REGISTRY = _load()
