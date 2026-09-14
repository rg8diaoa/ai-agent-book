"""运行适配器：按 learn/ch1/contracts.py 契约注入环境变量，原样运行上游实验脚本。

用法：
  .venv\\Scripts\\python.exe learn\\ch1\\run.py --list
  .venv\\Scripts\\python.exe learn\\ch1\\run.py --exp image-gen-workflow -- --route workflow --requirement agi-programmer
  .venv\\Scripts\\python.exe learn\\ch1\\run.py --exp search-codegen --evidence
`--` 之后的参数原样透传给上游脚本（追加在契约默认参数之后，可覆盖同名 flag）。
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # ROOT

from learn.ch1 import contracts

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "learn" / "ch1" / "evidence"

ENTRIES = {
    "image-gen-workflow": ROOT / "chapter1" / "image-gen-workflow" / "main.py",
    "search-codegen": ROOT / "chapter1" / "search-codegen" / "main.py",
    "learning-from-experience": ROOT / "chapter1" / "learning-from-experience" / "experiment.py",
    "context": ROOT / "chapter1" / "context" / "main.py",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="ch1 实验运行适配器（上游脚本零改动）")
    parser.add_argument("--exp", choices=contracts.experiments(),
                        help="实验名（--list 查看）")
    parser.add_argument("--list", action="store_true", help="列出实验（零 API 调用）")
    parser.add_argument("--evidence", action="store_true",
                        help="收集 stdout/stderr 与路由摘要，写 learn/ch1/evidence/")
    parser.add_argument("passthrough", nargs="*",
                        help="透传给上游脚本的参数（写在 -- 之后）")
    args = parser.parse_args()

    if args.list:
        for exp in contracts.experiments():
            print(exp)
        return 0
    if not args.exp:
        parser.error("--exp 或 --list 必选其一")

    contracts.apply_env(args.exp)
    passthrough = contracts.default_args(args.exp) + args.passthrough

    entry = ENTRIES[args.exp]
    cwd = entry.parent
    cmd = [sys.executable, str(entry)] + passthrough

    print(f"[adapter] exp={args.exp} cwd={cwd}")
    print("[adapter] 契约 env 注入完成（真实 provider/model 见 evidence json）")
    if args.evidence:
        proc = subprocess.run(cmd, cwd=str(cwd), env={**os.environ},
                              capture_output=True, text=True, timeout=1800)
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out = EVIDENCE_DIR / f"{ts}_run_{args.exp}.json"
        env_summary = {k: v for k, v in os.environ.items()
                       if k in ("LLM_PROVIDER", "MODEL_NAME")
                       or k.endswith(("_MODEL",)) and not k.endswith("API_KEY")}
        out.write_text(json.dumps({
            "kind": "variant", "exp": args.exp, "cmd": cmd,
            "routes": env_summary,
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-1000:],
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"🧾 证据已写 {out.relative_to(ROOT)}")
        print(proc.stdout[-3000:])
        if proc.returncode != 0:
            print(proc.stderr[-1500:], file=sys.stderr)
        return proc.returncode

    proc = subprocess.run(cmd, cwd=str(cwd), env={**os.environ})
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
