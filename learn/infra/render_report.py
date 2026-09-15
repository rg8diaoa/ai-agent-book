"""证据中文报告渲染内核与 CLI。

render_report(report) 只消费经 learn.infra.report.core.make_report 校验的 Report 形状
（顶层 title/meta/task/summary_columns/arms/footnotes；每臂 name/code/badge/cells/sections，
cells 值支持 str 或 {text,tone} 强调 dict；
section 支持 pre|note|list|table|kv 五种 kind），输出单文件自包含中文 HTML：
utf-8、零外部资源（系统字体三栈 + 内联 CSS/JS，无外链字体/图标/脚本/样式）。
视觉遵循研究型编辑风：暖白画布 #FBFBFA、卡片 #FFFFFF、结构边框 1px solid #EAEAEA、
badge 语义柔色 pill、无渐变无重阴影；动效只动 transform/opacity，滚动淡入由内联
IntersectionObserver 触发（不监听 scroll），臂节按 --index 级联，prefers-reduced-motion
下全部动画降级关闭。

CLI 用法：
  .venv\\Scripts\\python.exe learn\\infra\\render_report.py --input <json> [--output <html>]
      [--exp <name>] [--open] [--port 8933]

--exp 省略时按 REGISTRY 各转换器 matches(raw) 字段指纹自动识别，取首个命中；
全部不命中或注册表为空时 stderr 中文报错并以退出码 2 结束。默认输出
learn/ch1/notes/assets/<输入文件名去扩展>_report.html；--open 时起本地 HTTP 服务
（绑定 127.0.0.1，服务输出文件所在目录）并打印预览 URL 后阻塞。
"""
import argparse
import functools
import html
import http.server
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from learn.infra.report import REGISTRY
from learn.infra.report.core import make_report

ROOT = Path(__file__).resolve().parents[2]

_CSS = """
:root{
--canvas:#FBFBFA;--card:#FFFFFF;--line:#EAEAEA;--hover:#F9F9F8;
--ink:#2F3437;--ink2:#787774;
--ok-bg:#EDF3EC;--ok-fg:#346538;--fail-bg:#FDEBEC;--fail-fg:#9F2F2D;
--warn-bg:#FBF3DB;--warn-fg:#956400;--na-bg:#E1F3FE;--na-fg:#1F6C9F;
--ease:cubic-bezier(0.16,1,0.3,1);
--sans:-apple-system,'Segoe UI','Helvetica Neue',sans-serif;
--serif:Georgia,'Source Han Serif SC','SimSun',serif;
--mono:'Cascadia Mono',Consolas,'SF Mono',monospace;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--canvas);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.7}
main{max-width:980px;margin:0 auto;padding:44px 24px 72px}
h1,h2,h3{font-family:var(--serif);letter-spacing:-0.02em;font-weight:600;margin:0;color:var(--ink)}
h1{font-size:30px;line-height:1.35}
h2{font-size:20px;line-height:1.5;margin:40px 0 14px}
h3{font-size:15.5px;line-height:1.6;margin:0 0 10px}
.kicker{font-family:var(--mono);font-size:12px;letter-spacing:0.14em;color:var(--ink2);margin:0 0 12px}
.meta{display:flex;flex-direction:column;gap:4px;margin-top:16px;font-family:var(--mono);font-size:12.5px;color:var(--ink2)}
.task{margin-top:18px;background:var(--card);border:1px solid var(--line);border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.04);padding:14px 18px;font-size:14px;white-space:pre-wrap;word-break:break-word}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}
.card-h{margin:0 0 14px}
.scroll-x{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid var(--line);padding:8px 12px;text-align:left;vertical-align:top}
th{font-family:var(--sans);font-weight:600;font-size:12.5px;color:var(--ink2);background:var(--hover);white-space:nowrap}
th.center,td.center{text-align:center}
td{font-family:var(--mono);font-size:12.5px}
tbody tr{transition:background-color 200ms var(--ease)}
tbody tr:hover{background:var(--hover)}
.badge{display:inline-block;font-family:var(--mono);font-size:11.5px;line-height:1.6;padding:1px 11px;border-radius:999px;white-space:nowrap;flex:none}
.badge.ok{background:var(--ok-bg);color:var(--ok-fg)}
.badge.fail{background:var(--fail-bg);color:var(--fail-fg)}
.badge.warn{background:var(--warn-bg);color:var(--warn-fg)}
.badge.na{background:var(--na-bg);color:var(--na-fg)}
.tone{display:inline-block;border-radius:4px;padding:0 6px}
.tone.ok{background:var(--ok-bg);color:var(--ok-fg)}
.tone.fail{background:var(--fail-bg);color:var(--fail-fg)}
.tone.warn{background:var(--warn-bg);color:var(--warn-fg)}
.tone.na{background:var(--na-bg);color:var(--na-fg)}
details.arm{background:var(--card);border:1px solid var(--line);border-radius:12px;margin:0 0 10px;overflow:hidden}
details.arm>summary{cursor:pointer;list-style:none;display:flex;align-items:center;gap:10px;padding:13px 18px;transition:background-color 200ms var(--ease),transform 120ms var(--ease)}
details.arm>summary::-webkit-details-marker{display:none}
details.arm>summary:hover{background:var(--hover)}
details.arm>summary:active,details.item>summary:active{transform:scale(0.98)}
.arm-name{font-family:var(--serif);font-size:16px;font-weight:600;letter-spacing:-0.02em}
.arm-code{font-family:var(--mono);font-size:12px;color:var(--ink2)}
.arm-spacer{flex:1}
.arm-body{border-top:1px solid var(--line);padding:0 18px 6px}
details[open].arm>.arm-body{animation:unfold 320ms var(--ease) both}
@keyframes unfold{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.sec{padding:14px 0 12px;border-bottom:1px solid var(--line)}
.sec:last-child{border-bottom:none}
.note{color:var(--ink2);font-size:13px;margin:0}
pre{font-family:var(--mono);font-size:12.5px;line-height:1.6;background:var(--hover);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:0;overflow-x:auto;white-space:pre-wrap;word-break:break-word}
ol.plain{margin:0;padding-left:22px}
ol.plain li{margin:5px 0}
details.item{border:1px solid var(--line);border-radius:8px;margin:0 0 6px;background:var(--hover)}
details.item>summary{cursor:pointer;list-style:none;padding:8px 12px;font-size:13px;transition:transform 120ms var(--ease)}
details.item>summary::-webkit-details-marker{display:none}
details.item>summary::before{content:'\\25B8';font-size:11px;color:var(--ink2);margin-right:8px;display:inline-block;transition:transform 200ms var(--ease)}
details[open].item>summary::before{transform:rotate(90deg)}
details[open].item>.item-body{animation:unfold 320ms var(--ease) both;border-top:1px solid var(--line)}
.item-body{padding:10px 12px}
dl.kv{margin:0;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.kv-row{display:grid;grid-template-columns:230px minmax(0,1fr)}
.kv-row+.kv-row{border-top:1px solid var(--line)}
.kv-row dt{font-family:var(--mono);font-size:12px;color:var(--ink2);background:var(--hover);padding:8px 12px;word-break:break-all}
.kv-row dd{margin:0;padding:8px 12px;font-size:13px;white-space:pre-wrap;word-break:break-word}
footer{margin-top:48px;color:var(--ink2);font-size:13px}
footer ol{margin:8px 0 0;padding-left:22px}
footer li{margin:4px 0}
.reveal{opacity:0}
.reveal.in{animation:rise 600ms var(--ease) both;animation-delay:calc(var(--index,0)*80ms)}
@keyframes rise{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:none}}
@media (max-width:640px){.kv-row{grid-template-columns:1fr}.kv-row dt{border-bottom:1px solid var(--line)}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}.reveal{opacity:1!important;transform:none!important}}
"""

_JS = """
(function(){
var els=Array.prototype.slice.call(document.querySelectorAll('.reveal'));
var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if(reduced||!('IntersectionObserver' in window)){els.forEach(function(el){el.classList.add('in')});return}
var io=new IntersectionObserver(function(entries){entries.forEach(function(entry){
if(entry.isIntersecting){entry.target.classList.add('in');io.unobserve(entry.target)}})},
{threshold:0.06,rootMargin:'0px 0px -6% 0px'});
els.forEach(function(el){io.observe(el)});
})();
"""

_SYMBOLS = ("\u2713", "\u2717", "\u26A0")


def _t(value) -> str:
    text = str(value)
    for symbol in _SYMBOLS:
        if symbol in text:
            text = text.replace(symbol, symbol + "\uFE0E")
    return html.escape(text, quote=False)


def _badge_html(badge: dict) -> str:
    return f'<span class="badge {badge["kind"]}">{_t(badge["text"])}</span>'


def _th(col: dict) -> str:
    cls = ' class="center"' if col.get("align") == "center" else ""
    return f"<th{cls}>{_t(col['title'])}</th>"


def _td(value, col: dict) -> str:
    cls = ' class="center"' if col.get("align") == "center" else ""
    if isinstance(value, dict):
        inner = f'<span class="tone {value["tone"]}">{_t(value["text"])}</span>'
    else:
        inner = _t(value)
    return f"<td{cls}>{inner}</td>"


def _summary_table_html(report: dict) -> str:
    columns = report["summary_columns"]
    head = "".join(_th(col) for col in columns)
    rows = "".join(
        "<tr>"
        + "".join(_td(arm["cells"].get(col["key"], ""), col) for col in columns)
        + "</tr>"
        for arm in report["arms"]
    )
    return (
        '<div class="scroll-x"><table class="summary">'
        f'<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _pre_html(section: dict) -> str:
    return f"<pre>{_t(section['text'])}</pre>"


def _note_html(section: dict) -> str:
    return f'<p class="note">{_t(section["text"])}</p>'


def _item_details(item: dict) -> str:
    return (
        f'<details class="item"><summary>{_t(item["summary"])}</summary>'
        f'<div class="item-body"><pre>{_t(item["body"])}</pre></div></details>'
    )


def _list_html(section: dict) -> str:
    chunks: list = []
    str_buf: list = []

    def flush():
        if str_buf:
            items = "".join(f"<li>{_t(x)}</li>" for x in str_buf)
            chunks.append(f'<ol class="plain">{items}</ol>')
            str_buf.clear()

    for item in section["items"]:
        if isinstance(item, str):
            str_buf.append(item)
        else:
            flush()
            chunks.append(_item_details(item))
    flush()
    return "".join(chunks)


def _table_html(section: dict) -> str:
    head = "".join(f"<th>{_t(h)}</th>" for h in section["headers"])
    rows = "".join(
        "<tr>" + "".join(f"<td>{_t(cell)}</td>" for cell in row) + "</tr>"
        for row in section["rows"]
    )
    return (
        '<div class="scroll-x"><table>'
        f'<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _kv_html(section: dict) -> str:
    rows = "".join(
        f'<div class="kv-row"><dt>{_t(pair[0])}</dt><dd>{_t(pair[1])}</dd></div>'
        for pair in section["pairs"]
    )
    return f'<dl class="kv">{rows}</dl>'


_SECTION_HTML = {
    "pre": _pre_html,
    "note": _note_html,
    "list": _list_html,
    "table": _table_html,
    "kv": _kv_html,
}


def _section_html(section: dict) -> str:
    body = _SECTION_HTML[section["kind"]](section)
    return f'<section class="sec"><h3>{_t(section["title"])}</h3>{body}</section>'


def _arm_html(arm: dict, index: int) -> str:
    inner = "".join(_section_html(s) for s in arm["sections"])
    if inner:
        body = f'<div class="arm-body">{inner}</div>'
    else:
        body = '<div class="arm-body"><p class="note">该分组暂无分节内容。</p></div>'
    return (
        f'<details class="arm reveal" style="--index:{index}">'
        f'<summary><span class="arm-name">{_t(arm["name"])}</span>'
        f'<span class="arm-code">{_t(arm["code"])}</span>'
        f'<span class="arm-spacer"></span>{_badge_html(arm["badge"])}</summary>'
        f"{body}</details>"
    )


def render_report(report: dict) -> str:
    title = _t(report["title"])
    meta = "".join(f"<div>{_t(item)}</div>" for item in report["meta"])
    task_html = (
        f'<div class="task">{_t(report["task"])}</div>' if report.get("task") else ""
    )
    summary_card = (
        '<section class="card reveal" style="--index:1">'
        f'<h2 class="card-h">汇总</h2>{_summary_table_html(report)}</section>'
    )
    arms = report["arms"]
    if arms:
        arms_body = "".join(_arm_html(arm, i) for i, arm in enumerate(arms))
        arms_block = f'<section class="arms"><h2>分组详情</h2>{arms_body}</section>'
    else:
        arms_block = ""
    footnotes = report["footnotes"]
    if footnotes:
        items = "".join(f"<li>{_t(note)}</li>" for note in footnotes)
        footer_html = (
            '<footer class="reveal" style="--index:0">'
            f"<h2>脚注</h2><ol>{items}</ol></footer>"
        )
    else:
        footer_html = ""
    return (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{title}</title>\n<style>{_CSS}</style>\n</head>\n<body>\n<main>\n"
        '<header class="reveal" style="--index:0">\n<p class="kicker">证据分析报告</p>\n'
        f"<h1>{title}</h1>\n"
        f'<div class="meta">{meta}</div>\n{task_html}\n</header>\n'
        f"{summary_card}\n{arms_block}\n{footer_html}\n</main>\n"
        '<noscript><style>.reveal{opacity:1;transform:none}</style></noscript>\n'
        f"<script>{_JS}</script>\n</body>\n</html>\n"
    )


def _default_output(src: Path) -> Path:
    assets = ROOT / "learn" / "ch1" / "notes" / "assets"
    return assets / f"{src.stem}_report.html"


def _registry_names() -> str:
    return ", ".join(REGISTRY) if REGISTRY else "（注册表为空：转换器尚未落地）"


def _detect(raw) -> str:
    for name, mod in REGISTRY.items():
        try:
            if mod.matches(raw):
                return name
        except Exception:
            continue
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="render_report",
        description="证据 JSON → 单文件中文 HTML 报告（研究型编辑风）",
    )
    parser.add_argument("--input", required=True, help="输入 json 路径（证据/验收/回执）")
    parser.add_argument(
        "--output",
        help="输出 html 路径（缺省 learn/ch1/notes/assets/<输入文件名去扩展>_report.html）",
    )
    parser.add_argument("--exp", help="显式指定实验转换器（缺省按字段指纹自动识别）")
    parser.add_argument("--open", action="store_true", help="渲染后启动本地预览服务")
    parser.add_argument("--port", type=int, default=8933, help="预览服务端口（默认 8933）")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.is_file():
        print(f"[render_report] 输入文件不存在：{src}", file=sys.stderr)
        return 2
    try:
        raw = json.loads(src.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"[render_report] 输入不是可读 JSON：{exc}", file=sys.stderr)
        return 2

    if args.exp:
        exp = args.exp
        if exp not in REGISTRY:
            print(
                f"[render_report] 未知实验：--exp {exp}。当前可用：{_registry_names()}",
                file=sys.stderr,
            )
            return 2
    else:
        exp = _detect(raw)
        if not exp:
            print(
                "[render_report] 无法自动识别输入形状（注册表所有转换器均未命中）。"
                f"可改用 --exp 显式指定。当前可用：{_registry_names()}",
                file=sys.stderr,
            )
            return 2

    try:
        report = make_report(REGISTRY[exp].transform(raw, source_path=str(src)))
    except Exception as exc:
        print(f"[render_report] 转换或校验失败（exp={exp}）：{exc}", file=sys.stderr)
        return 2

    out = Path(args.output) if args.output else _default_output(src)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_report(report), encoding="utf-8")

    try:
        shown = out.resolve().relative_to(ROOT)
    except ValueError:
        shown = out.resolve()
    print(f"报告已写 {shown}")

    if args.open:
        handler = functools.partial(
            http.server.SimpleHTTPRequestHandler,
            directory=str(out.resolve().parent),
        )
        server = http.server.ThreadingHTTPServer(("127.0.0.1", args.port), handler)
        url = f"http://127.0.0.1:{args.port}/{urllib.parse.quote(out.name)}"
        print(f"预览地址：{url}（Ctrl+C 停止服务）")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
