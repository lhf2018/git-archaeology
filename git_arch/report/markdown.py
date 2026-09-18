from __future__ import annotations

from pathlib import Path

from jinja2 import BaseLoader, Environment

from git_arch.models import ArchaeologyReport
from git_arch.report.classify import build_class_view, build_view


MD_TEMPLATE = """\
# 代码腐化考古报告

- 仓库 `{{ meta.repo }}` · 分支 `{{ meta.branch }}` · {{ meta.commit_count }} commits · {{ meta.file_count }} files · {{ meta.event_count }} 个拐点 · {{ meta.elapsed_sec }}s

## 多类演化

同一次提交里，**两个及以上类**的圈复杂度一起变化。类名来自方法所属类型（`Class::method`）。

共 {{ class_view.multi_total }} 次，下面列出类数最多的 {{ class_view.multi|length }} 次。

{% for m in class_view.multi %}
### {{ m.date }} `{{ m.sha }}` · {{ m.author }} · {{ m.class_count }} 个类

{{ m.message }}

区域：{{ m.areas | join("、") }}

| 类 | 文件 | 语言 | 方法数 | 变化前 | 变化后 | 幅度 |
|---|---|---|---:|---:|---:|---|
{% for c in m.classes -%}
| `{{ c.name }}` | `{{ c.file }}` | {{ c.lang }} | {{ c.methods }} | {{ c.before }} | {{ c.after }} | {{ c.pct }} |
{% endfor %}
{% endfor %}

## 单类演化

每个类自己的复杂度曲线。共 {{ class_view.single_total }} 个有变化的类，下面是变化幅度最大的 {{ class_view.single|length }} 个。

| 类 | 区域 | 文件 | 语言 | 方法数 | 起点 | 现在 | 曲线 | 最大跳变 | 提交人 |
|---|---|---|---|---:|---:|---:|---|---|---|
{% for s in class_view.single -%}
| `{{ s.name }}` | `{{ s.area }}` | `{{ s.file }}` | {{ s.lang }} | {{ s.methods }} | {{ s.start }} | {{ s.end }} | `{{ s.spark }}` | {{ s.jump_date }} `{{ s.jump_sha }}` | {{ s.author }} |
{% endfor %}

## 代码区域

腐化按**仓库顶层模块**分类。下表只列源码文件上的指标跳变，不含目录聚合。

| 代码区域 | 严重度 | 变化数 | 文件数 | 主要类型 | 代表文件 | 变化过程 |
|---|---|---:|---:|---|---|---|
{% for a in areas -%}
| `{{ a.name }}` | {{ a.severity }} | {{ a.change_count }} | {{ a.file_count }} | {{ a.primary_kind }} | `{{ a.top_file }}` | `{{ a.spark }}` |
{% endfor %}

{% for a in areas %}
## {{ a.name }}

<span>严重度 {{ a.severity }} · 类型 {{ a.kinds | join(" / ") }}</span>

{% if a.chart %}
复杂度曲线 · `{{ a.chart.file }}`

```
{{ a.spark }}
```
{% endif %}

| 日期 | 提交人 | 提交 | 文件 | 语言 | 类型 | 成因 | 变化前 | 变化后 | 幅度 | 动作 |
|---|---|---|---|---|---|---|---:|---:|---|---|
{% for c in a.changes -%}
| {{ c.date }} | {{ c.author }} | `{{ c.sha }}` | `{{ c.file }}` | {{ c.lang }} | {{ c.kind }} | {{ c.tag }} | {{ c.before }} | {{ c.after }} | {{ c.bar }} {{ c.pct }} | {{ c.action }} |
{% endfor %}
{% endfor %}

## 附录

- 算法 {{ appendix.algorithm }} / sensitivity={{ appendix.sensitivity }}
- 缓存 hits={{ appendix.cache_hits }} misses={{ appendix.cache_misses }}
- 类型说明：复杂度 = 圈复杂度；改动热度 = 累计改动次数 × 复杂度；所有权 = blame 熵
"""


def render_markdown(report: ArchaeologyReport) -> str:
    view = build_view(report)
    class_view = build_class_view(report)
    for area in view["areas"]:
        for change in area["changes"]:
            change["bar"] = _bar(change["before_pct"], change["after_pct"], change["up"])
    env = Environment(loader=BaseLoader(), autoescape=False)
    return env.from_string(MD_TEMPLATE).render(
        meta=report.meta,
        appendix=report.appendix,
        areas=view["areas"],
        class_view=class_view,
    )


def write_markdown(report: ArchaeologyReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")
    return path


def _bar(before_pct: int, after_pct: int, up: bool) -> str:
    width = 10
    before_n = max(1, round(before_pct / 100 * width)) if before_pct else 1
    after_n = max(1, round(after_pct / 100 * width))
    left = "░" * min(before_n, width)
    glyph = "▶" if up else "◀"
    right = ("█" if up else "▓") * min(after_n, width)
    return f"{left}{glyph}{right}"
