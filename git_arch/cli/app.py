from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from git_arch import __version__
from git_arch.config.loader import load_config, parse_formats
from git_arch.config.schema import DEFAULT_CONFIG_YAML
from git_arch.git.parse import short_sha
from git_arch.git.repo import find_repo_root
from git_arch.pipeline.analyze import run_analyze

console = Console(force_terminal=True, emoji=False)
app = typer.Typer(
    name="git-arch",
    help="git-archaeology — 代码腐化考古 CLI",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def main_callback() -> None:
    """代码腐化考古工具。"""


@app.command("init")
def init_cmd(
    force: bool = typer.Option(False, "--force", help="覆盖已有 .git-arch.yml"),
) -> None:
    """写入默认配置文件 .git-arch.yml。"""
    root = find_repo_root()
    path = root / ".git-arch.yml"
    if path.exists() and not force:
        console.print(f"[yellow].git-arch.yml 已存在[/yellow]: {path}")
        raise typer.Exit(0)
    path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
    gitignore = root / ".gitignore"
    marker = ".git-arch/"
    if gitignore.exists():
        text = gitignore.read_text(encoding="utf-8")
        if marker not in text:
            with gitignore.open("a", encoding="utf-8") as f:
                f.write(f"\n# git-archaeology cache\n{marker}\n")
    else:
        gitignore.write_text(f"# git-archaeology cache\n{marker}\n", encoding="utf-8")
    console.print(f"[green]已写入[/green] {path}")


@app.command("analyze")
def analyze_cmd(
    path: str | None = typer.Option(None, "--path", help="限定分析路径"),
    since: str | None = typer.Option(None, "--since", help="起始时间"),
    until: str | None = typer.Option(None, "--until", help="结束时间"),
    branch: str | None = typer.Option(None, "--branch", help="分支（默认当前）"),
    max_commits: int | None = typer.Option(None, "--max-commits", help="最大 commit 数"),
    metrics: str | None = typer.Option(
        None,
        "--metrics",
        help="启用指标，逗号分隔：complexity,churn_complexity,ownership_fragmentation",
    ),
    sensitivity: str = typer.Option("medium", "--sensitivity", help="low|medium|high"),
    format: str = typer.Option("both", "--format", help="md|html|json|both|md,html"),
    output: str = typer.Option("archaeology-report", "--output", "-o", help="输出路径或基名"),
    incremental: bool = typer.Option(False, "--incremental", help="增量分析"),
    no_cache: bool = typer.Option(False, "--no-cache", help="禁用缓存"),
    show_authors: bool = typer.Option(False, "--show-authors", help="显示真实作者"),
    repo: str | None = typer.Option(None, "--repo", help="Git 仓库路径（默认当前目录）"),
    ci: bool = typer.Option(False, "--ci", help="CI 模式（M2 预留）"),
    fail_on: str | None = typer.Option(None, "--fail-on", help="high|medium（M2）"),
) -> None:
    """对仓库执行腐化考古分析并生成报告。"""
    if sensitivity not in {"low", "medium", "high"}:
        console.print("[red]sensitivity 必须是 low|medium|high[/red]")
        raise typer.Exit(2)

    formats = parse_formats(format)
    start = Path(repo).resolve() if repo else None
    root = find_repo_root(start)
    cfg = load_config(
        root,
        {
            "sensitivity": sensitivity,
            "metrics": metrics,
            "show_authors": show_authors,
            "formats": formats,
            "output": output,
            "no_cache": no_cache,
        },
    )

    if not ci:
        console.print("[bold]考古中...[/bold]")

    try:
        report, written = run_analyze(
            path=path,
            since=since,
            until=until,
            branch=branch,
            max_commits=max_commits,
            incremental=incremental,
            cfg=cfg,
            cwd=root,
        )
    except Exception as exc:
        console.print(f"[red]执行错误:[/red] {exc}")
        raise typer.Exit(2) from exc

    if not ci:
        console.print(
            f"分析 {report.meta['commit_count']:,} commits / "
            f"{report.meta['file_count']:,} files"
        )
        console.print(f"检测到 {report.meta['event_count']} 个腐化拐点")
        if report.hotspots:
            h = report.hotspots[0]
            cx = h.current_metrics.get("complexity", 0)
            console.print(f"Top 热点: {h.path} (复杂度 {cx:.1f})")
        console.print()
        for w in written:
            console.print(f"[green]报告已生成:[/green] {w}")
        console.print("   运行 `git-arch explain <commit>` 查看单个拐点详情")
    else:
        # structured one-liner
        console.print(
            {
                "events": report.meta["event_count"],
                "files": report.meta["file_count"],
                "outputs": [str(w) for w in written],
            }
        )

    if fail_on:
        rank = {"low": 1, "medium": 2, "high": 3}
        threshold = rank.get(fail_on, 3)
        if any(rank.get(e.severity, 0) >= threshold for e in report.events):
            raise typer.Exit(1)


@app.command("explain")
def explain_cmd(commit: str = typer.Argument(..., help="commit sha（可短 hash）")) -> None:
    """解释某个腐化拐点（基于最近一次报告 JSON，若无则提示先 analyze）。"""
    root = find_repo_root()
    json_path = root / "archaeology-report.json"
    if not json_path.is_file():
        # try analyze with json only quickly? prompt user
        console.print(
            "[yellow]未找到 archaeology-report.json。[/yellow]\n"
            "请先运行: git-arch analyze --format json"
        )
        raise typer.Exit(2)

    import json
    from datetime import datetime

    data = json.loads(json_path.read_text(encoding="utf-8"))
    needle = commit.lower()
    matches = [
        e
        for e in data.get("events", [])
        if e.get("commit_sha", "").lower().startswith(needle)
    ]
    if not matches:
        console.print(f"[red]未找到与 {commit} 相关的腐化事件[/red]")
        raise typer.Exit(1)
    for e in matches:
        console.print(
            f"[bold]{e.get('timestamp')}[/bold] `{short_sha(e['commit_sha'])}` "
            f"[{e.get('severity')}] {e.get('author_name') or ''}"
        )
        console.print(f"类型: {e.get('hypothesis_label')}")
        for cp in e.get("change_points", []):
            console.print(
                f"  - {cp['metric']} @ {cp['entity_id']}: "
                f"{cp['before_value']:.2f} → {cp['after_value']:.2f}"
            )


@app.command("hotspots")
def hotspots_cmd(
    path: str | None = typer.Option(None, "--path"),
    max_commits: int | None = typer.Option(None, "--max-commits"),
) -> None:
    """只列出热点文件（会跑分析，报告仍按配置写出）。"""
    root = find_repo_root()
    cfg = load_config(root, {"formats": ["json"], "output": "archaeology-report"})
    report, _ = run_analyze(path=path, max_commits=max_commits, cfg=cfg, cwd=root)
    for i, h in enumerate(report.hotspots, 1):
        console.print(
            f"{i}. {h.path}  "
            f"cx={h.current_metrics.get('complexity', 0):.1f}  "
            f"churn×cx={h.current_metrics.get('churn_complexity', 0):.1f}  "
            f"own={h.current_metrics.get('ownership_fragmentation', 0):.2f}"
        )


@app.command("timeline")
def timeline_cmd() -> None:
    """打印最近报告中的拐点时间线。"""
    root = find_repo_root()
    json_path = root / "archaeology-report.json"
    if not json_path.is_file():
        console.print("请先运行: git-arch analyze --format json,md,html")
        raise typer.Exit(2)
    import json

    data = json.loads(json_path.read_text(encoding="utf-8"))
    for e in data.get("events", []):
        console.print(
            f"{e.get('timestamp', '')[:10]}  {short_sha(e['commit_sha'])}  "
            f"[{e.get('severity')}]  {e.get('hypothesis_label')}"
        )


@app.command("version")
def version_cmd() -> None:
    console.print(__version__)


# Typer object used as console script; also support `python -m git_arch`
# setuptools expects a callable — Typer is callable.
def _entry() -> None:
    app()


# For `[project.scripts] git-arch = git_arch.cli.app:app` — Typer apps are callable.
# Some setuptools versions need a function; expose both.
if __name__ != "__main__":
    pass
else:
    app()
