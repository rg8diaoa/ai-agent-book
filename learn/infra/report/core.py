"""Report 通用中间模型与构造校验。

Report 是四个实验异构证据统一后的 dict 形状：顶层 title/meta/task/summary_columns/arms/footnotes，
每臂 name/code/badge/cells/sections，section 支持 pre|list|table|note|kv 五种 kind，足以表达
全部实验形状普查内容（异构字段经 kv/table 节表达）。cells 值为 str，或含 text/tone 的强调
dict（tone ∈ ok|fail|warn|na，渲染内核以对应语义柔色对强调，如编造数字警示）。渲染内核只
消费通过 make_report 的 Report。

make_report() 对转换器产出的形状逐条校验，非法输入一律抛 ReportShapeError（消息以字段路径
开头，如 arms[0].badge.kind），校验通过后原样返回输入 dict，仅做一处浅规范化：每臂 cells
缺失的 summary_columns 列自动补空串，多余列报错。
"""

_BADGE_KINDS = ("ok", "fail", "warn", "na")
_ALIGNS = ("left", "center")
_SECTION_KINDS = ("pre", "list", "table", "note", "kv")


class ReportShapeError(ValueError):
    """Report 形状不满足契约；错误消息以字段路径开头（如 arms[0].badge.kind）。"""


def _fail(path, message):
    raise ReportShapeError(f"{path}: {message}")


def _str(value, path):
    if not isinstance(value, str):
        _fail(path, f"期望 str，得到 {type(value).__name__}")
    return value


def _nonempty_str(value, path):
    _str(value, path)
    if not value:
        _fail(path, "不可为空串")
    return value


def _list(value, path):
    if not isinstance(value, list):
        _fail(path, f"期望 list，得到 {type(value).__name__}")
    return value


def _dict(value, path):
    if not isinstance(value, dict):
        _fail(path, f"期望 dict，得到 {type(value).__name__}")
    return value


def _require_keys(obj, keys, path):
    for key in keys:
        if key not in obj:
            _fail(f"{path}.{key}", f"缺少必填键 {key}")


def make_report(report: dict) -> dict:
    if not isinstance(report, dict):
        raise ReportShapeError(f"report: 期望 dict，得到 {type(report).__name__}")

    if "title" not in report:
        _fail("title", "缺少必填键 title")
    _nonempty_str(report["title"], "title")

    if "meta" not in report:
        _fail("meta", "缺少必填键 meta")
    meta = _list(report["meta"], "meta")
    for i, item in enumerate(meta):
        _str(item, f"meta[{i}]")

    task = report.get("task")
    if task is not None:
        _str(task, "task")

    columns = report.get("summary_columns")
    if columns is None:
        _fail("summary_columns", "缺少必填键 summary_columns")
    _list(columns, "summary_columns")
    if not columns:
        _fail("summary_columns", "不可为空列表")
    column_keys = []
    for i, column in enumerate(columns):
        path = f"summary_columns[{i}]"
        _dict(column, path)
        _require_keys(column, ("key", "title"), path)
        _nonempty_str(column["key"], f"{path}.key")
        _nonempty_str(column["title"], f"{path}.title")
        align = column.get("align", "left")
        if align not in _ALIGNS:
            _fail(f"{path}.align", f"期望 left|center（缺省 left），得到 {align!r}")
        if column["key"] in column_keys:
            _fail(f"{path}.key", f"列 key 重复：{column['key']!r}")
        column_keys.append(column["key"])

    if "arms" not in report:
        _fail("arms", "缺少必填键 arms")
    arms = _list(report["arms"], "arms")
    codes = set()
    for i, arm in enumerate(arms):
        _validate_arm(arm, i, column_keys, codes)

    if "footnotes" not in report:
        _fail("footnotes", "缺少必填键 footnotes")
    _list(report["footnotes"], "footnotes")

    return report


def _validate_arm(arm, index, column_keys, codes):
    path = f"arms[{index}]"
    _dict(arm, path)
    _require_keys(arm, ("name", "code", "badge", "cells", "sections"), path)
    _nonempty_str(arm["name"], f"{path}.name")
    _nonempty_str(arm["code"], f"{path}.code")
    if arm["code"] in codes:
        _fail(f"{path}.code", f"臂 code 重复：{arm['code']!r}")
    codes.add(arm["code"])

    badge = _dict(arm["badge"], f"{path}.badge")
    _require_keys(badge, ("text", "kind"), f"{path}.badge")
    _nonempty_str(badge["text"], f"{path}.badge.text")
    if badge["kind"] not in _BADGE_KINDS:
        _fail(f"{path}.badge.kind", f"期望 ok|fail|warn|na，得到 {badge['kind']!r}")

    cells = _dict(arm["cells"], f"{path}.cells")
    for key, value in cells.items():
        if key not in column_keys:
            _fail(f"{path}.cells.{key}", f"未知列 key：{key!r}（不在 summary_columns 中）")
        if isinstance(value, dict):
            _require_keys(value, ("text", "tone"), f"{path}.cells.{key}")
            _nonempty_str(value["text"], f"{path}.cells.{key}.text")
            if value["tone"] not in _BADGE_KINDS:
                _fail(f"{path}.cells.{key}.tone", f"期望 ok|fail|warn|na，得到 {value['tone']!r}")
        elif not isinstance(value, str):
            _fail(f"{path}.cells.{key}", f"期望 str 或含 text/tone 的强调 dict，得到 {type(value).__name__}")
    for key in column_keys:
        if key not in cells:
            cells[key] = ""

    sections = _list(arm["sections"], f"{path}.sections")
    for i, section in enumerate(sections):
        _validate_section(section, f"{path}.sections[{i}]")


def _validate_section(section, path):
    _dict(section, path)
    _require_keys(section, ("title", "kind"), path)
    _nonempty_str(section["title"], f"{path}.title")
    kind = section["kind"]
    if kind not in _SECTION_KINDS:
        _fail(f"{path}.kind", f"期望 pre|list|table|note|kv，得到 {kind!r}")
    if kind in ("pre", "note"):
        _require_keys(section, ("text",), path)
        _str(section["text"], f"{path}.text")
    elif kind == "list":
        _validate_list_section(section, path)
    elif kind == "table":
        _validate_table_section(section, path)
    else:
        _validate_kv_section(section, path)


def _validate_list_section(section, path):
    _require_keys(section, ("items",), path)
    items = _list(section["items"], f"{path}.items")
    for i, item in enumerate(items):
        item_path = f"{path}.items[{i}]"
        if isinstance(item, str):
            continue
        if isinstance(item, dict):
            _require_keys(item, ("summary", "body"), item_path)
            _str(item["summary"], f"{item_path}.summary")
            _str(item["body"], f"{item_path}.body")
        else:
            _fail(item_path, "期望 str 或含 summary/body 的 dict")


def _validate_table_section(section, path):
    _require_keys(section, ("headers", "rows"), path)
    headers = _list(section["headers"], f"{path}.headers")
    for i, header in enumerate(headers):
        _str(header, f"{path}.headers[{i}]")
    rows = _list(section["rows"], f"{path}.rows")
    for i, row in enumerate(rows):
        row_path = f"{path}.rows[{i}]"
        _list(row, row_path)
        if len(row) != len(headers):
            _fail(row_path, f"行长度 {len(row)} 与 headers 长度 {len(headers)} 不一致")


def _validate_kv_section(section, path):
    _require_keys(section, ("pairs",), path)
    pairs = _list(section["pairs"], f"{path}.pairs")
    for i, pair in enumerate(pairs):
        pair_path = f"{path}.pairs[{i}]"
        if not isinstance(pair, (list, tuple)):
            _fail(pair_path, "期望 [key, value] 二元组")
        if len(pair) != 2:
            _fail(pair_path, f"期望长度 2 的二元组，得到长度 {len(pair)}")
