from __future__ import annotations

import fnmatch
import re
from pathlib import Path, PurePosixPath

from git_arch.git.repo import parse_git_datetime, run_git
from git_arch.models import CommitRef, FileRevision, HistoryGraph

SUPPORTED_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx", ".java"}


def is_ignored(path: str, patterns: list[str]) -> bool:
    posix = path.replace("\\", "/")
    name = PurePosixPath(posix).name
    for pat in patterns:
        pat = pat.replace("\\", "/")
        if fnmatch.fnmatch(posix, pat) or fnmatch.fnmatch(name, pat):
            return True
    return False


def list_head_files(repo: Path, path_filter: str | None, ignore: list[str]) -> list[str]:
    args = ["ls-tree", "-r", "--name-only", "HEAD"]
    out = run_git(args, repo)
    files: list[str] = []
    pf = path_filter.replace("\\", "/").rstrip("/") if path_filter else None
    for line in out.splitlines():
        p = line.strip().replace("\\", "/")
        if not p:
            continue
        if PurePosixPath(p).suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if is_ignored(p, ignore):
            continue
        if pf and not (p == pf or p.startswith(pf + "/")):
            continue
        files.append(p)
    return files


def build_history_graph(
    repo: Path,
    *,
    branch: str,
    path_filter: str | None,
    since: str | None,
    until: str | None,
    max_commits: int | None,
    ignore: list[str],
) -> HistoryGraph:
    head_files = list_head_files(repo, path_filter, ignore)
    commit_map: dict[str, CommitRef] = {}
    files: dict[str, list[FileRevision]] = {}

    for path in head_files:
        revs = _file_revisions(repo, path, branch, since, until)
        if not revs:
            continue
        files[path] = revs
        for rev in revs:
            if rev.commit_sha not in commit_map:
                meta = _commit_meta(repo, rev.commit_sha)
                if meta:
                    commit_map[rev.commit_sha] = meta

    commits = sorted(commit_map.values(), key=lambda c: (c.timestamp, c.sha))
    truncated = False
    if max_commits and len(commits) > max_commits:
        truncated = True
        keep = {c.sha for c in commits[-max_commits:]}
        commits = [c for c in commits if c.sha in keep]
        for path, revs in list(files.items()):
            files[path] = [r for r in revs if r.commit_sha in keep]
            if not files[path]:
                del files[path]

    return HistoryGraph(
        commits=commits,
        files=files,
        path_filter=path_filter,
        branch=branch,
        truncated=truncated,
    )


def _file_revisions(
    repo: Path,
    path: str,
    branch: str,
    since: str | None,
    until: str | None,
) -> list[FileRevision]:
    args = ["log", branch, "--follow", "--diff-filter=ACMR", "--numstat", "--pretty=format:COMMIT %H"]
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    args.extend(["--", path])

    out = run_git(args, repo, check=False)
    if not out.strip():
        return []

    # First pass: shas in newest-first order with line stats keyed by historical path
    entries: list[tuple[str, str, int, int]] = []  # sha, hist_path, add, del
    current_sha: str | None = None
    for line in out.splitlines():
        if line.startswith("COMMIT "):
            current_sha = line.split(" ", 1)[1].strip()
            continue
        if not line.strip() or current_sha is None:
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added_s, deleted_s, file_path = parts[0], parts[1], parts[2]
        hist_path = _normalize_numstat_path(file_path)
        try:
            added = int(added_s) if added_s != "-" else 0
            deleted = int(deleted_s) if deleted_s != "-" else 0
        except ValueError:
            added, deleted = 0, 0
        entries.append((current_sha, hist_path, added, deleted))

    entries.reverse()  # chronological
    revs: list[FileRevision] = []
    for sha, hist_path, added, deleted in entries:
        blob = _blob_hash(repo, sha, hist_path) or _blob_hash(repo, sha, path)
        if not blob:
            continue
        revs.append(
            FileRevision(
                path=path,
                blob_hash=blob,
                commit_sha=sha,
                lines_added=added,
                lines_deleted=deleted,
            )
        )
    return revs


_BLOB_RE = re.compile(r"^[0-9a-fA-F]{40,64}$")


def _collapse_slashes(path: str) -> str:
    path = path.replace("\\", "/")
    while "//" in path:
        path = path.replace("//", "/")
    return path


def _normalize_numstat_path(file_path: str) -> str:
    """Resolve git numstat rename syntax, including `{mix => }` (directory removed)."""
    file_path = file_path.strip()
    if "=>" in file_path and "{" in file_path and "}" in file_path:
        m = re.match(r"^(.*)\{(.*?) => (.*?)\}(.*)$", file_path)
        if m:
            file_path = f"{m.group(1)}{m.group(3)}{m.group(4)}"
        else:
            file_path = file_path.split("=>")[-1].strip()
    elif "=>" in file_path:
        file_path = file_path.split("=>")[-1].strip()
    return _collapse_slashes(file_path)


def _blob_hash(repo: Path, commit: str, path: str) -> str | None:
    path = _collapse_slashes(path)
    proc_out = run_git(["rev-parse", f"{commit}:{path}"], repo, check=False).strip()
    if not _BLOB_RE.match(proc_out):
        return None
    return proc_out


def _commit_meta(repo: Path, sha: str) -> CommitRef | None:
    fmt = "%H%x00%cI%x00%s%x00%an%x00%ae%x00%P"
    out = run_git(["show", "-s", f"--format={fmt}", sha], repo, check=False).strip()
    if not out:
        return None
    parts = out.split("\x00")
    if len(parts) < 6:
        return None
    parents = [p for p in parts[5].split() if p]
    return CommitRef(
        sha=parts[0],
        timestamp=parse_git_datetime(parts[1]),
        message=parts[2],
        author_name=parts[3],
        author_email=parts[4],
        parents=parents,
        is_merge=len(parents) > 1,
    )


def show_blob(repo: Path, blob_hash: str) -> str:
    if not _BLOB_RE.match(blob_hash or ""):
        return ""
    return run_git(["cat-file", "-p", blob_hash], repo, check=False)
