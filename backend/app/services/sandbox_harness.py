"""
Runs ONE student program inside the practice sandbox. Started by code_runner.py as:
    python -I -S -B sandbox_harness.py main.py CPU_SECONDS MEMORY_MB
(-I isolated mode, -S no site-packages, -B no .pyc files). The harness sets the OS
limits on itself before any student code runs (no preexec_fn in the threaded server),
and the parent kills the whole process group on timeout.

Layers of protection, in order:
  1. an import guard: only a short list of standard modules can be imported
  2. a Python audit hook (cannot be removed once installed) that blocks
     subprocesses, os.system/exec/fork, sockets (no network), ctypes, file writes,
     deleting/renaming files, and reading any file outside the Python stdlib
  3. OS limits from the parent (no new processes, 1 MB files, memory cap, CPU time)
"""
import sys

ALLOWED = {
    "math", "cmath", "random", "string", "re", "collections", "itertools", "functools", "heapq", "bisect",
    "statistics", "fractions", "decimal", "operator", "array", "copy", "typing", "dataclasses", "datetime",
    "time", "sys", "json", "enum", "numbers", "abc", "textwrap", "unicodedata", "io", "queue", "pprint",
}
BLOCKED_EVENTS = (
    "subprocess.", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty", "os.kill",
    "os.killpg", "os.remove", "os.unlink", "os.rename", "os.replace", "os.rmdir", "os.mkdir", "os.chmod",
    "os.chown", "os.symlink", "os.link", "os.truncate", "os.chdir", "os.putenv", "os.unsetenv", "os.listdir",
    "os.scandir", "os.walk", "socket.", "ctypes.", "shutil.", "pty.", "fcntl.", "resource.", "signal.",
    "urllib.", "http.", "ftplib.", "smtplib.", "webbrowser.", "sys._getframe", "sys.setprofile", "sys.settrace",
    "code.__new__", "marshal.", "pickle.", "import_module", "winreg.",
)


class SandboxViolation(Exception):
    pass


def _apply_limits(cpu_seconds: int, mem_mb: int) -> None:
    import resource
    mem = mem_mb * 1024 * 1024
    for res, val in ((resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds + 1)), (resource.RLIMIT_AS, (mem, mem)),
                     (resource.RLIMIT_FSIZE, (1 << 20, 1 << 20)), (resource.RLIMIT_NOFILE, (64, 64)),
                     (resource.RLIMIT_CORE, (0, 0)), (resource.RLIMIT_NPROC, (0, 0))):
        try:
            resource.setrlimit(res, val)
        except (ValueError, OSError):
            pass


def main() -> None:
    import builtins
    import os

    if len(sys.argv) >= 4:
        _apply_limits(int(sys.argv[2]), int(sys.argv[3]))

    program_path = os.path.abspath(sys.argv[1])
    workdir = os.path.dirname(program_path)
    with open(program_path, encoding="utf-8") as fh:
        source = fh.read()
    stdlib_dirs = tuple({os.path.dirname(os.__file__), sys.base_prefix, sys.prefix})

    # Pre-import the allowed modules so later imports do not need to open files.
    for name in ("math", "collections", "itertools", "functools", "heapq", "bisect", "string", "re", "random",
                 "statistics", "fractions", "decimal", "operator", "array", "copy", "typing", "dataclasses",
                 "datetime", "time", "json", "enum", "textwrap", "io", "queue", "pprint", "unicodedata", "cmath"):
        try:
            __import__(name)
        except Exception:
            pass

    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        top = name.split(".")[0]
        if level == 0 and top not in ALLOWED:
            raise ImportError(f"Import of '{top}' is not allowed in the practice runner. "
                              f"Allowed: {', '.join(sorted(ALLOWED))}.")
        return real_import(name, globals, locals, fromlist, level)

    def hook(event, args):
        if event == "open":
            path = args[0]
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else 0
            if isinstance(path, int):
                return  # already-open descriptors (stdin/stdout)
            p = os.path.abspath(os.fsdecode(path)) if path is not None else ""
            if isinstance(mode, str):
                writing = any(c in mode for c in "wax+")
            else:  # os.open(): look at the flags
                writing = bool((flags or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC))
            if writing:
                raise SandboxViolation("Writing files is not allowed in the practice runner.")
            if not (p.startswith(stdlib_dirs) or p == program_path):
                raise SandboxViolation("Reading files is not allowed in the practice runner. Read input from stdin.")
            return
        if event.startswith(BLOCKED_EVENTS):
            raise SandboxViolation(f"'{event}' is not allowed in the practice runner (no system, network or file access).")

    builtins.__import__ = guarded_import
    sys.addaudithook(hook)
    sys.setrecursionlimit(10000)
    code = compile(source, "main.py", "exec")
    namespace = {"__name__": "__main__", "__builtins__": builtins}
    try:
        exec(code, namespace)
    except SandboxViolation as exc:
        sys.stdout.flush()
        print(f"SandboxViolation: {exc}", file=sys.stderr)
        sys.exit(3)
    finally:
        del workdir


if __name__ == "__main__":
    main()
