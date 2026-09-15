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
import shutil
import subprocess
import sys
import threading
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


def transcribe_artifacts(exp: str, cwd: Path, evidence_dir: Path, ts: str) -> list:
    """按 contracts.artifacts(exp) 声明，把 cwd 下命中的上游产物原样复制改名进 evidence_dir。

    纯复制（shutil.copy2），不解析、不改写、不重组；目标同名已存在则跳过不覆盖。
    """
    copied: list = []
    for pattern in contracts.artifacts(exp):
        hits = [p for p in sorted(cwd.glob(pattern)) if p.is_file()]
        if not hits:
            print(f"[adapter] 上游产物：无匹配（{pattern}）")
            continue
        for hit in hits:
            dest = evidence_dir / f"{ts}_{exp}_{hit.name}"
            if dest.exists():
                print(f"[adapter] 上游产物：目标已存在，跳过 {dest.name}")
                continue
            shutil.copy2(hit, dest)
            copied.append(dest)
            print(f"[adapter] 已转录上游产物 {hit.name} -> {dest.name}")
    return copied


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

    child_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(errors="replace")
            except (ValueError, OSError):
                pass

    print(f"[adapter] exp={args.exp} cwd={cwd}")
    print("[adapter] 契约 env 注入完成（真实 provider/model 见 evidence json）")
    if args.evidence:
        out_buf: list = []
        err_buf: list = []

        def _pump(stream, sink, to_stderr=False):
            for line in stream:
                sink.append(line)
                print(line, end="", file=sys.stderr if to_stderr else sys.stdout)

        with subprocess.Popen(cmd, cwd=str(cwd), env=child_env,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, encoding="utf-8", errors="replace") as proc:
            t_out = threading.Thread(target=_pump, args=(proc.stdout, out_buf), daemon=True)
            t_err = threading.Thread(target=_pump, args=(proc.stderr, err_buf, True), daemon=True)
            t_out.start()
            t_err.start()
            try:
                proc.wait(timeout=1800)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
            except KeyboardInterrupt:
                proc.kill()
                proc.wait()
                raise
            t_out.join(timeout=30)
            t_err.join(timeout=30)

        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        out = EVIDENCE_DIR / f"{ts}_run_{args.exp}.json"
        env_summary = {k: v for k, v in os.environ.items()
                       if k in ("LLM_PROVIDER", "MODEL_NAME")
                       or k.endswith(("_MODEL",)) and not k.endswith("API_KEY")}
        stdout_all = "".join(out_buf)
        stderr_all = "".join(err_buf)
        out.write_text(json.dumps({
            "kind": "variant", "exp": args.exp, "cmd": cmd,
            "routes": env_summary,
            "exit_code": proc.returncode,
            "stdout_tail": stdout_all[-2000:], "stderr_tail": stderr_all[-1000:],
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        }, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        print(f"🧾 证据已写 {out.relative_to(ROOT)}")
        transcribe_artifacts(args.exp, cwd, EVIDENCE_DIR, ts)
        if proc.returncode != 0:
            print(f"[adapter] 子进程 exit={proc.returncode}，详见上方输出与证据 json", file=sys.stderr)
        return proc.returncode

    proc = subprocess.run(cmd, cwd=str(cwd), env=child_env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
