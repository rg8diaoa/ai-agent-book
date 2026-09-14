"""第二轨验收（路由变体）：用 learn/router 路由配置跑各实验核心流程，产出 evidence_*。

与作者基线分轨记录、永不混同：
- 第一轨：chapter1/**/validation/（作者 kimi/moonshot/qwen 观测，锚定 runner 产出）
- 第二轨：learn/ch1/evidence/（路由 provider/model + 耗时 + 产物摘要；经 learn/ch1/contracts.py 契约注入）
用法：
  .venv\\Scripts\\python.exe learn\\infra\\acceptance_router.py builtin|react|workflow|native|llm|all
  .venv\\Scripts\\python.exe learn\\infra\\acceptance_router.py workflow --requirement "一段自定义需求文本"
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "learn" / "ch1" / "evidence"


def _contracts_env(exp: str) -> dict:
    sys.path.insert(0, str(ROOT))
    from learn.ch1 import contracts

    return contracts.apply_env(exp)

QUESTION_1_2 = "现在比特币的价格是多少美元？"
DEFAULT_REQUIREMENT = "A focused AGI programmer coding late at night, dual monitors glowing, warm desk lamp"


def _dump_evidence(name: str, payload: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = OUT_DIR / f"{ts}_{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"🧾 证据已写 {path.relative_to(ROOT)}")
    return path


def _truncate(obj, limit: int = 800):
    if isinstance(obj, str):
        return obj if len(obj) <= limit else obj[:limit] + f"...(len={len(obj)})"
    if isinstance(obj, list):
        return [_truncate(x, limit) for x in obj]
    if isinstance(obj, dict):
        return {k: _truncate(v, limit) for k, v in obj.items()}
    return obj


def run_builtin() -> dict:
    sys.path.insert(0, str(ROOT / "learn" / "ch1" / "variants" / "web-search-agent"))
    from main_route import run_builtin as _run

    started = time.time()
    r = _run(QUESTION_1_2, timeout=180.0)
    return {"latency_s": round(time.time() - started, 1), "result": _truncate(r)}


def run_react() -> dict:
    sys.path.insert(0, str(ROOT / "learn" / "ch1" / "variants" / "web-search-agent"))
    from main_route import run_react as _run

    started = time.time()
    r = _run(QUESTION_1_2, max_rounds=5, timeout=120.0)
    return {"latency_s": round(time.time() - started, 1), "result": _truncate(r)}


def _requirement_text(arg: str) -> str:
    """--requirement 既接受 1-4 main.py 的预设 id，也接受自由文本。"""
    try:
        sys.path.insert(0, str(ROOT / "chapter1" / "image-gen-workflow"))
        from main import REQUIREMENTS

        for item in REQUIREMENTS:
            if item.get("id") == arg:
                return item.get("text") or item.get("requirement") or arg
    except Exception:
        pass
    return arg


def _recent_pngs() -> list:
    out = []
    for base in (ROOT / "chapter1" / "image-gen-workflow").rglob("*.png"):
        if time.time() - base.stat().st_mtime < 600:
            out.append({
                "file": str(base.relative_to(ROOT)),
                "sha256": hashlib.sha256(base.read_bytes()).hexdigest(),
                "bytes": base.stat().st_size,
            })
    return out


def _run_image_route(route: str, requirement: str) -> dict:
    sys.path.insert(0, str(ROOT))
    from learn.ch1 import contracts

    contracts.apply_env("image-gen-workflow")
    sys.path.insert(0, str(ROOT / "chapter1" / "image-gen-workflow"))
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    from pipeline import ROUTE_RUNNERS

    started = time.time()
    result = ROUTE_RUNNERS[route](requirement)
    return {
        "latency_s": round(time.time() - started, 1),
        "requirement": requirement,
        "result": _truncate(result),
        "images": _recent_pngs(),
    }


def run_workflow(requirement: str) -> dict:
    return _run_image_route("workflow", requirement)


def run_native(requirement: str) -> dict:
    return _run_image_route("native_gptimage", requirement)


def run_llm() -> dict:
    started = time.time()
    proc = subprocess.run(
        [sys.executable, "experiment.py", "--mode", "llm", "--llm-episodes", "1"],
        cwd=ROOT / "chapter1" / "learning-from-experience",
        env={**os.environ, **_contracts_env("learning-from-experience")},
        capture_output=True, text=True, timeout=900,
    )
    return {
        "latency_s": round(time.time() - started, 1),
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-1000:],
    }


def main():
    p = argparse.ArgumentParser(description="第二轨验收（路由变体证据，不与作者基线混同）")
    p.add_argument("target", choices=["builtin", "react", "workflow", "native", "llm", "all"])
    p.add_argument("--requirement", default=DEFAULT_REQUIREMENT,
                   help="1-4 需求文本，或 1-4 main.py 的预设 id（如 agi-programmer）")
    a = p.parse_args()

    targets = ["builtin", "react", "workflow", "native", "llm"] if a.target == "all" else [a.target]
    for t in targets:
        print(f"\n===== 第二轨验收：{t} =====")
        try:
            if t == "builtin":
                payload = run_builtin()
            elif t == "react":
                payload = run_react()
            elif t == "workflow":
                payload = run_workflow(_requirement_text(a.requirement))
            elif t == "native":
                payload = run_native(_requirement_text(a.requirement))
            else:
                payload = run_llm()
            _dump_evidence(t, {
                "kind": "variant",
                "target": t,
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "note": "第二轨：路由模式证据，不与作者基线（validation/）混同",
                **payload,
            })
        except Exception as exc:
            print(f"❌ {t} 失败：{exc!r}")
            _dump_evidence(t, {"kind": "variant", "target": t, "generated_utc":
                               datetime.now(timezone.utc).isoformat(), "error": repr(exc)})


if __name__ == "__main__":
    main()
