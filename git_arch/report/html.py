from __future__ import annotations

import json
from pathlib import Path

from git_arch.models import ArchaeologyReport
from git_arch.report.classify import build_class_view, build_view


def render_html(report: ArchaeologyReport) -> str:
    view = build_view(report)
    payload = {
        "meta": report.meta,
        "appendix": report.appendix,
        "areas": view["areas"],
        "classes": build_class_view(report),
    }
    data = json.dumps(payload, ensure_ascii=False)
    return _PAGE.replace("__DATA__", data)


def write_html(report: ArchaeologyReport, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_html(report), encoding="utf-8")
    return path


_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>代码腐化考古报告</title>
<style>
:root {
  --bg: #f4f1ea;
  --ink: #1c1917;
  --muted: #78716c;
  --card: #fffdf8;
  --line: #e6dfd4;
  --accent: #0f766e;
  --high: #b91c1c;
  --medium: #c2410c;
  --low: #78716c;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
  background: var(--bg);
  color: var(--ink);
  line-height: 1.45;
}
header, main { max-width: 1100px; margin: 0 auto; padding: 1.5rem 1.25rem; }
header { padding-bottom: 0; }
h1 { margin: 0 0 .25rem; font-size: 1.7rem; letter-spacing: -.03em; }
.sub { color: var(--muted); margin: 0; }
.chips { display: flex; gap: .45rem; flex-wrap: wrap; margin: 1rem 0; }
.chips button {
  border: 1px solid var(--line); background: var(--card); padding: .35rem .7rem; cursor: pointer;
}
.chips button.active { background: var(--ink); color: #fff; border-color: var(--ink); }
.lane-wrap, .area {
  background: var(--card); border: 1px solid var(--line); padding: 1rem; margin-bottom: 1rem;
}
h2 { margin: 0 0 .75rem; font-size: 1.05rem; }
.badge {
  display: inline-block; font-size: .72rem; letter-spacing: .03em;
  padding: .05rem .4rem; color: #fff; margin-left: .35rem; vertical-align: 1px;
}
.badge.high { background: var(--high); }
.badge.medium { background: var(--medium); }
.badge.low { background: var(--low); }
.kind {
  display: inline-block; font-size: .75rem; border: 1px solid var(--line);
  padding: 0 .35rem; margin-right: .25rem; background: #faf7f2;
}
table { width: 100%; border-collapse: collapse; font-size: .88rem; }
th, td { text-align: left; padding: .45rem .4rem; border-bottom: 1px solid var(--line); vertical-align: middle; }
th { color: var(--muted); font-weight: 600; font-size: .75rem; }
.file { font-family: ui-monospace, Consolas, monospace; font-size: .8rem; }
.meter { display: flex; align-items: center; gap: .35rem; min-width: 180px; }
.track { position: relative; flex: 1; height: 8px; background: #efeae2; }
.track i {
  position: absolute; top: 0; height: 8px; background: var(--accent);
}
.track i.down { background: var(--medium); }
.nums { font-variant-numeric: tabular-nums; white-space: nowrap; color: var(--muted); font-size: .8rem; }
.author { font-weight: 600; }
svg.chart, svg.lanes { width: 100%; display: block; background: #faf7f2; border: 1px solid var(--line); }
.chart-cap { color: var(--muted); font-size: .8rem; margin: .35rem 0 .6rem; }
.mode { display: flex; gap: .4rem; margin: .2rem 0 1rem; }
.mode button { border: 1px solid var(--line); background: var(--card); padding: .4rem .8rem; cursor: pointer; }
.mode button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.class-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: .75rem; }
.class-card, .cohort { background: var(--card); border: 1px solid var(--line); padding: .85rem 1rem; margin-bottom: .75rem; }
.class-card h3, .cohort h3 { margin: 0 0 .25rem; font-size: 1rem; }
.class-card h3 span, .cohort h3 span { color: var(--muted); font-weight: 500; font-size: .8rem; margin-left: .35rem; }
.hidden { display: none; }
@media print { .chips, .mode { display: none; } .hidden { display: block !important; } body { background: #fff; } }
</style>
</head>
<body>
<header>
  <h1>代码腐化考古报告</h1>
  <p class="sub" id="sub"></p>
  <div class="chips" id="chips"></div>
  <div class="mode" id="mode">
    <button data-mode="multi" class="active">多类演化</button>
    <button data-mode="single">单类演化</button>
    <button data-mode="module">模块</button>
  </div>
</header>
<main>
  <section id="view-multi">
    <h2>多类演化</h2>
    <p class="sub" id="multi-cap"></p>
    <div id="multi"></div>
  </section>
  <section id="view-single" class="hidden">
    <h2>单类演化</h2>
    <p class="sub" id="single-cap"></p>
    <div class="class-grid" id="single"></div>
  </section>
  <section id="view-module" class="hidden">
  <section class="lane-wrap">
    <h2>变化过程</h2>
    <svg class="lanes" id="lanes" viewBox="0 0 1000 320"></svg>
  </section>
  <div id="areas"></div>
  </section>
</main>
<script>
const DATA = __DATA__;
const sevRank = {high:3, medium:2, low:1};

function el(tag, attrs, kids) {
  const n = document.createElement(tag);
  Object.entries(attrs || {}).forEach(([k,v]) => {
    if (k === 'className') n.className = v;
    else if (k === 'text') n.textContent = v;
    else if (k === 'html') n.innerHTML = v;
    else n.setAttribute(k, v);
  });
  (kids || []).forEach(c => n.appendChild(c));
  return n;
}
function ns(name, attrs) {
  const n = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.entries(attrs).forEach(([k,v]) => n.setAttribute(k, v));
  return n;
}
function lineChart(svg, values) {
  svg.setAttribute('viewBox', '0 0 640 120');
  svg.replaceChildren();
  if (!values || values.length < 2) return;
  const w=640, h=120, pad=10;
  const min = Math.min(...values), max = Math.max(...values);
  const span = Math.max(max-min, 1e-6);
  const pts = values.map((v,i) => {
    const x = pad + (i / (values.length-1)) * (w-2*pad);
    const y = h-pad - ((v-min)/span) * (h-2*pad);
    return [x,y];
  });
  svg.appendChild(ns('polyline', {
    fill:'none', stroke:'#0f766e', 'stroke-width':'2',
    points: pts.map(p => p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')
  }));
  const last = pts[pts.length-1];
  svg.appendChild(ns('circle', {cx:last[0], cy:last[1], r:3.5, fill:'#b91c1c'}));
}
function swimlane() {
  const areas = DATA.areas;
  const svg = document.getElementById('lanes');
  const dates = [...new Set(areas.flatMap(a => a.changes.map(c => c.date)))].sort();
  const rowH = 28;
  const h = Math.max(80, areas.length * rowH + 36);
  svg.setAttribute('viewBox', `0 0 1000 ${h}`);
  svg.replaceChildren();
  if (!dates.length || !areas.length) return;
  const left = 180, right = 980;
  const xOf = (d) => {
    if (dates.length === 1) return (left+right)/2;
    const i = dates.indexOf(d);
    return left + (i / (dates.length-1)) * (right-left);
  };
  dates.forEach((d, i) => {
    if (i % Math.ceil(dates.length/6) !== 0 && i !== dates.length-1) return;
    const x = xOf(d);
    svg.appendChild(ns('text', {x, y:16, 'font-size':11, fill:'#78716c', 'text-anchor':'middle'})).textContent = d.slice(5);
  });
  areas.forEach((a, idx) => {
    const y = 32 + idx * rowH;
    svg.appendChild(ns('text', {x:8, y:y+4, 'font-size':12, fill:'#1c1917'})).textContent = a.name;
    svg.appendChild(ns('line', {x1:left, x2:right, y1:y, y2:y, stroke:'#e6dfd4'}));
    a.changes.forEach(c => {
      const color = c.severity === 'high' ? '#b91c1c' : c.severity === 'medium' ? '#c2410c' : '#0f766e';
      const dot = ns('circle', {cx:xOf(c.date), cy:y, r: c.severity==='high'?5:3.5, fill:color});
      const title = ns('title', {});
      title.textContent = `${c.date} ${c.author} ${c.file} ${c.kind} ${c.before}→${c.after}`;
      dot.appendChild(title);
      svg.appendChild(dot);
    });
  });
}
function meter(c) {
  const wrap = el('div', {className:'meter'});
  wrap.appendChild(el('span', {className:'nums', text:c.before}));
  const track = el('span', {className:'track'});
  const width = Math.max(8, c.up ? c.after_pct : c.before_pct);
  const bar = document.createElement('i');
  bar.style.width = width + '%';
  if (!c.up) bar.className = 'down';
  track.appendChild(bar);
  wrap.appendChild(track);
  wrap.appendChild(el('span', {className:'nums', text: c.after + '  ' + c.pct}));
  return wrap;
}
function render(filter) {
  const m = DATA.meta;
  document.getElementById('sub').textContent =
    `${m.repo} · ${m.branch} · ${m.commit_count} commits · ${m.file_count} files · ${m.event_count} 拐点`;
  const chips = document.getElementById('chips');
  chips.replaceChildren();
  const names = ['全部', ...DATA.areas.map(a => a.name)];
  names.forEach(name => {
    const b = el('button', {text: name, className: (filter===name || (filter==null && name==='全部')) ? 'active' : ''});
    b.onclick = () => render(name === '全部' ? null : name);
    chips.appendChild(b);
  });
  const host = document.getElementById('areas');
  host.replaceChildren();
  DATA.areas.filter(a => !filter || a.name === filter).forEach(a => {
    const box = el('section', {className:'area', id:'area-'+a.name});
    const title = el('h2');
    title.appendChild(document.createTextNode(a.name));
    title.appendChild(el('span', {className:'badge '+a.severity, text:a.severity}));
    a.kinds.forEach(k => title.appendChild(el('span', {className:'kind', text:k})));
    box.appendChild(title);
    if (a.chart) {
      const svg = el('svg', {className:'chart'});
      box.appendChild(svg);
      lineChart(svg, a.chart.values);
      box.appendChild(el('div', {className:'chart-cap', text:'复杂度 · ' + a.chart.file}));
    }
    const table = el('table');
    const head = el('tr');
    ['日期','提交人','提交','文件','语言','类型','成因','变化过程','动作'].forEach(h => head.appendChild(el('th', {text:h})));
    table.appendChild(el('thead', {}, [head]));
    const tb = el('tbody');
    a.changes.forEach(c => {
      const tr = el('tr');
      tr.appendChild(el('td', {text:c.date}));
      tr.appendChild(el('td', {className:'author', text:c.author}));
      tr.appendChild(el('td', {className:'file', text:c.sha, title:c.message}));
      tr.appendChild(el('td', {className:'file', text:c.file, title:c.path}));
      tr.appendChild(el('td', {text:c.lang}));
      tr.appendChild(el('td', {}, [el('span', {className:'kind', text:c.kind})]));
      tr.appendChild(el('td', {text:c.tag}));
      const td = el('td');
      td.appendChild(meter(c));
      tr.appendChild(td);
      tr.appendChild(el('td', {text:c.action}));
      tb.appendChild(tr);
    });
    table.appendChild(tb);
    box.appendChild(table);
    host.appendChild(box);
  });
}
swimlane();
render(null);
renderClasses();
document.getElementById('mode').addEventListener('click', (ev) => {
  const btn = ev.target.closest('button');
  if (!btn) return;
  [...ev.currentTarget.querySelectorAll('button')].forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const mode = btn.dataset.mode;
  document.getElementById('view-multi').classList.toggle('hidden', mode !== 'multi');
  document.getElementById('view-single').classList.toggle('hidden', mode !== 'single');
  document.getElementById('view-module').classList.toggle('hidden', mode !== 'module');
});
function renderClasses() {
  const data = DATA.classes || {multi:[], single:[], multi_total:0, single_total:0};
  document.getElementById('multi-cap').textContent =
    `同一次提交里至少两个类的复杂度一起变化。共 ${data.multi_total} 次，展示类数最多的 ${data.multi.length} 次。`;
  document.getElementById('single-cap').textContent =
    `每个类自己的圈复杂度曲线。共 ${data.single_total} 个有变化的类，展示幅度最大的 ${data.single.length} 个。`;
  const multi = document.getElementById('multi');
  data.multi.forEach(m => {
    const box = el('article', {className:'cohort'});
    const h = el('h3');
    h.appendChild(document.createTextNode(`${m.date}  ${m.sha}`));
    h.appendChild(el('span', {text: `${m.author} · ${m.class_count} 个类 · ${m.areas.join(' / ')}`}));
    box.appendChild(h);
    if (m.message) box.appendChild(el('div', {className:'chart-cap', text:m.message}));
    const table = el('table');
    const head = el('tr');
    ['类','文件','语言','方法','变化过程'].forEach(x => head.appendChild(el('th', {text:x})));
    table.appendChild(el('thead', {}, [head]));
    const tb = el('tbody');
    m.classes.forEach(c => {
      const tr = el('tr');
      tr.appendChild(el('td', {className:'file', text:c.name, title:c.path}));
      tr.appendChild(el('td', {className:'file', text:c.file}));
      tr.appendChild(el('td', {text:c.lang}));
      tr.appendChild(el('td', {text:String(c.methods)}));
      const td = el('td');
      td.appendChild(meter(c));
      tr.appendChild(td);
      tb.appendChild(tr);
    });
    table.appendChild(tb);
    box.appendChild(table);
    multi.appendChild(box);
  });
  const single = document.getElementById('single');
  data.single.forEach(s => {
    const box = el('article', {className:'class-card'});
    const h = el('h3');
    h.appendChild(document.createTextNode(s.name));
    h.appendChild(el('span', {text:s.lang}));
    box.appendChild(h);
    box.appendChild(el('div', {className:'chart-cap', text:`${s.area} · ${s.file} · ${s.methods} 方法`}));
    const svg = el('svg', {className:'chart'});
    box.appendChild(svg);
    lineChart(svg, s.chart.values);
    box.appendChild(el('div', {className:'nums', text:`${s.start} → ${s.end}    最大跳变 ${s.jump_date} ${s.author}`}));
    single.appendChild(box);
  });
}
</script>
</body>
</html>
"""
