from __future__ import annotations

import json
from pathlib import Path

from git_arch.models import ArchaeologyReport
from git_arch.report.classify import build_class_view, build_summary, build_view


def render_html(report: ArchaeologyReport) -> str:
    view = build_view(report)
    classes = build_class_view(report)
    payload = {
        "meta": report.meta,
        "appendix": report.appendix,
        "areas": view["areas"],
        "classes": classes,
        "summary": build_summary(report, view["areas"], classes),
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
  --bg: #f3f0e8;
  --ink: #1c1917;
  --muted: #78716c;
  --card: #fffdf8;
  --line: #e4ddd2;
  --accent: #0f766e;
  --accent-soft: #ccfbf1;
  --high: #b91c1c;
  --high-soft: #fee2e2;
  --medium: #c2410c;
  --medium-soft: #ffedd5;
  --low: #78716c;
  --low-soft: #f5f5f4;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: "Segoe UI", "PingFang SC", "Noto Sans SC", sans-serif;
  background:
    radial-gradient(ellipse 70% 40% at 0% 0%, #d9f3ef55, transparent 55%),
    radial-gradient(ellipse 50% 30% at 100% 0%, #fde68a33, transparent 50%),
    var(--bg);
  color: var(--ink);
  line-height: 1.45;
}
.wrap { max-width: 1120px; margin: 0 auto; padding: 1.4rem 1.2rem 3rem; }
h1 { margin: 0 0 .2rem; font-size: clamp(1.55rem, 3vw, 2rem); letter-spacing: -.03em; }
.sub { color: var(--muted); margin: 0; font-size: .92rem; }
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: .65rem;
  margin: 1.1rem 0;
}
.stat {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: .75rem .9rem;
}
.stat b { display: block; font-size: 1.45rem; font-variant-numeric: tabular-nums; letter-spacing: -.02em; }
.stat span { color: var(--muted); font-size: .78rem; }
.stat.high b { color: var(--high); }
.stat.medium b { color: var(--medium); }
.panel {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 1rem 1.05rem;
  margin-bottom: .85rem;
}
.panel h2, .section-head {
  margin: 0 0 .65rem;
  font-size: 1.02rem;
  display: flex;
  align-items: center;
  gap: .45rem;
  flex-wrap: wrap;
}
.conclusions { margin: 0; padding-left: 1.15rem; }
.conclusions li { margin: .3rem 0; }
.actions { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .75rem; }
.pill {
  display: inline-block;
  font-size: .78rem;
  border: 1px solid var(--line);
  background: #faf7f2;
  padding: .2rem .55rem;
  border-radius: 999px;
}
.nav {
  display: flex;
  gap: .4rem;
  flex-wrap: wrap;
  margin: 1rem 0 .75rem;
  position: sticky;
  top: 0;
  z-index: 5;
  padding: .45rem 0;
  background: color-mix(in srgb, var(--bg) 88%, transparent);
  backdrop-filter: blur(6px);
}
.nav button, .filters button, .more-btn {
  border: 1px solid var(--line);
  background: var(--card);
  padding: .4rem .8rem;
  cursor: pointer;
  border-radius: 4px;
  font: inherit;
}
.nav button.active { background: var(--accent); color: #fff; border-color: var(--accent); }
.filters {
  display: flex;
  gap: .45rem;
  flex-wrap: wrap;
  align-items: center;
  margin: 0 0 .85rem;
}
.filters input, .filters select {
  border: 1px solid var(--line);
  background: var(--card);
  padding: .38rem .55rem;
  border-radius: 4px;
  font: inherit;
  min-width: 140px;
}
.filters button.active { background: var(--ink); color: #fff; border-color: var(--ink); }
.badge {
  display: inline-block;
  font-size: .72rem;
  letter-spacing: .03em;
  padding: .08rem .42rem;
  color: #fff;
  border-radius: 3px;
  text-transform: uppercase;
}
.badge.high { background: var(--high); }
.badge.medium { background: var(--medium); }
.badge.low { background: var(--low); }
.kind, .tag-action {
  display: inline-block;
  font-size: .75rem;
  border: 1px solid var(--line);
  padding: .05rem .4rem;
  margin-right: .2rem;
  background: #faf7f2;
  border-radius: 3px;
}
.tag-action { background: var(--accent-soft); border-color: #99f6e4; color: #115e59; }
table { width: 100%; border-collapse: collapse; font-size: .86rem; }
th, td { text-align: left; padding: .42rem .35rem; border-bottom: 1px solid var(--line); vertical-align: middle; }
th {
  color: var(--muted);
  font-weight: 600;
  font-size: .74rem;
  position: sticky;
  top: 48px;
  background: var(--card);
  z-index: 2;
}
.file { font-family: ui-monospace, Consolas, monospace; font-size: .78rem; }
.author { font-weight: 600; }
.nums { font-variant-numeric: tabular-nums; white-space: nowrap; color: var(--muted); font-size: .8rem; }
.meter {
  display: grid;
  grid-template-columns: 52px 1fr 88px;
  gap: .4rem;
  align-items: center;
  min-width: 220px;
}
.track {
  position: relative;
  height: 10px;
  background: #efeae2;
  border-radius: 999px;
  overflow: hidden;
}
.track .before-bar, .track .after-bar {
  position: absolute;
  top: 0;
  height: 100%;
  border-radius: 999px;
}
.track .before-bar { left: 0; background: #d6d3d1; opacity: .9; }
.track .after-bar { left: 0; background: var(--accent); opacity: .85; }
.track.down .after-bar { background: var(--medium); }
.cap { color: var(--muted); font-size: .82rem; margin: 0 0 .7rem; }
svg.chart, svg.lanes {
  width: 100%;
  display: block;
  background: #faf7f2;
  border: 1px solid var(--line);
  border-radius: 4px;
}
.chart-cap { color: var(--muted); font-size: .8rem; margin: .35rem 0 .55rem; }
.class-grid {
  display: flex;
  flex-direction: column;
  gap: .9rem;
}
.story {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 1rem 1.05rem 1.1rem;
}
.story.hot { border-left: 3px solid var(--high); }
.story-head {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: .6rem;
  align-items: baseline;
  margin-bottom: .55rem;
}
.story-head h3 { margin: 0; font-size: 1.12rem; }
.story-head .meta { color: var(--muted); font-size: .84rem; }
.story-delta {
  font-variant-numeric: tabular-nums;
  font-size: 1.05rem;
  font-weight: 700;
}
.story-delta.up { color: var(--high); }
.story-delta.down { color: var(--accent); }
.author-legend {
  display: flex;
  flex-wrap: wrap;
  gap: .45rem;
  margin: .35rem 0 .65rem;
}
.author-chip {
  display: inline-flex;
  align-items: center;
  gap: .35rem;
  font-size: .78rem;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: .12rem .55rem .12rem .2rem;
  background: #faf7f2;
}
.author-chip .dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  color: #fff;
  font-size: .65rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
svg.story-chart {
  width: 100%;
  height: auto;
  display: block;
  background: #faf7f2;
  border: 1px solid var(--line);
  border-radius: 6px;
}
.rail {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: .55rem;
  margin-top: .75rem;
}
.rail-step {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: .55rem .6rem;
  background: #fff;
  position: relative;
}
.rail-step::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  border-radius: 6px 0 0 6px;
  background: var(--step, var(--accent));
}
.rail-step .when { color: var(--muted); font-size: .72rem; }
.rail-step .who { font-weight: 700; font-size: .86rem; margin: .1rem 0; }
.rail-step .chg {
  font-variant-numeric: tabular-nums;
  font-size: .9rem;
  font-weight: 700;
}
.rail-step .msg { color: var(--muted); font-size: .72rem; margin-top: .2rem; }
.burst {
  display: flex;
  flex-direction: column;
  gap: .35rem;
  margin: .55rem 0 .7rem;
}
.burst-row {
  display: grid;
  grid-template-columns: minmax(90px, 160px) 1fr 64px;
  gap: .45rem;
  align-items: center;
  font-size: .8rem;
}
.burst-bar {
  height: 12px;
  background: #efeae2;
  border-radius: 999px;
  overflow: hidden;
}
.burst-bar > span {
  display: block;
  height: 100%;
  border-radius: 999px;
  background: var(--accent);
}
.cohort, .class-card, .area {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: .9rem 1rem;
  margin-bottom: .75rem;
}
.cohort.high, .area.high, .class-card.hot, .story.hot {
  border-left: 3px solid var(--high);
  background: linear-gradient(90deg, var(--high-soft), var(--card) 42%);
}
.cohort.medium, .area.medium {
  border-left: 3px solid var(--medium);
}
.cohort h3, .class-card h3, .area > h2 {
  margin: 0 0 .35rem;
  font-size: .98rem;
}
.cohort h3 span, .class-card h3 span { color: var(--muted); font-weight: 500; font-size: .78rem; margin-left: .35rem; }
.hidden { display: none !important; }
.jump-link {
  color: var(--accent);
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
  background: none;
  border: none;
  padding: 0;
  font: inherit;
}
.legend { display: flex; gap: .8rem; flex-wrap: wrap; color: var(--muted); font-size: .78rem; margin: .4rem 0 .7rem; }
.legend i {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: .25rem;
}
.top-list { margin: 0; padding-left: 1.1rem; }
.top-list li { margin: .25rem 0; }
.story-list {
  display: flex;
  flex-direction: column;
  gap: .65rem;
}
.story-card {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: .8rem;
  align-items: center;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: .85rem 1rem;
  cursor: pointer;
  transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
}
.story-card:hover, .story-card:focus-visible {
  border-color: #99f6e4;
  box-shadow: 0 8px 24px rgba(15, 118, 110, .08);
  transform: translateY(-1px);
  outline: none;
}
.story-card.hot { border-left: 3px solid var(--high); }
.story-card h3 { margin: 0 0 .2rem; font-size: 1.02rem; }
.story-card .path-preview {
  font-family: ui-monospace, Consolas, monospace;
  font-size: .72rem;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 62vw;
}
.story-card .open-hint {
  color: var(--accent);
  font-size: .78rem;
  white-space: nowrap;
}
.story-card .mini {
  width: 140px;
  height: 42px;
  display: block;
}
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(28, 25, 23, .42);
  backdrop-filter: blur(3px);
  z-index: 40;
  display: flex;
  justify-content: flex-end;
}
.drawer {
  width: min(720px, 100%);
  height: 100%;
  background: linear-gradient(180deg, #fffefb, #f7f3eb);
  border-left: 1px solid var(--line);
  box-shadow: -18px 0 50px rgba(0,0,0,.12);
  overflow: auto;
  padding: 1.15rem 1.2rem 2rem;
  animation: slideIn .22s ease;
}
@keyframes slideIn {
  from { transform: translateX(24px); opacity: .6; }
  to { transform: translateX(0); opacity: 1; }
}
.drawer-top {
  display: flex;
  justify-content: space-between;
  gap: .8rem;
  align-items: flex-start;
  margin-bottom: 1rem;
}
.drawer-top h2 {
  margin: 0 0 .35rem;
  font-size: 1.35rem;
  letter-spacing: -.02em;
}
.drawer-close {
  border: 1px solid var(--line);
  background: #fff;
  border-radius: 999px;
  width: 36px;
  height: 36px;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
}
.path-box {
  font-family: ui-monospace, Consolas, monospace;
  font-size: .78rem;
  background: #fff;
  border: 1px dashed #d6d3d1;
  border-radius: 8px;
  padding: .65rem .75rem;
  color: #44403c;
  word-break: break-all;
  margin: .55rem 0 1rem;
}
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: .55rem;
  margin-bottom: 1rem;
}
.detail-grid .cell {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: .55rem .65rem;
}
.detail-grid .cell b {
  display: block;
  font-size: 1.05rem;
  font-variant-numeric: tabular-nums;
}
.detail-grid .cell span { color: var(--muted); font-size: .72rem; }
.timeline {
  position: relative;
  margin: .4rem 0 0;
  padding-left: .2rem;
}
.timeline::before {
  content: "";
  position: absolute;
  left: 15px;
  top: 8px;
  bottom: 8px;
  width: 2px;
  background: linear-gradient(180deg, #99f6e4, #e7e5e4);
}
.tl-item {
  position: relative;
  display: grid;
  grid-template-columns: 32px 1fr;
  gap: .7rem;
  margin: 0 0 .85rem;
}
.tl-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid #fff;
  box-shadow: 0 0 0 1px var(--line);
  margin-top: .2rem;
  z-index: 1;
}
.tl-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: .7rem .8rem;
}
.tl-card .row1 {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: .4rem;
  align-items: baseline;
}
.tl-card .sha {
  font-family: ui-monospace, Consolas, monospace;
  font-size: .75rem;
  color: var(--muted);
}
.tl-card .chg {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  font-size: 1rem;
}
.tl-card .msg { margin-top: .35rem; color: #57534e; font-size: .84rem; }
@media (max-width: 720px) {
  .story-card { grid-template-columns: 1fr; }
  .story-card .mini { width: 100%; }
  .drawer { width: 100%; }
}
@media (max-width: 720px) {
  .meter { grid-template-columns: 1fr; min-width: 0; }
  table, thead, tbody, th, td, tr { display: block; }
  thead { display: none; }
  tr { border-bottom: 1px solid var(--line); padding: .45rem 0; }
  td { border: 0; padding: .15rem 0; }
  th { position: static; }
}
@media print {
  .nav, .filters, .more-btn { display: none !important; }
  body { background: #fff; }
  .cohort, .class-card, .area, .panel { break-inside: avoid; }
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>代码腐化考古报告</h1>
    <p class="sub" id="sub"></p>
  </header>

  <section class="panel" id="summary">
    <h2>摘要</h2>
    <div class="stats" id="stats"></div>
    <ol class="conclusions" id="conclusions"></ol>
    <div class="actions" id="actions"></div>
  </section>

  <nav class="nav" id="mode">
    <button data-mode="summary" class="active">摘要</button>
    <button data-mode="multi">多类演化</button>
    <button data-mode="single">单类演化</button>
    <button data-mode="module">模块</button>
  </nav>

  <section id="view-summary">
    <div class="panel">
      <h2>优先看这些</h2>
      <div id="priority"></div>
    </div>
  </section>

  <section id="view-multi" class="hidden">
    <div class="filters" id="multi-filters"></div>
    <p class="cap" id="multi-cap"></p>
    <div id="multi"></div>
  </section>

  <section id="view-single" class="hidden">
    <div class="filters" id="single-filters"></div>
    <p class="cap" id="single-cap"></p>
    <div class="class-grid" id="single"></div>
  </section>

  <section id="view-module" class="hidden">
    <div class="filters" id="module-filters"></div>
    <div class="panel">
      <h2>变化过程</h2>
      <div class="legend">
        <span><i style="background:#b91c1c"></i>high</span>
        <span><i style="background:#c2410c"></i>medium</span>
        <span><i style="background:#0f766e"></i>low</span>
      </div>
      <svg class="lanes" id="lanes" viewBox="0 0 1000 320"></svg>
    </div>
    <div id="areas"></div>
  </section>
</div>
<div id="class-drawer" class="drawer-backdrop hidden" role="dialog" aria-modal="true"></div>
<script>
const DATA = __DATA__;
const state = {
  mode: 'summary',
  multiSev: 'all',
  multiQ: '',
  singleArea: 'all',
  singleQ: '',
  moduleArea: 'all',
  moduleSev: 'all',
  moduleQ: '',
  multiShow: 5,
};

function el(tag, attrs, kids) {
  const n = document.createElement(tag);
  Object.entries(attrs || {}).forEach(([k,v]) => {
    if (k === 'className') n.className = v;
    else if (k === 'text') n.textContent = v;
    else if (k === 'html') n.innerHTML = v;
    else if (k.startsWith('on') && typeof v === 'function') n.addEventListener(k.slice(2).toLowerCase(), v);
    else n.setAttribute(k, v);
  });
  (kids || []).forEach(c => {
    if (c == null) return;
    n.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
  });
  return n;
}
function ns(name, attrs) {
  const n = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.entries(attrs || {}).forEach(([k,v]) => n.setAttribute(k, v));
  return n;
}
function setMode(mode) {
  state.mode = mode;
  ['summary','multi','single','module'].forEach(m => {
    document.getElementById('view-' + m).classList.toggle('hidden', m !== mode);
  });
  [...document.getElementById('mode').querySelectorAll('button')].forEach(b => {
    b.classList.toggle('active', b.dataset.mode === mode);
  });
  location.hash = mode === 'summary' ? '' : mode;
}
const AUTHOR_PALETTE = ['#0f766e','#b45309','#7c3aed','#be123c','#0369a1','#4d7c0f','#c2410c','#0e7490'];
function authorColor(name) {
  const s = String(name || '?');
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return AUTHOR_PALETTE[h % AUTHOR_PALETTE.length];
}
function authorInitial(name) {
  const s = String(name || '?').trim();
  return (s[0] || '?').toUpperCase();
}
function lineChart(svg, chart) {
  svg.setAttribute('viewBox', '0 0 640 140');
  svg.replaceChildren();
  const values = (chart && chart.values) || [];
  if (values.length < 2) return;
  const w=640, h=140, padL=34, padR=12, padT=14, padB=28;
  const min = Math.min(...values), max = Math.max(...values);
  const span = Math.max(max-min, 1e-6);
  const pts = values.map((v,i) => {
    const x = padL + (i / (values.length-1)) * (w-padL-padR);
    const y = padT + (1 - (v-min)/span) * (h-padT-padB);
    return [x,y,v];
  });
  [0, 0.5, 1].forEach(t => {
    const y = padT + (1-t) * (h-padT-padB);
    const val = min + span * t;
    svg.appendChild(ns('line', {x1:padL, x2:w-padR, y1:y, y2:y, stroke:'#e7e0d6', 'stroke-width':'1'}));
    svg.appendChild(ns('text', {x:4, y:y+3, 'font-size':'10', fill:'#78716c'})).textContent = Math.round(val);
  });
  svg.appendChild(ns('polyline', {
    fill:'none', stroke:'#0f766e', 'stroke-width':'2.2',
    points: pts.map(p => p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ')
  }));
  const ji = Math.min(Math.max(chart.jump_index || pts.length-1, 0), pts.length-1);
  const jump = pts[ji];
  const jumpDot = ns('circle', {cx:jump[0], cy:jump[1], r:5, fill:'#b91c1c'});
  const tip = ns('title', {});
  tip.textContent = `拐点 ${chart.jump_label || ''} ${chart.jump_sha || ''} ${chart.jump_author || ''} · ${jump[2]}`;
  jumpDot.appendChild(tip);
  svg.appendChild(jumpDot);
  const last = pts[pts.length-1];
  svg.appendChild(ns('circle', {cx:last[0], cy:last[1], r:3, fill:'#0f766e'}));
  if (chart.labels && chart.labels.length) {
    const first = chart.labels[0];
    const mid = chart.labels[Math.floor(chart.labels.length/2)];
    const end = chart.labels[chart.labels.length-1];
    [[padL, first],[ (padL+w-padR)/2, mid],[w-padR, end]].forEach(([x, lab], idx) => {
      svg.appendChild(ns('text', {
        x, y:h-8, 'font-size':'10', fill:'#78716c',
        'text-anchor': idx===0?'start':(idx===2?'end':'middle')
      })).textContent = lab;
    });
  }
}
function drawClassStory(svg, chart) {
  const points = (chart && chart.points) || [];
  const values = points.length ? points.map(p => p.value) : ((chart && chart.values) || []);
  svg.replaceChildren();
  if (values.length < 2) {
    svg.setAttribute('viewBox', '0 0 900 120');
    svg.appendChild(ns('text', {x:20, y:60, fill:'#78716c', 'font-size':'14'})).textContent = '数据点不足';
    return;
  }
  const jumps = points.filter(p => p.is_jump);
  const labelRows = Math.min(3, Math.max(1, Math.ceil(jumps.length / 6)));
  const w = 900, h = 210 + labelRows * 22;
  const padL = 44, padR = 18, padT = 28, padB = 36 + labelRows * 22;
  svg.setAttribute('viewBox', `0 0 ${w} ${h}`);
  const min = Math.min(...values), max = Math.max(...values);
  const span = Math.max(max - min, 1e-6);
  const xy = values.map((v, i) => {
    const x = padL + (i / (values.length - 1)) * (w - padL - padR);
    const y = padT + (1 - (v - min) / span) * (h - padT - padB);
    return {x, y, v, i};
  });
  // area fill
  const areaPts = [`${xy[0].x},${h-padB}`]
    .concat(xy.map(p => `${p.x},${p.y}`))
    .concat([`${xy[xy.length-1].x},${h-padB}`])
    .join(' ');
  svg.appendChild(ns('polygon', {points: areaPts, fill:'#ccfbf155', stroke:'none'}));
  [0, 0.5, 1].forEach(t => {
    const y = padT + (1 - t) * (h - padT - padB);
    svg.appendChild(ns('line', {x1:padL, x2:w-padR, y1:y, y2:y, stroke:'#e7e0d6'}));
    svg.appendChild(ns('text', {x:6, y:y+3, 'font-size':'11', fill:'#78716c'})).textContent = Math.round(min + span * t);
  });
  svg.appendChild(ns('polyline', {
    fill:'none', stroke:'#134e4a', 'stroke-width':'2.4',
    points: xy.map(p => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
  }));
  // quiet points
  xy.forEach((p, i) => {
    const src = points[i] || {};
    if (src.is_jump) return;
    svg.appendChild(ns('circle', {cx:p.x, cy:p.y, r:2.2, fill:'#a8a29e'}));
  });
  // jump markers with author color + callouts
  let callout = 0;
  xy.forEach((p, i) => {
    const src = points[i];
    if (!src || !src.is_jump) return;
    const color = authorColor(src.author);
    const prev = i > 0 ? values[i-1] : src.value;
    const delta = src.value - prev;
    svg.appendChild(ns('line', {
      x1:p.x, x2:p.x, y1:p.y, y2:h-padB+4,
      stroke:color, 'stroke-width':'1.2', 'stroke-dasharray':'3 3', opacity:'0.55'
    }));
    const dot = ns('circle', {cx:p.x, cy:p.y, r:6, fill:color, stroke:'#fff', 'stroke-width':'2'});
    const tip = ns('title', {});
    tip.textContent = `${src.date} ${src.author} ${src.sha}\n${prev} → ${src.value} (${delta>=0?'+':''}${delta.toFixed(1)})\n${src.message||''}`;
    dot.appendChild(tip);
    svg.appendChild(dot);
    const row = callout % labelRows;
    const ly = h - 12 - row * 18;
    const lx = Math.min(Math.max(p.x, padL + 8), w - padR - 8);
    svg.appendChild(ns('text', {
      x: lx, y: ly, 'font-size':'11', fill: color, 'text-anchor':'middle', 'font-weight':'700'
    })).textContent = `${authorInitial(src.author)} ${delta>=0?'+':''}${Math.round(delta)}`;
    callout += 1;
  });
  // x labels
  const first = points[0], mid = points[Math.floor(points.length/2)], end = points[points.length-1];
  [[xy[0].x, first && first.label], [xy[Math.floor(xy.length/2)].x, mid && mid.label], [xy[xy.length-1].x, end && end.label]]
    .forEach(([x, lab], idx) => {
      if (!lab) return;
      svg.appendChild(ns('text', {
        x, y: padT - 10, 'font-size':'11', fill:'#78716c',
        'text-anchor': idx===0?'start':(idx===2?'end':'middle')
      })).textContent = lab;
    });
}
function scaleRows(rows) {
  let peak = 1e-9;
  rows.forEach(r => {
    peak = Math.max(peak, Math.abs(r.before_raw||0), Math.abs(r.after_raw||0));
  });
  return peak;
}
function meter(c, peak) {
  const wrap = el('div', {className:'meter' + (c.up ? '' : ' down')});
  wrap.appendChild(el('span', {className:'nums', text:String(c.before)}));
  const track = el('span', {className:'track' + (c.up ? '' : ' down')});
  const beforePct = Math.max(4, Math.round(Math.abs(c.before_raw||0) / peak * 100));
  const afterPct = Math.max(4, Math.round(Math.abs(c.after_raw||0) / peak * 100));
  const b = el('span', {className:'before-bar'});
  b.style.width = beforePct + '%';
  const a = el('span', {className:'after-bar'});
  a.style.width = afterPct + '%';
  track.appendChild(b);
  track.appendChild(a);
  wrap.appendChild(track);
  wrap.appendChild(el('span', {className:'nums', text: `${c.after}  ${c.pct}`}));
  return wrap;
}
function matchQ(text, q) {
  if (!q) return true;
  return String(text||'').toLowerCase().includes(q.toLowerCase());
}
function renderSummary() {
  const m = DATA.meta;
  const s = DATA.summary || {};
  document.getElementById('sub').textContent =
    `${m.repo} · ${m.branch} · ${m.commit_count} commits · ${m.file_count} files · ${m.elapsed_sec}s`;
  const stats = document.getElementById('stats');
  stats.replaceChildren();
  [
    ['拐点', m.event_count, ''],
    ['high', s.high||0, 'high'],
    ['medium', s.medium||0, 'medium'],
    ['模块', s.area_count||0, ''],
    ['多类共变', s.multi_total||0, ''],
    ['变化中的类', s.single_total||0, ''],
  ].forEach(([k,v,cls]) => {
    stats.appendChild(el('div', {className:'stat ' + cls}, [
      el('b', {text:String(v)}),
      el('span', {text:k}),
    ]));
  });
  const cons = document.getElementById('conclusions');
  cons.replaceChildren();
  (s.conclusions||[]).forEach(t => cons.appendChild(el('li', {text:t})));
  const acts = document.getElementById('actions');
  acts.replaceChildren();
  (s.actions||[]).forEach(a => acts.appendChild(el('span', {className:'pill', text:a})));

  const pri = document.getElementById('priority');
  pri.replaceChildren();
  const left = el('div');
  left.appendChild(el('h3', {text:'Top 模块', style:'margin:.2rem 0 .4rem;font-size:.92rem'}));
  const ol1 = el('ol', {className:'top-list'});
  (s.top_areas||[]).forEach(a => {
    const li = el('li');
    li.appendChild(el('button', {
      className:'jump-link',
      text: a.name,
      onClick: () => { state.moduleArea = a.name; setMode('module'); renderModule(); }
    }));
    li.appendChild(document.createTextNode(` · ${a.severity} · ${a.change_count} 变化 · ${a.primary_kind}`));
    ol1.appendChild(li);
  });
  left.appendChild(ol1);
  const right = el('div');
  right.appendChild(el('h3', {text:'Top 类', style:'margin:.2rem 0 .4rem;font-size:.92rem'}));
  const ol2 = el('ol', {className:'top-list'});
  (s.top_classes||[]).forEach(c => {
    const li = el('li');
    li.appendChild(el('button', {
      className:'jump-link',
      text: c.name,
      onClick: () => openClassDetail(c.name),
    }));
    li.appendChild(document.createTextNode(` · ${c.start} → ${c.end} · ${c.area}`));
    ol2.appendChild(li);
  });
  right.appendChild(ol2);
  const grid = el('div', {style:'display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem'});
  grid.appendChild(left);
  grid.appendChild(right);
  pri.appendChild(grid);
}
function buildFilterBar(host, opts) {
  host.replaceChildren();
  if (opts.severities) {
    ['all','high','medium','low'].forEach(sev => {
      const label = sev === 'all' ? '全部严重度' : sev;
      const b = el('button', {
        text: label,
        className: opts.sevValue === sev ? 'active' : '',
        onClick: () => opts.onSev(sev),
      });
      host.appendChild(b);
    });
  }
  if (opts.areas) {
    const sel = el('select');
    [['all','全部区域'], ...opts.areas.map(a => [a,a])].forEach(([v,t]) => {
      const o = document.createElement('option');
      o.value = v; o.textContent = t;
      if (v === opts.areaValue) o.selected = true;
      sel.appendChild(o);
    });
    sel.addEventListener('change', () => opts.onArea(sel.value));
    host.appendChild(sel);
  }
  if (opts.search) {
    const input = el('input', {placeholder: opts.placeholder || '搜索…', value: opts.q || ''});
    input.addEventListener('input', () => opts.onSearch(input.value.trim()));
    host.appendChild(input);
  }
}
function renderMulti() {
  const data = DATA.classes || {multi:[], multi_total:0};
  buildFilterBar(document.getElementById('multi-filters'), {
    severities: true,
    sevValue: state.multiSev,
    onSev: (v) => { state.multiSev = v; state.multiShow = 5; renderMulti(); },
    search: true,
    q: state.multiQ,
    placeholder: '搜索类 / 作者 / 提交',
    onSearch: (v) => { state.multiQ = v; renderMulti(); },
  });
  let rows = data.multi.slice();
  if (state.multiQ) {
    rows = rows.filter(m =>
      matchQ(m.author, state.multiQ) ||
      matchQ(m.sha, state.multiQ) ||
      matchQ(m.message, state.multiQ) ||
      m.classes.some(c => matchQ(c.name, state.multiQ) || matchQ(c.file, state.multiQ))
    );
  }
  const sevOf = (m) => m.class_count >= 8 ? 'high' : (m.class_count >= 4 ? 'medium' : 'low');
  if (state.multiSev !== 'all') rows = rows.filter(m => sevOf(m) === state.multiSev);
  document.getElementById('multi-cap').textContent =
    `同一次提交里多个类一起腐化。条形长度=复杂度跳变幅度，颜色=提交人。共 ${data.multi_total} 次，当前 ${rows.length} 次。`;
  const host = document.getElementById('multi');
  host.replaceChildren();
  rows.slice(0, state.multiShow).forEach(m => {
    const sev = sevOf(m);
    const color = authorColor(m.author);
    const box = el('article', {className:'cohort ' + sev, id:'cohort-' + m.sha});
    const h = el('h3');
    h.appendChild(document.createTextNode(`${m.date}  ${m.sha}`));
    h.appendChild(el('span', {className:'badge ' + sev, text:sev}));
    box.appendChild(h);
    const who = el('div', {className:'author-legend'});
    who.appendChild(el('span', {className:'author-chip'}, [
      el('span', {className:'dot', text: authorInitial(m.author), style:`background:${color}`}),
      document.createTextNode(`${m.author} · 一次动了 ${m.class_count} 个类 · 总Δ ${m.total_delta}`),
    ]));
    box.appendChild(who);
    if (m.message) box.appendChild(el('div', {className:'chart-cap', text:m.message}));
    box.appendChild(el('div', {className:'chart-cap', text:'区域：' + m.areas.join(' / ')}));
    const burst = el('div', {className:'burst'});
    const peak = Math.max(...m.classes.map(c => Math.abs(c.after_raw - c.before_raw)), 1e-9);
    m.classes.forEach(c => {
      const delta = c.after_raw - c.before_raw;
      const row = el('div', {className:'burst-row'});
      row.appendChild(el('span', {className:'file', text:c.name, title:c.path}));
      const bar = el('div', {className:'burst-bar'});
      const fill = el('span');
      fill.style.width = Math.max(4, Math.round(Math.abs(delta) / peak * 100)) + '%';
      fill.style.background = color;
      bar.appendChild(fill);
      row.appendChild(bar);
      row.appendChild(el('span', {className:'nums', text: `${c.before}→${c.after}`}));
      burst.appendChild(row);
    });
    box.appendChild(burst);
    host.appendChild(box);
  });
  if (rows.length > state.multiShow) {
    host.appendChild(el('button', {
      className:'more-btn',
      text: `展开更多（还剩 ${rows.length - state.multiShow}）`,
      onClick: () => { state.multiShow += 5; renderMulti(); },
    }));
  }
}
function renderSingle() {
  const data = DATA.classes || {single:[], single_total:0};
  const areas = [...new Set(data.single.map(s => s.area))].sort();
  buildFilterBar(document.getElementById('single-filters'), {
    areas,
    areaValue: state.singleArea,
    onArea: (v) => { state.singleArea = v; renderSingle(); },
    search: true,
    q: state.singleQ,
    placeholder: '搜索类名 / 文件 / 作者 / 路径',
    onSearch: (v) => { state.singleQ = v; renderSingle(); },
  });
  let rows = data.single.slice();
  if (state.singleArea !== 'all') rows = rows.filter(s => s.area === state.singleArea);
  if (state.singleQ) {
    rows = rows.filter(s =>
      matchQ(s.name, state.singleQ) ||
      matchQ(s.file, state.singleQ) ||
      matchQ(s.path, state.singleQ) ||
      matchQ(s.author, state.singleQ) ||
      matchQ(s.area, state.singleQ) ||
      (s.authors||[]).some(a => matchQ(a, state.singleQ))
    );
  }
  document.getElementById('single-cap').textContent =
    `点击任意类查看完整路径与腐化时间线。共 ${data.single_total} 个类，当前 ${rows.length} 个。`;
  const host = document.getElementById('single');
  host.replaceChildren();
  host.className = 'story-list';
  rows.forEach(s => {
    const hot = Math.abs(s.delta) >= 40;
    const card = el('article', {
      className: 'story-card' + (hot ? ' hot' : ''),
      id: 'class-' + s.name,
      tabindex: '0',
      role: 'button',
      'aria-label': '打开 ' + s.name + ' 详情',
      onClick: () => openClassDetail(s.name),
      onKeydown: (ev) => {
        if (ev.key === 'Enter' || ev.key === ' ') {
          ev.preventDefault();
          openClassDetail(s.name);
        }
      },
    });
    const left = el('div');
    left.appendChild(el('h3', {text: s.name}));
    left.appendChild(el('div', {className:'path-preview', text: s.path, title: s.path}));
    left.appendChild(el('div', {className:'meta', style:'color:var(--muted);font-size:.8rem;margin-top:.25rem', text:
      `${s.area} · ${s.lang} · ${s.methods} 方法 · ${(s.authors||[s.author]).join(' / ')}`
    }));
    left.appendChild(el('div', {
      className: 'story-delta ' + (s.delta >= 0 ? 'up' : 'down'),
      style: 'margin-top:.35rem;font-size:.95rem',
      text: `${s.start} → ${s.end}（${s.delta>=0?'+':''}${s.delta}）`,
    }));
    card.appendChild(left);
    const right = el('div', {style:'text-align:right'});
    const mini = el('svg', {className:'mini'});
    right.appendChild(mini);
    drawMiniSpark(mini, s.chart);
    right.appendChild(el('div', {className:'open-hint', text:'查看详情 →'}));
    card.appendChild(right);
    host.appendChild(card);
  });
}
function drawMiniSpark(svg, chart) {
  const values = (chart && chart.values) || [];
  svg.setAttribute('viewBox', '0 0 140 42');
  svg.replaceChildren();
  if (values.length < 2) return;
  const min = Math.min(...values), max = Math.max(...values);
  const span = Math.max(max-min, 1e-6);
  const pts = values.map((v,i) => {
    const x = 4 + (i/(values.length-1))*132;
    const y = 38 - ((v-min)/span)*30;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  svg.appendChild(ns('polyline', {fill:'none', stroke:'#0f766e', 'stroke-width':'2', points:pts}));
  const ji = Math.min(chart.jump_index || values.length-1, values.length-1);
  const jx = 4 + (ji/(values.length-1))*132;
  const jy = 38 - ((values[ji]-min)/span)*30;
  svg.appendChild(ns('circle', {cx:jx, cy:jy, r:3.2, fill:'#b91c1c'}));
}
function findClass(name) {
  return ((DATA.classes && DATA.classes.single) || []).find(s => s.name === name);
}
function closeClassDetail() {
  const host = document.getElementById('class-drawer');
  host.classList.add('hidden');
  host.replaceChildren();
  document.body.style.overflow = '';
  if ((location.hash || '').startsWith('#class=')) {
    history.replaceState(null, '', '#single');
  }
}
function openClassDetail(name) {
  const s = findClass(name);
  if (!s) return;
  setMode('single');
  const host = document.getElementById('class-drawer');
  host.classList.remove('hidden');
  host.replaceChildren();
  document.body.style.overflow = 'hidden';
  location.hash = 'class=' + encodeURIComponent(s.name);

  const drawer = el('div', {className:'drawer', onClick: (ev) => ev.stopPropagation()});
  const top = el('div', {className:'drawer-top'});
  const title = el('div');
  title.appendChild(el('h2', {text: s.name}));
  title.appendChild(el('div', {className:'sub', text: `${s.area} · ${s.file} · ${s.lang}`}));
  top.appendChild(title);
  top.appendChild(el('button', {
    className:'drawer-close',
    text: '×',
    title: '关闭',
    onClick: closeClassDetail,
  }));
  drawer.appendChild(top);

  drawer.appendChild(el('div', {className:'path-box', text: s.path}));

  const grid = el('div', {className:'detail-grid'});
  [
    ['起点', s.start],
    ['现在', s.end],
    ['变化', `${s.delta>=0?'+':''}${s.delta}`],
    ['方法数', String(s.methods)],
    ['跳变次数', String((s.jumps||[]).length)],
    ['主要提交人', s.author],
  ].forEach(([k,v]) => {
    grid.appendChild(el('div', {className:'cell'}, [
      el('b', {text: v}),
      el('span', {text: k}),
    ]));
  });
  drawer.appendChild(grid);

  const legend = el('div', {className:'author-legend'});
  (s.authors || [s.author]).forEach(a => {
    const color = authorColor(a);
    legend.appendChild(el('span', {className:'author-chip'}, [
      el('span', {className:'dot', text: authorInitial(a), style:`background:${color}`}),
      document.createTextNode(a),
    ]));
  });
  drawer.appendChild(legend);

  const svg = el('svg', {className:'story-chart'});
  drawer.appendChild(svg);
  drawClassStory(svg, s.chart);
  drawer.appendChild(el('div', {
    className:'chart-cap',
    text: '完整腐化过程：曲线为复杂度，彩色圆点为提交跳变（悬停看详情）',
  }));

  drawer.appendChild(el('h3', {text:'提交时间线', style:'margin:1rem 0 .55rem;font-size:1rem'}));
  const tl = el('div', {className:'timeline'});
  (s.jumps || []).forEach(j => {
    const color = authorColor(j.author);
    const item = el('div', {className:'tl-item'});
    item.appendChild(el('div', {className:'tl-dot', style:`background:${color}`}));
    const card = el('div', {className:'tl-card'});
    const row1 = el('div', {className:'row1'});
    row1.appendChild(el('div', {className:'who', style:'font-weight:700', text: j.author}));
    row1.appendChild(el('div', {className:'sha', text: `${j.date} · ${j.sha}`}));
    card.appendChild(row1);
    card.appendChild(el('div', {className:'chg', text: `${j.before} → ${j.after}  ${j.pct}`}));
    if (j.message) card.appendChild(el('div', {className:'msg', text: j.message}));
    item.appendChild(card);
    tl.appendChild(item);
  });
  drawer.appendChild(tl);

  host.appendChild(drawer);
  host.onclick = (ev) => {
    if (ev.target === host) closeClassDetail();
  };
  const onKey = (ev) => {
    if (ev.key === 'Escape') {
      closeClassDetail();
      document.removeEventListener('keydown', onKey);
    }
  };
  document.addEventListener('keydown', onKey);
}
function swimlane(areas) {
  const svg = document.getElementById('lanes');
  const dates = [...new Set(areas.flatMap(a => a.changes.map(c => c.date)))].sort();
  const rowH = 28;
  const h = Math.max(90, areas.length * rowH + 40);
  svg.setAttribute('viewBox', `0 0 1000 ${h}`);
  svg.replaceChildren();
  if (!dates.length || !areas.length) {
    svg.appendChild(ns('text', {x:20, y:40, fill:'#78716c', 'font-size':'13'})).textContent = '当前筛选无数据';
    return;
  }
  const left = 190, right = 980;
  const xOf = (d) => dates.length === 1 ? (left+right)/2 : left + (dates.indexOf(d)/(dates.length-1))*(right-left);
  dates.forEach((d, i) => {
    if (i % Math.ceil(dates.length/6) !== 0 && i !== dates.length-1) return;
    svg.appendChild(ns('text', {x:xOf(d), y:16, 'font-size':11, fill:'#78716c', 'text-anchor':'middle'})).textContent = d.slice(5);
  });
  areas.forEach((a, idx) => {
    const y = 34 + idx * rowH;
    const label = ns('text', {x:8, y:y+4, 'font-size':12, fill:'#1c1917', cursor:'pointer'});
    label.textContent = a.name.length > 22 ? a.name.slice(0,20)+'…' : a.name;
    label.addEventListener('click', () => {
      const node = document.getElementById('area-' + a.name);
      if (node) node.scrollIntoView({behavior:'smooth', block:'start'});
    });
    svg.appendChild(label);
    svg.appendChild(ns('line', {x1:left, x2:right, y1:y, y2:y, stroke:'#e6dfd4'}));
    a.changes.forEach(c => {
      const color = c.severity === 'high' ? '#b91c1c' : c.severity === 'medium' ? '#c2410c' : '#0f766e';
      const dot = ns('circle', {
        cx:xOf(c.date), cy:y, r: c.severity==='high'?5:3.5, fill:color, cursor:'pointer'
      });
      const title = ns('title', {});
      title.textContent = `${c.date} ${c.author} ${c.file} ${c.kind} ${c.before}→${c.after}`;
      dot.appendChild(title);
      dot.addEventListener('click', () => {
        const node = document.getElementById('area-' + a.name);
        if (node) node.scrollIntoView({behavior:'smooth', block:'start'});
      });
      svg.appendChild(dot);
    });
  });
}
function renderModule() {
  const areasAll = DATA.areas || [];
  buildFilterBar(document.getElementById('module-filters'), {
    severities: true,
    sevValue: state.moduleSev,
    onSev: (v) => { state.moduleSev = v; renderModule(); },
    areas: areasAll.map(a => a.name),
    areaValue: state.moduleArea,
    onArea: (v) => { state.moduleArea = v; renderModule(); },
    search: true,
    q: state.moduleQ,
    placeholder: '搜索文件 / 作者 / 提交',
    onSearch: (v) => { state.moduleQ = v; renderModule(); },
  });
  let areas = areasAll.slice();
  if (state.moduleArea !== 'all') areas = areas.filter(a => a.name === state.moduleArea);
  if (state.moduleSev !== 'all') areas = areas.filter(a => a.severity === state.moduleSev || a.changes.some(c => c.severity === state.moduleSev));
  areas = areas.map(a => {
    let changes = a.changes;
    if (state.moduleSev !== 'all') changes = changes.filter(c => c.severity === state.moduleSev);
    if (state.moduleQ) {
      changes = changes.filter(c =>
        matchQ(c.file, state.moduleQ) ||
        matchQ(c.author, state.moduleQ) ||
        matchQ(c.sha, state.moduleQ) ||
        matchQ(c.path, state.moduleQ)
      );
    }
    return {...a, changes};
  }).filter(a => a.changes.length);
  swimlane(areas);
  const host = document.getElementById('areas');
  host.replaceChildren();
  areas.forEach(a => {
    const box = el('section', {className:'area ' + a.severity, id:'area-' + a.name});
    const title = el('h2');
    title.appendChild(document.createTextNode(a.name));
    title.appendChild(el('span', {className:'badge ' + a.severity, text:a.severity}));
    a.kinds.forEach(k => title.appendChild(el('span', {className:'kind', text:k})));
    box.appendChild(title);
    if (a.chart) {
      const svg = el('svg', {className:'chart'});
      box.appendChild(svg);
      lineChart(svg, a.chart);
      box.appendChild(el('div', {className:'chart-cap', text:'复杂度 · ' + a.chart.file + '（红点为最大跳变）'}));
    }
    const table = el('table');
    const head = el('tr');
    ['日期','提交人','提交','文件','语言','类型','成因','变化过程','动作'].forEach(h => head.appendChild(el('th', {text:h})));
    table.appendChild(el('thead', {}, [head]));
    const tb = el('tbody');
    const peak = scaleRows(a.changes);
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
      td.appendChild(meter(c, peak));
      tr.appendChild(td);
      tr.appendChild(el('td', {}, [el('span', {className:'tag-action', text:c.action})]));
      tb.appendChild(tr);
    });
    table.appendChild(tb);
    box.appendChild(table);
    host.appendChild(box);
  });
}
function boot() {
  renderSummary();
  renderMulti();
  renderSingle();
  renderModule();
  document.getElementById('mode').addEventListener('click', (ev) => {
    const btn = ev.target.closest('button');
    if (!btn) return;
    closeClassDetail();
    setMode(btn.dataset.mode);
  });
  const raw = (location.hash || '').replace(/^#/, '');
  if (raw.startsWith('class=')) {
    const name = decodeURIComponent(raw.slice(6));
    setMode('single');
    openClassDetail(name);
  } else if (['multi','single','module'].includes(raw)) {
    setMode(raw);
  } else {
    setMode('summary');
  }
}
boot();
</script>
</body>
</html>
"""
