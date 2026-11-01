"""
Safe(ish) Python runner for coding practice.

Each run: a fresh temp directory, the student's code in main.py, and a child
Python process started through sandbox_harness.py with:
  * a wall-clock timeout (process group killed when it expires)
  * CPU-time, memory (address space), file-size, open-file and process limits
  * an empty environment, isolated mode, no site-packages
  * an audit hook that blocks network, subprocesses, file writes and file reads
Output is compared to the expected output after normalising whitespace at line ends.

This is a practice runner for a student project, not a hardened multi-tenant judge.
For a public deployment with untrusted users, also run the app in a container with no
network egress (see docs/KNOWN_LIMITATIONS.md).
"""
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.config import settings

HARNESS = Path(__file__).with_name("sandbox_harness.py")
MAX_OUTPUT = 64 * 1024
_slots = threading.BoundedSemaphore(2)  # at most 2 student programs at once (small servers)


def normalise(text: str) -> str:
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").split("\n")]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def run_python(code: str, stdin: str, timeout: float | None = None) -> dict:
    """Run code once. Returns {status, stdout, stderr, time_ms}. status: ok | error | timeout | blocked."""
    timeout = timeout or settings.code_timeout_seconds
    workdir = tempfile.mkdtemp(prefix="cp-run-")
    try:
        main = Path(workdir) / "main.py"
        main.write_text(code, encoding="utf-8")
        cmd = [sys.executable, "-I", "-S", "-B", str(HARNESS), str(main), str(int(timeout) + 1), str(settings.code_memory_mb)]
        env = {"PATH": "/usr/bin:/bin", "PYTHONIOENCODING": "utf-8", "LANG": "C.UTF-8", "PYTHONHASHSEED": "0"}
        with _slots:
            started = time.monotonic()
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    cwd=workdir, env=env, start_new_session=True)
            try:
                out, err = proc.communicate(stdin.encode("utf-8"), timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                out, err = proc.communicate()
            elapsed = int((time.monotonic() - started) * 1000)
        stdout = out[:MAX_OUTPUT].decode("utf-8", "replace")
        stderr = err[-4000:].decode("utf-8", "replace")
        if timed_out or proc.returncode in (-signal.SIGXCPU, -signal.SIGKILL):
            return {"status": "timeout", "stdout": stdout, "stderr": f"Time limit exceeded ({timeout:g} s). Check for an infinite loop or a slow approach.", "time_ms": elapsed}
        if proc.returncode == 3 and "SandboxViolation" in stderr:
            return {"status": "blocked", "stdout": stdout, "stderr": stderr.split("SandboxViolation: ")[-1].strip(), "time_ms": elapsed}
        if proc.returncode != 0:
            if "MemoryError" in stderr:
                stderr = f"Memory limit exceeded ({settings.code_memory_mb} MB).\n" + stderr
            return {"status": "error", "stdout": stdout, "stderr": _clean_trace(stderr, workdir), "time_ms": elapsed}
        return {"status": "ok", "stdout": stdout, "stderr": "", "time_ms": elapsed}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _clean_trace(stderr: str, workdir: str) -> str:
    """Hide the harness frames and temp paths so the student sees only their own error."""
    lines = [ln for ln in stderr.splitlines() if "sandbox_harness.py" not in ln and "exec(code, namespace)" not in ln]
    return "\n".join(lines).replace(workdir + "/", "").strip()


def run_tests(code: str, tests: list[dict], include_hidden: bool) -> dict:
    """Run code against test cases. Hidden tests show pass/fail only, never their data."""
    chosen = [t for t in tests if include_hidden or not t.get("hidden")]

    def one(idx_t):
        idx, t = idx_t
        r = run_python(code, t["input"])
        passed = r["status"] == "ok" and normalise(r["stdout"]) == normalise(t["output"])
        res = {"index": idx + 1, "hidden": bool(t.get("hidden")), "passed": passed, "status": r["status"],
               "time_ms": r["time_ms"]}
        if not t.get("hidden"):
            res.update({"input": t["input"], "expected": t["output"], "output": r["stdout"][:4000], "error": r["stderr"]})
        elif not passed:
            res["error"] = r["stderr"].splitlines()[-1] if r["stderr"] else "Wrong answer on a hidden test."
        return res

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, list(enumerate(chosen))))
    passed = sum(r["passed"] for r in results)
    return {"passed": passed, "total": len(results), "all_passed": passed == len(results) and bool(results), "results": results}
