from __future__ import annotations

from collections import Counter
from pathlib import Path

from git_arch.git.repo import run_git


def blame_author_counts(repo: Path, commit: str, path: str) -> dict[str, int]:
    """Return author email -> line count for path at commit."""
    out = run_git(
        ["blame", "--line-porcelain", commit, "--", path],
        repo,
        check=False,
    )
    if not out.strip():
        return {}
    counts: Counter[str] = Counter()
    current_author = "unknown"
    for line in out.splitlines():
        if line.startswith("author-mail "):
            mail = line[len("author-mail ") :].strip().strip("<>")
            current_author = mail or "unknown"
        elif line.startswith("\t"):
            counts[current_author] += 1
    return dict(counts)
