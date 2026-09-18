from __future__ import annotations

import subprocess
from datetime import datetime
from pathlib import Path


class GitError(RuntimeError):
    pass


def run_git(args: list[str], cwd: Path, check: bool = True) -> str:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        raise GitError("git executable not found; install Git >= 2.30") from exc
    if check and proc.returncode != 0:
        raise GitError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def find_repo_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    out = run_git(["rev-parse", "--show-toplevel"], start)
    return Path(out.strip())


def resolve_branch(repo: Path, branch: str | None) -> str:
    if branch:
        return branch
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"], repo).strip()


def parse_git_datetime(value: str) -> datetime:
    # ISO-ish from %cI
    return datetime.fromisoformat(value.strip())
