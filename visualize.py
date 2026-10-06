#!/usr/bin/env python3
"""
Renders groups.json as a self-contained, offline HTML node-link diagram:
nodes are clusters of your own photos sharing a colour theme (square thumbnail
tiles packed into the node, sized by how well each photo matches the group's
colour), edges connect perceptually similar groups. Click a node to zoom into
a full grid of every photo in that group. No network dependency — everything
(including thumbnails) is inlined, since these are personal photos and the
file should stay local.
"""
import json
import sys
from pathlib import Path

TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Colour Map — __TOTAL__ photos, __GROUPS__ groups</title>
<style>
  /* subset to printable Basic Latin (U+0020–007E) — the only characters any
     node label needs (hex codes, city names, digits) — from
     DotGothic16-Regular.ttf (desktop ~/Desktop/DotGothic16), cut down from
     ~2MB to ~3KB with pyftsubset so it's cheap to inline here */
  @font-face {
    font-family: 'DotGothic16';
    src: url(data:font/woff2;base64,d09GMgABAAAAAAuoABAAAAAAItAAAAtOAAEZmgAAAAAAAAAAAAAAAAAAAAAAAAAAGYFWGyAcIAZgAFIRCAq2BKsjATYCJAOBRAuBQgAEIAWDYAcgFyQYgUIblhtRlHDWDkVRJiVR8WWBHQzHbwiVOCOCptmWIKxWcVUjYc+wr69iI9KmEmkT4nSMxHMhKt3n98zOk3WzqzPJrDozhgD4TDJzhjlgCJikzoBC+hARVk6gnz+W71+3dfQ6CU5wUTSRA5vA/E/VEsvOLjq32x0vC9LuznDew13+QHdF5TZEaOUI0M5UU7m8EOmVIyA5U1XpLDkk0j4i3bynjgbjkJ54xJZsjdgKTs7//tZPGG3WnMkC3RbBjZow4AAbj5rwgbRsIOn/l958zf/eU4Oow/5vrvdtpgCo0LdCAkoUioTO3pnsfTP3ZSltCrMF5NDpyabMDlhIxE0VkdA9NQKd/U5920xEu9XuEYiIE3OVEEKf+zxnNjQb8j+Q1lwxkrEOr4msI+WnQ4Ccg2ZwZAsXFxqguufOD8HznF0egOfdc7wHqm/P8RRU/57LY/AgAKAYXWRUdAgABIxEDzwiqJGEFaAG0szoC3dk32pm4pd/mvC/OT85Ol7amJHGy0bgsN1NdqoaoUW/GgkDaBoAgJ5u4Y3cpgV6VbcArDgeKDuxZSGg2kEfUni9xSdfhwiJ5zrdALssQwC7oVXonWYIAqBAAEpYhNPhmA1wchSlNvDgeS85JGg19HjD5lvStJiZ3IksHENIgTxju58Fz4DL6HgCfq3kJjqp6oBtEUhxdUztUMrGZBN4FNosHTAxFK0dfMAxgCKtrzQkH2E2hV92lCcrywnJzaoyZeNm9PVRI1LfZqTMkPThDUcMsWGdZmWuZnVhypOPuiZPyaprxc68b4+++Yzc/DZjRtWVuxUt9c/KNIJNrulxu5GVm1g+xgaWZdIpqeqBdxoypCwf0eNCNCfiF6J6bWZudonMG8FzcJykkKpHNsLZ3MQQOyHi/GwlruWo3pis7hwo18GgLY1Bok1xq8hExLKmhW1xtjpaQ1jH2x4JFpFbk2pa6DW2ijcDKIz2pdcVW6U6bbkAoMVN27VMy1tPWZf1TBSgUBK1F3KehQVpc0RYxLcWuEjPt6DZBkttXpFaKxTt2Ksi47HyxgU1vkFWFA3xUdMwPUlEkoV5kvaFO2RGxpuGgqRx1/zlYAUDI71UmPvYJAUUFB5RdL5mmhpR3kCxQkY8AEaGusFQe5dqoJPfWruDbfaK2fGtqQvUV2Lik2uDiglyu1VXD3Qi5HqRkYRZwTVm4+KxXGEGGU0WJEqcl/BDik9eAMenQ36Cbu2EVi5vehdOsJGxGPtYq2QXVGB9wIFddc55LoWGjaIWIWYeavKC89TOnBGzyAi28ULOyxuwKZNjRfBUyAMO4zwMsgV4nnbPjCgwiCJcdZBBqSxaocYlgeBvHX4m7nw6CjNSXeqzdJdLgfQkg6dq5fhR8H9o0rwFSMQ8VhtAJYe35aZET4iWopQ13OJlnGo18myWt7v5/4PIrsJn+B5oKWaxZAoTzSqIGi9K46MH3NXtRhHQ8GCywExJqnZPZFmi5YjIdIAEB1rPrSeOdkSYW+IRKiu0k5LP50BSGda6vDmBwtgx247NTHZPWxRwyF23ssy2BBf/GJYTISDKIBcKOr6vHYdD9EYJlqxK5lJIQiOaF2IRGBlMRXVIfSy4KPrDJCynMvyd2NOT1b6r7UWwAio+SoCi2oQoOdevbH/v6cEl8o0mH/oZIWmS8AiPWfCfqdjQ+wTYmR3buVWi16SQ8ztWLXlnxER6CnvpvXk0hREegqVd+qV8ViDS09sqXC698ESgKQwCLQM4l+jLQJ6jGX6EMSlvX9gea0tfKh2bFSv9yu3KeAcYRjFcFSKICJOb4hzMOwb9KPoRxn68Kp8tb0OP9PdjX416zS5IeBTAQ2ANVEMrs+IoSkPVOTEjc/DRCiDan7bA3anH3aYcsdqognWX2bvZcclEyiMybiDRCalqKVHrTJFpjC2rdgoPQ3rSiAOogw2axB2sT/zMpzJIWqeIZ5t72yebBqtqSbNp1mwbeEZtaxWxsPpGoWJEZGBkRLANIwMiww9Qi8oLs29IdAC5T8J0hlevogV3yZbYVeoZpDttFS5DMpBgS7ZEch0B625DMhIPpm5FvlrjItAmTEs2JQ4b3dzWHVj9nZQQiVgFRETgylMQ1FfqZ5+5emM0oTR9W3GkLe0WdP+9LuNSB7sg9BcHWuEJ+U0sFotsVW3VHYbMxEg9k1XDiFQfJS+s05rsRCjA/bcuc70W2EM75JNdanXS8TTnsHOSrjtkeYsSVAPmzXxrRHcGrmtKdWvSOpVzYw0DiUgROs2gP64COjHRpVJeX9u6raVWR4xAMupxxQ05AYvbWiKdcWoqwddQtRV/YhXtnNQ9CP0PTfCVJOP35u+puOCSEazwFUCsgCsY4T1Uk9GNCqfdgcHLA9/jiJWueI/wd8fl8+UP5ahUYGZgQrKJCQPXsiyXblK0TDqxVcK9z6PV5ycrP3dT/jL9HOFwaXeP3SwVQdLafTLDsl31/uQmK5mWYzsuv6qe3kOeOf4Lt9kW50KNK640ldMyKz/Q2pzTVimOyynH3ZKF32aiCZI0M+869MOliMqhtbSeuYX2d1tM4QIye90zM8hp+V0PdioP+vfoXDjdRf3UkGM4dLUI+qS7wb1ixcbs99zkdXIjiU9QrObpGqZwc6/Z2OiJ8PBUPtzlTJuZewpsBhU0EqI22v0ybzajJtuVTbfhDnfhbr1Zq7E3hfsDPbPO7NlLwR6Jta1xUl5x353QPQY7sNcnZJ+DDBy0eaooVCYyQiMwmgak0qEUxPg6UF81N5lLzcCo/aLaKUqi55vOpaRZSTpyuDPLDFNL/Z6sZAAYlK5otZLXOgmPBdepp9KAIN3dzikPs9WcqNjILeafIOo5WX4X9b9Oojnltfb6+936dhNdY1gQH9CJ8aYzpn8U9JsHCuQGzY4A1bpIG9c06Og4ZnV8P+ecM+DcshWOKjyWKbI0zpc19SB/itFfnmh0J1pPPZEe7/j5KbyabrXUGegktUnS7wcwYWyoywX1z+I/Yq/H5Jw0NJNz7aY9NvalvzD9uSyIH7Nw6k52brU9sErtFh4/8Z5FNi7FOJoGxg1ty0hqMtJm0HX0wLPKn1YBTsQj6Cnk//K7JhfWQiaICM6PF497HYLHu5wba0ZHvRS34/dMCfzNYxeQF1FekuWi4/jvIzOnZBCuJ0giF6LAXCgfTKyTkVUaiWU7ZpGmWzvdSnJSN76TFTarl+6oMlOP5AD4UtVyRgW3jzrqiGAa2Nri2h3q3KJXzfpQai7PM+mfwKlHHK7NFH/MKOwvBdhGBO8geIqzN4owTpHkhbLJKGem7FR2s8i1U4RLtkf+vYtPtTw7q/w303Ja+FPCITUPg2tItUh9TOR0jM02cUrVmJEWmM5gKeMU8wZtQJ8o+jYIB24vE7lKuhKTcsC9j4O6Tu5izvwt7/ALwBd76bzij7GHVHM52yacBsjQ6gp2+f/QMojx9wkQutSk9cX8uvAz7qiUYcxA/8lIOczvEclXyj50xZ+hII/ajor+lxyL4RLb/hlJdyaxXt/+yT/mZGzXJwJ2e1EmYR5KEspueDcsYh1Tn0HQS+jrt5fSyee9AjP99TJGZUivFgOzWGZp+t3EnTh159yetY1LEjYWM1miEbOlTKD6UtrKDd5tzsolK+XVT+xbmouOusLkSSovDqWZmxF5Gk32Mate28NMeOGMyVzkUSZXTh4z3dTlgeSNyalcMG9xKmba/NY1S2tXDk2dx9JkpOXc2C+lLa/uI9QTjBLp+UGoblk+m/Y2j0nW7ohVDpY+2uaBabaXHqBf/0/1y8+QhChJ1gqnGRIbENAVh9mob3UFQxDCTbNx3LyTjQwrt42vKtQTOzcb2Z5q2LI6VDYGhMQMk0ujAAA=) format('woff2');
    font-weight: 400;
    font-style: normal;
    font-display: block;
  }
  :root {
    --bg: #f5f5f4;
    --panel: #ffffff;
    --ink: #1a1a1a;
    --ink-muted: #6b6b6b;
    --border: rgba(0,0,0,0.08);
    --edge: rgba(60,60,60,0.55);
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #15151a;
      --panel: #202027;
      --ink: #ededee;
      --ink-muted: #9a9aa2;
      --border: rgba(255,255,255,0.10);
      --edge: rgba(230,230,235,0.5);
    }
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif; overflow: hidden; }
  #city-filter { font: inherit; font-size: 13px; font-weight: 500; color: var(--ink);
    background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 8px 12px;
    flex: none; cursor: pointer; }
  svg { width: 100vw; height: 100vh; display: block; cursor: grab;
    transition: transform 0.55s cubic-bezier(0.5, 0, 0.2, 1), opacity 0.5s ease; }
  svg:active { cursor: grabbing; }
  .edge { stroke: var(--edge); fill: none; }
  .node-thumb { pointer-events: none; transition: opacity 0.2s ease; }
  .node-hit { fill: transparent; cursor: pointer; }
  .node-label { font-family: 'DotGothic16', monospace; font-size: 16px; fill: var(--ink-muted);
    pointer-events: none; font-weight: 400; letter-spacing: 0.3px; }
  .node-label-dot { pointer-events: none; }
  .node-sublabel { font-size: 10px; fill: var(--ink-muted); text-anchor: middle; pointer-events: none;
    opacity: 0.75; }

  #detail { position: fixed; inset: 0; z-index: 20; background: var(--panel);
    opacity: 0; pointer-events: none; overflow-y: auto;
    transition: opacity 0.42s ease; }
  #detail.open { opacity: 1; pointer-events: auto; }
  #detail-header { position: sticky; top: 0; display: flex; align-items: center; gap: 14px;
    padding: 18px 24px; background: var(--panel); border-bottom: 1px solid var(--border); z-index: 2; }
  #detail-back { width: 36px; height: 36px; border-radius: 18px; border: none; flex: none;
    background: var(--bg); color: var(--ink); font-size: 16px; cursor: pointer; }
  #detail-swatch { width: 34px; height: 34px; border-radius: 9px; flex: none; }
  #detail-title { font-size: 16px; font-weight: 600; letter-spacing: -0.2px; }
  #detail-sub { font-size: 13px; color: var(--ink-muted); }
  .seg-toggle { position: relative; display: flex; gap: 2px; background: var(--bg);
    border-radius: 10px; padding: 2px; flex: none; }
  .seg-toggle-pill { position: absolute; top: 2px; height: calc(100% - 4px);
    background: var(--panel); border-radius: 8px; transform-origin: center; }
  .seg-toggle button { position: relative; z-index: 1; font: inherit; font-size: 12px; font-weight: 500;
    color: var(--ink-muted); background: none; border: none; border-radius: 8px; padding: 6px 10px;
    cursor: pointer; transition: color 0.28s ease; }
  .seg-toggle button.active { color: var(--ink); }
  #graph-view-toggle { position: fixed; top: 18px; left: 50%; transform: translateX(-50%); z-index: 5; }
  #detail-grid { padding: 20px 24px 60px; display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 6px;
    transition: opacity 0.12s ease; }
  #detail-grid.location-mode { display: block; }
  .detail-group { margin-bottom: 28px; }
  .detail-group-heading { font-size: 13px; font-weight: 600; color: var(--ink);
    margin: 0 0 10px; letter-spacing: -0.1px; }
  .detail-group-grid { display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 6px; }
  .detail-tile { position: relative; aspect-ratio: 1; border-radius: 10px; overflow: hidden;
    background: var(--bg); will-change: transform, opacity; }
  .detail-tile img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .detail-name { position: absolute; bottom: 4px; left: 5px; font-size: 10px; color: #fff;
    background: rgba(0,0,0,0.45); padding: 2px 5px; border-radius: 5px; max-width: calc(100% - 10px);
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>
</head>
<body>
<svg id="graph"></svg>

<div id="graph-view-toggle" class="seg-toggle">
  <div class="seg-toggle-pill"></div>
  <button type="button" data-mode="colour" class="active">Colours</button>
  <button type="button" data-mode="location">Locations</button>
</div>

<div id="detail">
  <div id="detail-header">
    <button id="detail-back">←</button>
    <div id="detail-swatch"></div>
    <div>
      <div id="detail-title"></div>
      <div id="detail-sub"></div>
    </div>
    <div id="view-toggle" class="seg-toggle" style="margin-left:auto">
      <div class="seg-toggle-pill"></div>
      <button type="button" data-mode="flat" class="active">All</button>
      <button type="button" data-mode="location">By Location</button>
    </div>
    <select id="city-filter"><option value="">All cities</option></select>
  </div>
  <div id="detail-grid"></div>
</div>

<script id="graph-data" type="application/json">__DATA__</script>
<script>
const data = JSON.parse(document.getElementById('graph-data').textContent);
const svg = document.getElementById('graph');
const W = () => window.innerWidth, H = () => window.innerHeight;

// the two things the main page can group bubbles by: colour (the original
// Sanzo-style clusters, with similarity edges) or location (every photo
// re-bucketed by city, connected in the order you actually visited them —
// see buildLocationTimelineEdges below).
const colourGroups = data.groups.map(g => ({ ...g, label: g.centroid_hex }));
const colourEdges = data.edges;
const allPhotos = data.groups.flatMap(g => g.photos);

function averageHex(photos) {
  let r = 0, g = 0, b = 0;
  for (const p of photos) {
    const hex = p.hex.replace('#', '');
    r += parseInt(hex.slice(0, 2), 16);
    g += parseInt(hex.slice(2, 4), 16);
    b += parseInt(hex.slice(4, 6), 16);
  }
  const n = photos.length;
  const toHex = v => Math.round(v / n).toString(16).padStart(2, '0');
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

function buildLocationGroups() {
  const byCity = new Map();
  for (const p of allPhotos) {
    const key = p.city || 'Unknown location';
    if (!byCity.has(key)) byCity.set(key, []);
    byCity.get(key).push(p);
  }
  return [...byCity.entries()]
    .sort((a, b) => b[1].length - a[1].length)
    .map(([city, photos], i) => ({
      id: i,
      label: city,
      centroid_hex: averageHex(photos),
      count: photos.length,
      photos,
    }));
}

// connects each city to the one that followed it chronologically — an
// itinerary path (city1–city2–city3–…), not a nearest-neighbour mesh.
// "Visited" time is a city's earliest photo timestamp (first arrival);
// photo taken_at comes straight from EXIF via the generator's cache, so
// this is the actual trip order, not a guess.
function buildLocationTimelineEdges(groups) {
  const withTime = groups
    .map(g => {
      const times = g.photos.map(p => Date.parse(p.taken_at)).filter(Number.isFinite);
      return times.length ? { g, t: Math.min(...times) } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.t - b.t);
  if (withTime.length < 2) return [];

  const gaps = [];
  for (let i = 0; i < withTime.length - 1; i++) gaps.push(withTime[i + 1].t - withTime[i].t);
  const minGap = Math.min(...gaps), maxGap = Math.max(...gaps);
  const span = Math.max(1, maxGap - minGap);

  return withTime.slice(0, -1).map((cur, i) => ({
    source: cur.g.id,
    target: withTime[i + 1].g.id,
    // a shorter gap to the next stop reads as a tighter leg of the trip —
    // same 0–1 "similarity" convention the colour edges use for line
    // weight/opacity and the edge-spring's target distance
    similarity: Math.max(0.2, Math.min(0.95, 1 - (gaps[i] - minGap) / span)),
  }));
}

const svgns = 'http://www.w3.org/2000/svg';
function el(tag, attrs) {
  const e = document.createElementNS(svgns, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  return e;
}

// Each node is modelled as a sphere of photos: every thumbnail sits at a fixed
// point on a unit sphere (even coverage via the Fibonacci-sphere method), and
// each frame the sphere is rotated slowly about its vertical axis (classic
// "spinning globe" — only x/z orbit, y stays put) and reprojected to 2D.
// z-depth drives scale + opacity so the far side visibly recedes. Photos stay
// upright the whole time (billboarded, never rotated in-plane) since we only
// ever translate+scale the wrapping <g>, never rotate it.

// deterministic pseudo-random in [0,1) from a seed — keeps layout + spin speed
// stable across re-renders (no flicker/reshuffle) while still varying per node
function rnd(seed) {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
}

function matchScale(i, count) {
  if (count <= 1) return 1.15;
  const t = i / (count - 1);
  return 1.35 - t * 0.6; // 1.35x at the best match down to 0.75x at the weakest
}

function fibonacciSphere(count) {
  const pts = [];
  const offset = 2 / count;
  const increment = Math.PI * (3 - Math.sqrt(5)); // golden angle
  for (let i = 0; i < count; i++) {
    const y = (i * offset - 1) + offset / 2;
    const r = Math.sqrt(Math.max(0, 1 - y * y));
    const phi = i * increment;
    pts.push({ x: Math.cos(phi) * r, y, z: Math.sin(phi) * r });
  }
  return pts;
}

function buildThumbs(n) {
  const previewCount = Math.min(n.photos.length, Math.max(5, Math.min(14, Math.round(Math.sqrt(n.count) * 2.2))));
  const spherePts = fibonacciSphere(previewCount);
  const sphereR = n.r * 0.72; // < n.r, leaving room for tile half-size + "spaced out" gaps
  const baseSide = Math.max(16, (sphereR / Math.sqrt(previewCount)) * 1.75);

  return spherePts.map((pt, i) => ({
    photo: n.photos[i],
    pt,
    sizeScale: matchScale(i, previewCount),
    baseSide,
    bobPhase: rnd(n.id * 211 + i * 7 + 3) * Math.PI * 2,
    bobAmp: 1.5 + rnd(n.id * 211 + i * 7 + 4) * 2,
    bobSpeed: 0.5 + rnd(n.id * 211 + i * 7 + 5) * 0.4,
  }));
}

let clipCounter = 0;
const animStart = performance.now();

// builds one full graph (nodes + physics state + SVG elements + drag/click
// handlers) from a set of groups and edges. Called once up front for the
// colour view, and again whenever the top-level toggle switches to/from
// the location view — the returned object is what tick() reads each frame.
function buildGraph(groupsData, edgesData, showColourDot = true) {
  // on a small screen this stays close to the old fixed 180px ring; on a
  // big one it grows — and grows per-axis, since a wide monitor is mostly
  // wider, not taller, and a radius keyed off the smaller dimension barely
  // reacts to that extra width at all
  const spreadX = Math.max(180, W() * 0.3);
  const spreadY = Math.max(180, H() * 0.32);
  const nodes = groupsData.map((g, i) => ({
    ...g,
    r: 44 + Math.sqrt(g.count) * 11,
    x: W()/2 + Math.cos(i / groupsData.length * Math.PI * 2) * spreadX,
    y: H()/2 + Math.sin(i / groupsData.length * Math.PI * 2) * spreadY,
    vx: 0, vy: 0,
  }));
  const nodeById = Object.fromEntries(nodes.map(n => [n.id, n]));
  const edges = edgesData;

  const edgeEls = edges.map(e => {
    const line = el('line', { class: 'edge' });
    line.setAttribute('stroke-width', 0.3 + e.similarity * 0.8);
    line.style.opacity = 0.05 + e.similarity * 0.14;
    svg.appendChild(line);
    return { el: line, data: e };
  });

  const nodeGroups = nodes.map(n => {
    const g = el('g', { class: 'node-group' });

    n.sphereR = n.r * 0.72;
    n.spinSpeed = (0.05 + rnd(n.id * 13 + 3) * 0.045) * (rnd(n.id * 13 + 6) < 0.5 ? 1 : -1); // rad/s, alternating direction
    n.spinPhase = rnd(n.id * 13 + 4) * Math.PI * 2;

    const thumbs = buildThumbs(n);
    const thumbEls = [];       // { el, city } — used by the city filter to dim non-matches
    const thumbByPath = {};    // photo.path -> <image> — start positions for the click FLIP
    // best matches (drawn last, on top) also get a slight head start facing the viewer
    for (const th of [...thumbs].reverse()) {
      const half = th.baseSide / 2;
      const tg = el('g', {});
      const clipId = `clip-${clipCounter++}`;
      const clip = el('clipPath', { id: clipId });
      clip.appendChild(el('rect', { x: -half, y: -half, width: th.baseSide, height: th.baseSide, rx: th.baseSide * 0.2 }));
      tg.appendChild(clip);

      const img = el('image', {
        class: 'node-thumb',
        href: th.photo.thumbnail,
        x: -half, y: -half, width: th.baseSide, height: th.baseSide,
        preserveAspectRatio: 'xMidYMid slice',
        'clip-path': `url(#${clipId})`,
      });
      tg.appendChild(img);
      g.appendChild(tg);

      th.g = tg;
      thumbEls.push({ el: img, city: th.photo.city || null });
      thumbByPath[th.photo.path] = img;
    }
    n.thumbs = thumbs;
    n.thumbByPath = thumbByPath;

    // invisible click/drag target (slightly larger than r to cover sphere overshoot)
    const hit = el('circle', { class: 'node-hit', r: n.r * 1.15 });
    g.appendChild(hit);

    // colour swatch (colour view only — on the location view the "colour"
    // of a city bubble is just an average of whatever was in its photos,
    // not a meaningful reference like it is for an actual colour group) +
    // label, centred together as one unit. Text width is estimated from
    // character count rather than measured via getComputedTextLength() —
    // the label isn't attached to a live document yet at this point (it's
    // still being built inside a detached <g>), so DOM text-metrics calls
    // aren't reliable here. DotGothic16 is a fixed-width pixel font, so a
    // flat per-character estimate holds up fine.
    const labelFontSize = 16;
    const labelY = n.r + 18;
    const charW = labelFontSize * 0.62;
    const dotR = labelFontSize * 0.26;
    const dotGap = 6;
    const textWidth = n.label.length * charW;
    const rowWidth = (showColourDot ? dotR * 2 + dotGap : 0) + textWidth;
    const rowStartX = -rowWidth / 2;

    if (showColourDot) {
      const labelDot = el('circle', {
        class: 'node-label-dot', cx: rowStartX + dotR, cy: labelY - labelFontSize * 0.32,
        r: dotR, fill: n.centroid_hex,
      });
      g.appendChild(labelDot);
    }
    const label = el('text', {
      class: 'node-label',
      x: rowStartX + (showColourDot ? dotR * 2 + dotGap : 0),
      y: labelY, 'text-anchor': 'start',
    });
    label.textContent = n.label;
    const sublabel = el('text', { class: 'node-sublabel', y: n.r + 35 });
    sublabel.textContent = n.count + (n.count === 1 ? ' photo' : ' photos');
    g.appendChild(label);
    g.appendChild(sublabel);
    svg.appendChild(g);

    hit.addEventListener('click', (ev) => {
      ev.stopPropagation();
      if (dragMoved) return; // a real drag happened — don't also open the group
      openDetail(n);
    });

    let dragging = false, offX = 0, offY = 0, dragMoved = false, startX = 0, startY = 0;
    const DRAG_THRESHOLD = 4; // px of pointer movement before it counts as a drag, not a click
    hit.addEventListener('pointerdown', (ev) => {
      dragging = true; dragMoved = false; n.fixed = true;
      startX = ev.clientX; startY = ev.clientY;
      offX = n.x - ev.clientX; offY = n.y - ev.clientY;
      hit.setPointerCapture(ev.pointerId);
    });
    hit.addEventListener('pointermove', (ev) => {
      if (!dragging) return;
      if (!dragMoved) {
        const dx = ev.clientX - startX, dy = ev.clientY - startY;
        if (dx * dx + dy * dy > DRAG_THRESHOLD * DRAG_THRESHOLD) dragMoved = true;
      }
      n.x = ev.clientX + offX; n.y = ev.clientY + offY;
    });
    hit.addEventListener('pointerup', () => { dragging = false; });

    return { el: g, circle: hit, label, sublabel, thumbEls, data: n };
  });

  // release "fixed" a short while after drag ends so dropped nodes settle naturally
  nodeGroups.forEach(ne => {
    ne.circle.addEventListener('pointerup', () => {
      setTimeout(() => { ne.data.fixed = false; }, 1200);
    });
  });

  return { nodes, nodeById, edges, edgeEls, nodeGroups };
}

let current = buildGraph(colourGroups, colourEdges);
let transitioningGraph = false; // true while the collapse/emerge swap animation owns node transforms

// one physics increment: collision avoidance, similarity-edge spring, and a
// gentle pull back toward the screen centre. Shared by the normal steady-
// state tick() loop and emergeGraph — a freshly built graph's bubbles start
// heavily overlapping (a dozen city bubbles all placed on one small starting
// circle), and running this continuously through the emerge animation (the
// same way it already runs, unremarkably, during ordinary operation) lets
// that overlap resolve gradually. Freezing it and releasing it all at once
// is what caused the stutter-then-explode burst this replaced.
function stepPhysics(graph) {
  const n = graph.nodes;
  // the edge spring's target distance and the repulsion zone are both
  // fixed-pixel baselines — on a small screen that's the right size, but it
  // means connected (similar-colour) bubbles always spring back to roughly
  // the same small natural size no matter how much room there is, which is
  // what was actually pulling everything back into a knot: the initial
  // layout and the centering pull below were never the dominant force here.
  // Scaling both with screen width lets that natural resting size grow too.
  const spacingScale = Math.min(2.8, Math.max(1, W() / 750));
  for (let i = 0; i < n.length; i++) {
    for (let j = i + 1; j < n.length; j++) {
      const a = n[i], b = n[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      let dist = Math.sqrt(dx*dx + dy*dy) || 1;
      const minDist = a.r + b.r + 36;
      // a narrower personal-space zone (was 2.2x) so most pairs sit outside
      // it at rest instead of hovering right on its edge — that boundary is
      // an unstable equilibrium, which is what read as constant jitter
      const repelZone = minDist * 1.35 * spacingScale;
      if (dist < repelZone) {
        const force = (repelZone - dist) / dist * 0.007;
        const fx = dx * force, fy = dy * force;
        if (!a.fixed) { a.vx += fx; a.vy += fy; }
        if (!b.fixed) { b.vx -= fx; b.vy -= fy; }
      }
    }
  }
  for (const e of graph.edges) {
    const a = graph.nodeById[e.source], b = graph.nodeById[e.target];
    let dx = b.x - a.x, dy = b.y - a.y;
    let dist = Math.sqrt(dx*dx + dy*dy) || 1;
    const target = (a.r + b.r) + 90 * spacingScale * (1 - e.similarity);
    const force = (dist - target) / dist * 0.0032;
    const fx = dx * force, fy = dy * force;
    if (!a.fixed) { a.vx += fx; a.vy += fy; }
    if (!b.fixed) { b.vx -= fx; b.vy -= fy; }
  }
  const cx = W()/2, cy = H()/2;
  const maxV = 2; // hard velocity cap — stops any force spike turning into a visible snap
  // the pull back toward centre is a fixed-strength spring, but repulsion is
  // sized off fixed pixel radii — on a small screen that balance is fine,
  // but on a big one it reels bubbles into a tight knot in the middle
  // instead of letting them use the room. Softening the pull as each axis
  // grows (never strengthening it below baseline) lets repulsion win more
  // space at equilibrium, not just at the initial layout — done per-axis,
  // since a wide monitor is wide, not necessarily tall, and tying both to
  // whichever dimension is smaller barely responds to that extra width.
  const pullX = 0.0015 * Math.min(1, 900 / W());
  const pullY = 0.0015 * Math.min(1, 760 / H());
  for (const node of n) {
    if (!node.fixed) {
      node.vx += (cx - node.x) * pullX;
      node.vy += (cy - node.y) * pullY;
      node.vx *= 0.55; node.vy *= 0.55;
      node.vx = Math.max(-maxV, Math.min(maxV, node.vx));
      node.vy = Math.max(-maxV, Math.min(maxV, node.vy));
      node.x += node.vx; node.y += node.vy;
    }
    node.x = Math.max(node.r + 10, Math.min(W() - node.r - 10, node.x));
    node.y = Math.max(node.r + 60, Math.min(H() - node.r - 10, node.y));
  }
}

function tick() {
  const n = current.nodes;

  // during a collapse/emerge swap, collapseGraph/emergeGraph own each node's
  // position and outer transform entirely (emergeGraph steps its own physics
  // — see stepPhysics above — so this loop staying out of the way is what
  // avoids double-stepping it)
  if (!transitioningGraph) {
    stepPhysics(current);
    for (const ne of current.nodeGroups) {
      ne.el.setAttribute('transform', `translate(${ne.data.x},${ne.data.y})`);
    }
  }

  // spin every node's photo-sphere — slow rotation about the vertical axis
  // (x/z orbit, y fixed) plus a gentle independent per-tile float. z-depth
  // drives scale + opacity so the far side of the sphere visibly recedes.
  // kept running through a collapse/emerge swap so thumbnails are already
  // spinning/spread into formation rather than popping in once it ends.
  const elapsed = (performance.now() - animStart) / 1000;
  for (const node of n) {
    const angle = node.spinPhase + elapsed * node.spinSpeed;
    const cosA = Math.cos(angle), sinA = Math.sin(angle);
    for (const th of node.thumbs) {
      const rx = th.pt.x * cosA - th.pt.z * sinA;
      const rz = th.pt.x * sinA + th.pt.z * cosA;
      const bob = Math.sin(elapsed * th.bobSpeed + th.bobPhase) * th.bobAmp;
      const screenX = rx * node.sphereR;
      const screenY = th.pt.y * node.sphereR + bob;
      const depth = (rz + 1) / 2; // 0 = far side, 1 = near side
      const scale = (0.65 + depth * 0.5) * th.sizeScale;
      th.g.setAttribute('transform', `translate(${screenX.toFixed(2)},${screenY.toFixed(2)}) scale(${scale.toFixed(3)})`);
      th.g.style.opacity = (0.92 + depth * 0.08).toFixed(2);
    }
  }

  if (!transitioningGraph) {
    for (const ee of current.edgeEls) {
      const a = current.nodeById[ee.data.source], b = current.nodeById[ee.data.target];
      ee.el.setAttribute('x1', a.x); ee.el.setAttribute('y1', a.y);
      ee.el.setAttribute('x2', b.x); ee.el.setAttribute('y2', b.y);
    }
  }
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);

// moves a .seg-toggle's pill indicator under whichever button is .active —
// not a slide: it deflates to nothing where it was, jumps, then pops back
// out on the new tab (organic shrink/grow rather than a mechanical glide)
function positionPill(container, animate = true) {
  const pill = container.querySelector('.seg-toggle-pill');
  const activeBtn = container.querySelector('button.active');
  if (!pill || !activeBtn) return;
  const left = activeBtn.offsetLeft - 2;
  const width = activeBtn.offsetWidth;

  if (!animate) {
    pill.style.transition = 'none';
    pill.style.left = left + 'px';
    pill.style.width = width + 'px';
    pill.style.transform = 'scale(1)';
    pill.style.opacity = '1';
    void pill.offsetWidth; // flush so a later animated call doesn't inherit 'none'
    pill.style.transition = '';
    return;
  }

  // 1. shrink away evenly (both axes, not just width — a squish-only shrink
  //    reads as a flip, a uniform one reads as genuinely getting smaller),
  //    right where it's currently sitting
  pill.style.transition = 'transform 0.16s cubic-bezier(0.4, 0, 1, 1), opacity 0.16s ease-in';
  pill.style.transform = 'scale(0.4)';
  pill.style.opacity = '0';
  setTimeout(() => {
    // 2. jump to the new tab's position/size while invisible
    pill.style.transition = 'none';
    pill.style.left = left + 'px';
    pill.style.width = width + 'px';
    void pill.offsetWidth; // flush before re-enabling the transition
    // 3. grow back in with a touch of overshoot
    pill.style.transition = 'transform 0.32s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease-out';
    pill.style.transform = 'scale(1)';
    pill.style.opacity = '1';
  }, 150);
}

// top-level view toggle — switches the whole graph between colour-group
// bubbles (colour-similarity edges) and city bubbles (chronological-visit-
// order edges — see buildLocationTimelineEdges above). The swap itself is a
// collapse-to-centre / emerge-from-centre animation rather than a hard cut
// — see collapseGraph/emergeGraph below.
const graphViewToggle = document.getElementById('graph-view-toggle');
const graphViewButtons = document.querySelectorAll('#graph-view-toggle button');
let graphMode = 'colour';

const easeInCubic = t => t * t * t;
const easeOutCubic = t => 1 - Math.pow(1 - t, 3);

// runs a tween for `duration`ms, calling render(easedT) every frame, then onDone
function tween(duration, ease, render, onDone) {
  const start = performance.now();
  function frame(now) {
    const t = Math.min(1, (now - start) / duration);
    render(ease(t));
    if (t < 1) requestAnimationFrame(frame);
    else onDone();
  }
  requestAnimationFrame(frame);
}

// every bubble rushes inward to the centre of the screen, shrinking and
// picking up a small spin as it goes — a vortex collapse, not a hard cut
function collapseGraph(graph, onDone) {
  const cx = W() / 2, cy = H() / 2;
  const starts = graph.nodeGroups.map(ne => ({ x: ne.data.x, y: ne.data.y }));
  graph.edgeEls.forEach(ee => {
    ee.el.style.transition = 'opacity 0.22s ease-in';
    ee.el.style.opacity = '0';
  });
  tween(360, easeInCubic, (e) => {
    graph.nodeGroups.forEach((ne, i) => {
      const s = starts[i];
      const x = s.x + (cx - s.x) * e;
      const y = s.y + (cy - s.y) * e;
      const rot = -14 * e;
      const scale = 1 - e;
      ne.el.setAttribute('transform', `translate(${x},${y}) rotate(${rot}) scale(${scale})`);
    });
  }, onDone);
}

// the new set of bubbles starts as a point at the centre and eases outward,
// unspinning as they settle. Position is a blend of "still at the centre"
// and "wherever stepPhysics has live-settled it to" — physics runs every
// frame of this (not frozen and released afterward), so a freshly built,
// heavily overlapping layout (a dozen city bubbles starting on one small
// circle) resolves itself gradually and gently, the same unremarkable way
// it already does during ordinary operation, instead of all at once.
function emergeGraph(graph, onDone) {
  const cx = W() / 2, cy = H() / 2;
  graph.nodeGroups.forEach(ne => ne.el.setAttribute('transform', `translate(${cx},${cy}) rotate(14) scale(0)`));
  graph.edgeEls.forEach(ee => {
    const restOpacity = ee.el.style.opacity;
    ee.el.style.opacity = '0';
    ee.el.dataset.restOpacity = restOpacity;
  });
  tween(850, easeOutCubic, (e) => {
    stepPhysics(graph);
    graph.nodeGroups.forEach(ne => {
      const x = cx + (ne.data.x - cx) * e;
      const y = cy + (ne.data.y - cy) * e;
      const rot = 14 * (1 - e);
      ne.el.setAttribute('transform', `translate(${x},${y}) rotate(${rot}) scale(${e})`);
    });
  }, () => {
    graph.edgeEls.forEach(ee => {
      ee.el.style.transition = 'opacity 0.35s ease-out';
      ee.el.style.opacity = ee.el.dataset.restOpacity;
    });
    onDone();
  });
}

function switchGraphView(mode) {
  if (transitioningGraph || mode === graphMode) return;
  graphMode = mode;
  transitioningGraph = true;
  svg.style.pointerEvents = 'none';
  graphViewButtons.forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  positionPill(graphViewToggle);

  collapseGraph(current, () => {
    svg.innerHTML = '';
    const groupsData = mode === 'location' ? buildLocationGroups() : colourGroups;
    const edgesData = mode === 'location' ? buildLocationTimelineEdges(groupsData) : colourEdges;
    current = buildGraph(groupsData, edgesData, mode !== 'location');
    emergeGraph(current, () => {
      transitioningGraph = false;
      svg.style.pointerEvents = '';
    });
  });
}
graphViewButtons.forEach(b => b.addEventListener('click', () => switchGraphView(b.dataset.mode)));
positionPill(graphViewToggle, false);

// city filter (inner detail page) — dims non-matching thumbnails and relabels
// counts, without touching layout/positions
let activeCity = '';
const cityFilter = document.getElementById('city-filter');
const allCities = [...new Set(allPhotos.map(p => p.city).filter(Boolean))].sort();
for (const c of allCities) {
  const opt = document.createElement('option');
  opt.value = c;
  opt.textContent = c;
  cityFilter.appendChild(opt);
}

// two detail-page view modes: 'flat' (one grid, city dropdown dims/orders it)
// and 'location' (photos split into a section per city). Lives inside the
// detail header now — filters/regroups the currently open group in place
// rather than touching the outer map.
let openNode = null;
let viewMode = 'flat';

function makeTile(p) {
  const tile = document.createElement('div');
  tile.className = 'detail-tile';
  tile.dataset.city = p.city || '';
  if (viewMode === 'flat' && activeCity && p.city !== activeCity) tile.dataset.dim = '1';
  const img = document.createElement('img');
  img.src = p.thumbnail;
  img.loading = 'lazy';
  const name = document.createElement('div');
  name.className = 'detail-name';
  name.textContent = p.city ? `${p.city} · ${p.path.split('/').pop()}` : p.path.split('/').pop();
  tile.appendChild(img);
  tile.appendChild(name);
  return tile;
}

// builds the grid content for the open node under the current viewMode,
// returns the flat list of { tile, path } used to drive the FLIP-in animation
function buildDetailGrid(n) {
  detailGrid.innerHTML = '';
  const tileRefs = [];

  if (viewMode === 'location') {
    detailGrid.classList.add('location-mode');
    const groups = new Map();
    for (const p of n.photos) {
      const key = p.city || 'Unknown location';
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key).push(p);
    }
    const keys = [...groups.keys()].sort((a, b) => {
      if (a === 'Unknown location') return 1;
      if (b === 'Unknown location') return -1;
      return a.localeCompare(b);
    });
    for (const key of keys) {
      const photos = groups.get(key);
      const section = document.createElement('div');
      section.className = 'detail-group';
      const heading = document.createElement('div');
      heading.className = 'detail-group-heading';
      heading.textContent = `${key} · ${photos.length}`;
      const sectionGrid = document.createElement('div');
      sectionGrid.className = 'detail-group-grid';
      for (const p of photos) {
        const tile = makeTile(p);
        sectionGrid.appendChild(tile);
        tileRefs.push({ tile, path: p.path });
      }
      section.appendChild(heading);
      section.appendChild(sectionGrid);
      detailGrid.appendChild(section);
    }
  } else {
    detailGrid.classList.remove('location-mode');
    // matching photos (if filtered) lead, so they're visible without scrolling
    const ordered = activeCity
      ? [...n.photos].sort((a, b) => (b.city === activeCity) - (a.city === activeCity))
      : n.photos;
    for (const p of ordered) {
      const tile = makeTile(p);
      detailGrid.appendChild(tile);
      tileRefs.push({ tile, path: p.path });
    }
  }
  return tileRefs;
}

function updateDetailSub(n) {
  if (viewMode === 'location') {
    const cities = new Set(n.photos.map(p => p.city).filter(Boolean));
    const locCount = cities.size + (n.photos.some(p => !p.city) ? 1 : 0);
    document.getElementById('detail-sub').textContent =
      `${n.count} ${n.count === 1 ? 'photo' : 'photos'} across ${locCount} ${locCount === 1 ? 'location' : 'locations'}`;
  } else {
    const matchCount = activeCity ? n.photos.filter(p => p.city === activeCity).length : n.count;
    document.getElementById('detail-sub').textContent = activeCity
      ? `${matchCount} of ${n.count} photos in this group are from ${activeCity}`
      : n.count + (n.count === 1 ? ' photo' : ' photos') + ' in this group';
  }
}

// rebuilds the open group's grid in place (city filter change, view-mode
// toggle) — no fly-in, the tiles just resettle with a quick crossfade
function refreshOpenGroup() {
  if (!openNode) return;
  const n = openNode;
  updateDetailSub(n);
  detailGrid.style.opacity = '0';
  setTimeout(() => {
    buildDetailGrid(n);
    detailGrid.style.opacity = '1';
  }, 120);
}
cityFilter.addEventListener('change', () => {
  activeCity = cityFilter.value;
  refreshOpenGroup();
});

const viewToggle = document.getElementById('view-toggle');
const viewToggleButtons = document.querySelectorAll('#view-toggle button');
function setViewMode(mode) {
  if (viewMode === mode) return;
  viewMode = mode;
  viewToggleButtons.forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  positionPill(viewToggle);
  cityFilter.style.display = mode === 'location' ? 'none' : '';
  refreshOpenGroup();
}
viewToggleButtons.forEach(b => b.addEventListener('click', () => setViewMode(b.dataset.mode)));
positionPill(viewToggle, false);

const detail = document.getElementById('detail');
const detailGrid = document.getElementById('detail-grid');

function openDetail(n) {
  openNode = n;
  // 1. capture each preview thumbnail's on-screen rect BEFORE the graph zooms,
  //    so the grid tiles can fly out from exactly where they sat in the cluster
  const startRects = {};
  for (const path in n.thumbByPath) {
    startRects[path] = n.thumbByPath[path].getBoundingClientRect();
  }
  const nodeX = n.x, nodeY = n.y;

  document.getElementById('detail-swatch').style.background = n.centroid_hex;
  document.getElementById('detail-title').textContent = n.label;
  updateDetailSub(n);

  detailGrid.style.opacity = '1';
  const tileRefs = buildDetailGrid(n);

  // 2. "fly into the node": the whole graph scales up toward the clicked node
  //    and fades, so the viewer feels pulled in through it
  svg.style.transformOrigin = nodeX + 'px ' + nodeY + 'px';
  svg.style.transform = 'scale(2.6)';
  svg.style.opacity = '0';
  svg.style.pointerEvents = 'none';

  // 3. reveal the detail surface (bg fades in) and FLIP each tile from its
  //    cluster position into its grid cell — the pile reorganising into a grid
  detail.classList.add('open');
  detail.scrollTop = 0;

  requestAnimationFrame(() => {
    for (const { tile, path } of tileRefs) {
      const fr = tile.getBoundingClientRect();
      const sr = startRects[path];
      let dx, dy, scale, startOpacity;
      if (sr) {
        dx = (sr.left + sr.width / 2) - (fr.left + fr.width / 2);
        dy = (sr.top + sr.height / 2) - (fr.top + fr.height / 2);
        scale = Math.max(sr.width, 6) / fr.width;
        startOpacity = '1';
      } else {
        // photos not shown in the cluster preview spawn from the node centre
        dx = nodeX - (fr.left + fr.width / 2);
        dy = nodeY - (fr.top + fr.height / 2);
        scale = 0.16;
        startOpacity = '0';
      }
      tile.style.transition = 'none';
      tile.style.transform = `translate(${dx}px, ${dy}px) scale(${scale})`;
      tile.style.opacity = startOpacity;
    }
    void detailGrid.offsetWidth; // flush the start state before animating
    tileRefs.forEach(({ tile }, idx) => {
      const delay = Math.min(idx * 11, 240);
      tile.style.transition =
        `transform 0.62s cubic-bezier(0.22, 1, 0.36, 1) ${delay}ms, opacity 0.42s ease ${delay}ms`;
      tile.style.transform = 'none';
      tile.style.opacity = tile.dataset.dim ? '0.3' : '1';
    });
  });
}

function closeDetail() {
  if (!detail.classList.contains('open')) return;
  openNode = null;
  detail.classList.remove('open');
  svg.style.transform = 'scale(1)';
  svg.style.opacity = '1';
  svg.style.pointerEvents = '';
  // clear grid once faded so stale tiles never flash on the next open
  setTimeout(() => {
    if (!detail.classList.contains('open')) detailGrid.innerHTML = '';
  }, 450);
}
document.getElementById('detail-back').addEventListener('click', closeDetail);
document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') closeDetail(); });
</script>
</body>
</html>
"""
def main():
    if len(sys.argv) < 3:
        print("usage: visualize.py <groups_json> <output_html>")
        sys.exit(1)

    groups_path = Path(sys.argv[1]).expanduser().resolve()
    out_path = Path(sys.argv[2]).expanduser().resolve()

    with open(groups_path) as f:
        data = json.load(f)

    total_photos = sum(g["count"] for g in data["groups"])
    payload = json.dumps(data).replace("</script>", "<\\/script>")

    html = (TEMPLATE
            .replace("__DATA__", payload)
            .replace("__TOTAL__", str(total_photos))
            .replace("__GROUPS__", str(len(data["groups"]))))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"Wrote {out_path} ({len(html)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
