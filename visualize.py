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
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Colour Map — __TOTAL__ photos, __GROUPS__ groups</title>
<style>
  /* subset to printable Basic Latin (U+0020–007E) — the only characters any
     node label needs (hex codes, city names, digits) — from
     DotGothic16-Regular.ttf (desktop ~/Desktop/DotGothic16), cut down from
     ~2MB to ~3KB with pyftsubset so it's cheap to inline here */
  @font-face {
    font-family: 'DotGothic16';
    src: url(data:font/woff2;base64,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) format('woff2');
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
    --gallery: #f6f4ef;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #15151a;
      --panel: #202027;
      --ink: #ededee;
      --ink-muted: #9a9aa2;
      --border: rgba(255,255,255,0.10);
      --edge: rgba(230,230,235,0.5);
      --gallery: #16161a;
    }
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; height: 100%; background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif; overflow: hidden; }
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
  #detail-title { font-size: 16px; font-weight: 600; letter-spacing: -0.2px; }
  .seg-toggle { position: relative; display: flex; gap: 2px; background: var(--bg);
    border-radius: 10px; padding: 2px; flex: none; }
  .seg-toggle-pill { position: absolute; top: 2px; height: calc(100% - 4px);
    background: var(--panel); border-radius: 8px; transform-origin: center; }
  .seg-toggle button { position: relative; z-index: 1; font: inherit; font-size: 12px; font-weight: 500;
    color: var(--ink-muted); background: none; border: none; border-radius: 8px; padding: 6px 10px;
    cursor: pointer; transition: color 0.28s ease; }
  .seg-toggle button.active { color: var(--ink); }
  #graph-view-toggle { position: fixed; top: 18px; left: 50%; transform: translateX(-50%); z-index: 5; }
  /* detail gallery — editorial scatter (photos at their natural aspect, mixed
     sizes, staggered across a 12-col grid with lots of air) on a warm ground.
     Positions are computed in JS (layoutScatter); under 700px it collapses to
     a single full-width column, and small groups fit one row with no scroll. */
  /* The page takes the open group's own colour as its ground (--g-bg, set in
     openDetail); ink/control colours flip light or dark against it
     (applyGalleryTheme) so text stays legible on any hex. */
  #detail { background: var(--g-bg, var(--gallery)); color: var(--g-ink, var(--ink));
    --ink: var(--g-ink); --ink-muted: var(--g-muted); }
  #detail-header { position: static; flex-direction: column; justify-content: center; gap: 0;
    padding: 64px 24px 24px; background: transparent; border-bottom: none; text-align: center; }
  #detail-back { position: fixed; top: 18px; left: 24px; z-index: 5; padding: 0;
    display: grid; place-items: center;
    background: var(--g-chip); color: var(--g-ink);
    -webkit-backdrop-filter: blur(12px); backdrop-filter: blur(12px); }
  /* override the graph's global svg rule (100vw/100vh, grab cursor, transition) */
  #detail-back svg { display: block; width: 16px; height: 16px; cursor: inherit; transition: none; }
  #detail-back { cursor: pointer; }
  /* the hex title scrolls up at ~60% speed while shrinking, then pins at the
     top level with the back button (no backing — photos pass under it) —
     driven by updateDetailTitle on scroll */
  /* fixed to the viewport (not in the scrolling flow) so the browser's
     scroll can't drag it between JS updates — #detail-title-space holds its
     place in the header */
  #detail-title { position: fixed; top: 0; left: 0; right: 0; z-index: 4; text-align: center;
    font-family: 'DotGothic16', monospace;
    font-weight: 400; font-size: clamp(48px, 8vw, 104px); line-height: 1; letter-spacing: 0.5px;
    transform-origin: 50% 0; will-change: transform; pointer-events: none; }
  /* tabs: same shape as the main page's toggle, but no container fill — the
     active tab is a soft translucent pill (padding kept at 2px: positionPill
     offsets by it) */
  #view-toggle { margin-top: 24px; background: transparent; }
  #view-toggle .seg-toggle-pill { background: var(--g-tab); }
  #view-toggle button { color: var(--g-muted); }
  #view-toggle button.active { color: var(--g-ink); }
  #detail-grid { padding: 24px 24px 120px; transition: opacity 0.12s ease; }
  #detail-grid.fit-mode { padding-bottom: 24px; }
  /* By Location sections: city in large translucent DotGothic, separated by
     a hand-drawn wobbly, slightly slanted rule (wobblyDivider) */
  .detail-group { margin-bottom: 0; }
  .detail-group-heading { font-family: 'DotGothic16', monospace; font-weight: 400;
    font-size: clamp(32px, 4.4vw, 56px); line-height: 1; letter-spacing: 0.5px;
    color: var(--ink); opacity: 0.55; margin: 0 0 28px; }
  .detail-group-count { font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
    font-size: 13px; letter-spacing: 0; vertical-align: top; margin-left: 6px; }
  .detail-divider { margin: 72px 0 56px; color: var(--ink); opacity: 0.45; }
  /* override the graph's global svg rule (100vw/100vh, grab cursor, transition) */
  .detail-divider svg { display: block; width: 100%; height: 24px; cursor: auto; transition: none; }
  .g-canvas { position: relative; }
  .g-item { position: absolute; top: 0; left: 0; margin: 0; }
  .g-body { transition: opacity 0.7s ease, transform 0.9s cubic-bezier(0.22, 1, 0.36, 1); }
  .g-body.pending { opacity: 0; transform: translateY(40px); }
  .g-frame { position: relative; overflow: hidden; background: var(--g-chip); }
  .g-frame img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; display: block; }
  /* sharp copy layered over the blurry inline thumbnail; fades in once loaded */
  .g-frame img.detail-sharp { opacity: 0; transition: opacity 0.35s ease; }
  .g-frame img.detail-sharp.loaded { opacity: 1; }
  .g-cap { padding-top: 8px; font-size: 13px; line-height: 18px; color: var(--ink); }
  .g-cap-title { font-weight: 500; letter-spacing: -0.1px; }
  .g-cap-line { color: var(--ink-muted); font-size: 12px; line-height: 17px; }
  .g-cap-more { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
    opacity: 0; transform: translateY(-3px); transition: opacity 0.25s ease, transform 0.25s ease; }
  .g-item:hover .g-cap-more { opacity: 1; transform: none; }
  .g-palette { display: inline-flex; gap: 3px; }
  .g-palette span { width: 10px; height: 10px; border-radius: 2px; }
  /* touch screens have no hover — show everything */
  @media (hover: none) { .g-cap-more { opacity: 1; transform: none; } }

  /* single column on narrow screens: normal flow, full width, captions on */
  .g-canvas.stack .g-item { position: relative; width: auto !important; left: auto !important;
    top: auto !important; margin-bottom: 40px; }
  .g-canvas.stack .g-cap-more { opacity: 1; transform: none; }
  @media (max-width: 700px) {
    #detail-header { padding: 64px 16px 16px; }
    #detail-back { left: 16px; }
    #detail-grid { padding: 16px 16px 80px; }
  }
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
    <button id="detail-back" aria-label="Back"><svg width="16" height="16" viewBox="0 0 16 16" fill="none"
      stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M13 8H3M7.5 3.5 3 8l4.5 4.5"/></svg></button>
    <div id="detail-title"></div>
    <div id="detail-title-space"></div>
    <div id="view-toggle" class="seg-toggle">
      <div class="seg-toggle-pill"></div>
      <button type="button" data-mode="flat" class="active">All</button>
      <button type="button" data-mode="location">By Location</button>
    </div>
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
    }
    n.thumbs = thumbs;

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
  // offsetLeft and the pill's absolute `left` are both measured from the
  // container's padding edge, so no padding correction is needed
  const left = activeBtn.offsetLeft;
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

// two detail-page view modes: 'flat' (one gallery) and 'location' (photos
// split into a section per city). Lives inside the
// detail header now — filters/regroups the currently open group in place
// rather than touching the outer map.
let openNode = null;
let viewMode = 'flat';

// ---- detail gallery -------------------------------------------------------

function formatTakenAt(s) {
  const d = s ? new Date(s) : null;  // EXIF time has no zone -> parsed as local, as shot
  if (!d || isNaN(d)) return null;
  return d.toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' }) +
    ', ' + d.toLocaleTimeString('en-AU', { hour: 'numeric', minute: '2-digit' });
}

function formatCamera(c) {
  if (!c) return null;
  const parts = [];
  if (c.model) parts.push(c.model);
  if (c.focal35) parts.push(`${Math.round(c.focal35)}mm`);
  if (c.fnumber) parts.push(`f/${+c.fnumber.toFixed(1)}`);
  if (c.exposure) parts.push(c.exposure >= 1 ? `${+c.exposure.toFixed(1)}s` : `1/${Math.round(1 / c.exposure)}s`);
  if (c.iso) parts.push(`ISO ${Math.round(c.iso)}`);
  return parts.join(' · ') || null;
}

function makeTile(p) {
  const tile = document.createElement('figure');
  tile.className = 'g-item';
  tile.dataset.city = p.city || '';
  tile.dataset.aspect = p.aspect || 0.75;

  const body = document.createElement('div');
  // born hidden: layout measures tiles before armReveal runs, so adding
  // 'pending' later would animate a visible photo *out* first
  body.className = 'g-body pending';
  const frame = document.createElement('div');
  frame.className = 'g-frame';
  frame.style.aspectRatio = p.aspect || 0.75;
  const img = document.createElement('img');
  img.src = p.thumbnail;
  img.alt = '';
  frame.appendChild(img);
  // the inline thumbnail is a placeholder; the full-size display copy loads
  // behind it and fades in on top
  if (p.display) {
    const sharp = document.createElement('img');
    sharp.className = 'detail-sharp';
    sharp.loading = 'lazy';
    sharp.decoding = 'async';
    sharp.alt = '';
    sharp.addEventListener('load', () => sharp.classList.add('loaded'));
    sharp.src = p.display;
    frame.appendChild(sharp);
  }

  // caption: place + time always; camera, palette and filename on hover
  // (always on touch / single-column, see CSS)
  const cap = document.createElement('figcaption');
  cap.className = 'g-cap';
  const title = document.createElement('div');
  title.className = 'g-cap-title';
  title.textContent = p.city || 'Unknown location';
  cap.appendChild(title);
  const when = formatTakenAt(p.taken_at);
  if (when) {
    const line = document.createElement('div');
    line.className = 'g-cap-line';
    line.textContent = when;
    cap.appendChild(line);
  }
  const more = document.createElement('div');
  more.className = 'g-cap-more';
  const cameraText = formatCamera(p.camera);
  if (cameraText) {
    const cam = document.createElement('span');
    cam.className = 'g-cap-line';
    cam.textContent = cameraText;
    more.appendChild(cam);
  }
  if (p.palette && p.palette.length) {
    const pal = document.createElement('span');
    pal.className = 'g-palette';
    for (const hex of p.palette) {
      const sw = document.createElement('span');
      sw.style.background = hex;
      sw.title = hex;
      pal.appendChild(sw);
    }
    more.appendChild(pal);
  }
  const file = document.createElement('span');
  file.className = 'g-cap-line';
  file.textContent = p.path.split('/').pop();
  more.appendChild(file);
  cap.appendChild(more);

  body.appendChild(frame);
  body.appendChild(cap);
  tile.appendChild(body);
  return tile;
}

// Scatter layout: 12-column grid, each photo gets a span (size) and a zone
// (left / centre / right…) from short repeating patterns, then drops to the
// lowest y that clears everything already placed in its columns ("skyline")
// AND sits a staggered step below the previous photo, so the page reads top
// to bottom while photos zig-zag across it. Deterministic per group (seed),
// so a resize or filter change re-flows the same composition.
const GALLERY_COLS = 12;
const GALLERY_GUTTER = 24;
const GALLERY_STACK_BELOW = 700;        // px canvas width -> single column
const GALLERY_SPANS = [3, 2, 4, 2, 3, 2, 3, 4, 2, 3];
const GALLERY_ZONES = [0.02, 0.5, 0.98, 0.3, 0.75, 0.1, 0.6, 0.9, 0.4, 0.2];

function layoutScatter(canvas, items, seed) {
  const W = canvas.clientWidth;
  if (W < GALLERY_STACK_BELOW) {
    canvas.classList.add('stack');
    canvas.style.height = '';
    return;
  }
  canvas.classList.remove('stack');
  const g = GALLERY_GUTTER, cols = GALLERY_COLS;
  const colW = (W - g * (cols - 1)) / cols;
  // tall phone portraits (9:16) would overrun the screen at the bigger spans
  const maxH = Math.max(320, detail.clientHeight * 0.68);
  const sky = new Array(cols).fill(0);
  let lastY = -Infinity;
  items.forEach((el, i) => {
    const aspect = +el.dataset.aspect || 0.75;
    let span = GALLERY_SPANS[(i + seed) % GALLERY_SPANS.length];
    if (aspect > 1.2) span = Math.min(span + 2, 6);  // landscapes need width to read
    const zone = GALLERY_ZONES[(i + seed * 3) % GALLERY_ZONES.length];
    const start = Math.round(zone * (cols - span));
    const spanW = span * colW + (span - 1) * g;
    const w = Math.min(spanW, maxH * aspect);
    el.style.width = w + 'px';
    const h = el.offsetHeight;
    const r = rnd(seed * 101 + i * 7.3);
    const clear = Math.max(...sky.slice(start, start + span));
    const y = i === 0 ? 0 : Math.max(clear + 48 + r * 120, lastY + 80 + r * 140);
    // a height-capped photo hugs the outer edge of its span (left half of the
    // page -> left, right half -> right) so the zig-zag stays wide
    const x = start * (colW + g) + (zone > 0.5 ? spanW - w : 0);
    el.style.left = x + 'px';
    el.style.top = y + 'px';
    for (let c = start; c < start + span; c++) sky[c] = y + h;
    lastY = y;
  });
  canvas.style.height = Math.max(...sky) + 'px';
}

// Few photos: one centred row sized to fill the viewport — no scroll path.
function layoutFit(canvas, items) {
  canvas.classList.remove('stack');
  const W = canvas.clientWidth;
  const gap = W < GALLERY_STACK_BELOW ? 12 : 32;
  const header = document.getElementById('detail-header');
  const availH = Math.max(240, detail.clientHeight - header.offsetHeight - 48);
  const aspects = items.map(el => +el.dataset.aspect || 0.75);
  const sumA = aspects.reduce((a, b) => a + b, 0);
  const rowW = W - gap * (items.length - 1);
  // two passes: size the row, then re-fit once the real caption height is known
  let capH = 60, h = 0;
  for (let pass = 0; pass < 2; pass++) {
    h = Math.min((availH - capH) * 0.86, rowW / sumA);
    items.forEach((el, i) => { el.style.width = (aspects[i] * h) + 'px'; });
    capH = Math.max(...items.map(el => el.offsetHeight)) - h;
  }
  const totalW = aspects.reduce((s, a) => s + a * h, 0) + gap * (items.length - 1);
  let x = (W - totalW) / 2;
  const y = Math.max(0, (availH - (h + capH)) / 2);
  items.forEach((el, i) => {
    el.style.left = x + 'px';
    el.style.top = y + 'px';
    x += aspects[i] * h + gap;
  });
  canvas.style.height = availH + 'px';
}

let galleryLayouts = [];  // [{ canvas, items, seed, fit }] for the open group

function runGalleryLayouts() {
  for (const L of galleryLayouts) {
    if (L.fit) layoutFit(L.canvas, L.items);
    else layoutScatter(L.canvas, L.items, L.seed);
  }
}

// Every photo starts hidden ('.pending': faded + dropped 40px). Ones already
// on screen rise in one at a time, top to bottom, after `startDelay` (opening
// waits for the coloured page to finish fading in); the rest rise in as they
// scroll into view.
const REVEAL_STAGGER = 140;   // ms between on-screen photos
const OPEN_REVEAL_DELAY = 450; // ≈ #detail's 0.42s opacity transition
let revealGeneration = 0;      // stale staggered timers (re-open/re-layout) no-op

const revealObserver = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    e.target.classList.remove('pending');
    revealObserver.unobserve(e.target);
  }
}, { root: document.getElementById('detail'), rootMargin: '0px 0px -6% 0px' });

function armReveal(startDelay = 0) {
  revealObserver.disconnect();
  const gen = ++revealGeneration;
  const fold = detail.clientHeight;
  const onScreen = [];
  for (const L of galleryLayouts) {
    for (const el of L.items) {
      const body = el.firstChild;
      body.classList.add('pending');
      const top = el.getBoundingClientRect().top;
      if (top < fold) onScreen.push({ body, top });
      else revealObserver.observe(body);
    }
  }
  onScreen.sort((a, b) => a.top - b.top).forEach(({ body }, i) => {
    setTimeout(() => {
      if (gen === revealGeneration) body.classList.remove('pending');
    }, startDelay + i * REVEAL_STAGGER);
  });
}

let galleryResizeTimer = null;
window.addEventListener('resize', () => {
  clearTimeout(galleryResizeTimer);
  galleryResizeTimer = setTimeout(() => { if (openNode) runGalleryLayouts(); }, 120);
});

function newCanvas(parent) {
  const canvas = document.createElement('div');
  canvas.className = 'g-canvas';
  parent.appendChild(canvas);
  return canvas;
}

// Hand-drawn rule between By Location sections: a gentle slant across the
// width, a slow drift and a faint hand tremor — a line someone tried to draw
// straight — plus a little jitter, smoothed through
// quadratic midpoints. Seeded, so each divider keeps its own shape across
// re-renders. Stretched to the page width; the stroke stays 1.5px thanks to
// non-scaling-stroke.
function wobblyDivider(seed) {
  const W = 1000, H = 24, mid = H / 2, step = 25;
  const slant = (rnd(seed) - 0.5) * 8;             // end-to-end tilt, ±4 units
  const a1 = 1.2 + rnd(seed + 1) * 1.4, f1 = 0.003 + rnd(seed + 2) * 0.004, p1 = rnd(seed + 3) * 6.28;
  const a2 = 0.25 + rnd(seed + 4) * 0.35, f2 = 0.04 + rnd(seed + 5) * 0.03, p2 = rnd(seed + 6) * 6.28;
  const pts = [];
  for (let x = 0; x <= W; x += step) {
    const y = mid + slant * (x / W - 0.5) + a1 * Math.sin(x * f1 + p1) + a2 * Math.sin(x * f2 + p2) +
      (rnd(seed * 7 + x) - 0.5) * 0.5;
    pts.push([x, y]);
  }
  let d = `M${pts[0][0]},${pts[0][1].toFixed(2)}`;
  for (let i = 1; i < pts.length - 1; i++) {
    const [x, y] = pts[i], [nx, ny] = pts[i + 1];
    d += ` Q${x},${y.toFixed(2)} ${(x + nx) / 2},${((y + ny) / 2).toFixed(2)}`;
  }
  const last = pts[pts.length - 1];
  d += ` T${last[0]},${last[1].toFixed(2)}`;

  const wrap = document.createElement('div');
  wrap.className = 'detail-divider';
  wrap.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">` +
    `<path d="${d}" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" ` +
    `vector-effect="non-scaling-stroke"/></svg>`;
  return wrap;
}

// builds the gallery for the open node under the current viewMode, lays it
// out, and arms the one-at-a-time reveal (after `revealDelay` ms)
function buildDetailGrid(n, revealDelay = 0) {
  detailGrid.innerHTML = '';
  detail.scrollTop = 0;
  galleryLayouts = [];
  const seed = (n.id || 0) + 1;
  const narrow = detailGrid.clientWidth - 48 < GALLERY_STACK_BELOW;

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
    keys.forEach((key, si) => {
      const photos = groups.get(key);
      if (si > 0) detailGrid.appendChild(wobblyDivider(seed * 13 + si));
      const section = document.createElement('div');
      section.className = 'detail-group';
      const heading = document.createElement('div');
      heading.className = 'detail-group-heading';
      heading.textContent = key;
      const count = document.createElement('span');
      count.className = 'detail-group-count';
      count.textContent = photos.length;
      heading.appendChild(count);
      section.appendChild(heading);
      detailGrid.appendChild(section);
      const canvas = newCanvas(section);
      const items = photos.map(p => {
        const tile = makeTile(p);
        canvas.appendChild(tile);
        return tile;
      });
      galleryLayouts.push({ canvas, items, seed: seed + si * 3, fit: false });
    });
  } else {
    detailGrid.classList.remove('location-mode');
    const ordered = n.photos;
    const canvas = newCanvas(detailGrid);
    const items = ordered.map(p => {
      const tile = makeTile(p);
      canvas.appendChild(tile);
      return tile;
    });
    const fit = ordered.length <= (narrow ? 2 : 4);
    galleryLayouts.push({ canvas, items, seed, fit });
  }
  detailGrid.classList.toggle('fit-mode', galleryLayouts.some(L => L.fit));
  runGalleryLayouts();
  armReveal(revealDelay);
}

// rebuilds the open group's grid in place (view-mode toggle) — a quick
// crossfade, then the photos rise in one at a time again
function refreshOpenGroup() {
  if (!openNode) return;
  const n = openNode;
  detailGrid.style.opacity = '0';
  setTimeout(() => {
    buildDetailGrid(n);
    detailGrid.style.opacity = '1';
  }, 120);
}

const viewToggle = document.getElementById('view-toggle');
const viewToggleButtons = document.querySelectorAll('#view-toggle button');
function setViewMode(mode) {
  if (viewMode === mode) return;
  viewMode = mode;
  viewToggleButtons.forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
  positionPill(viewToggle);
  refreshOpenGroup();
}
viewToggleButtons.forEach(b => b.addEventListener('click', () => setViewMode(b.dataset.mode)));
positionPill(viewToggle, false);

const detail = document.getElementById('detail');
const detailGrid = document.getElementById('detail-grid');

// WCAG relative luminance -> pick whichever of white/near-black ink has the
// higher contrast against the group's hex, and derive the controls from it
function applyGalleryTheme(hex) {
  const lin = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const h = hex.replace('#', '');
  const L = 0.2126 * lin(parseInt(h.slice(0, 2), 16)) +
            0.7152 * lin(parseInt(h.slice(2, 4), 16)) +
            0.0722 * lin(parseInt(h.slice(4, 6), 16));
  const darkInk = (L + 0.05) / 0.05 > 1.05 / (L + 0.05);
  const s = detail.style;
  s.setProperty('--g-bg', hex);
  s.setProperty('--g-ink', darkInk ? 'rgba(0,0,0,0.88)' : 'rgba(255,255,255,0.95)');
  s.setProperty('--g-muted', darkInk ? 'rgba(0,0,0,0.58)' : 'rgba(255,255,255,0.7)');
  s.setProperty('--g-chip', darkInk ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.16)');
  s.setProperty('--g-tab', darkInk ? 'rgba(0,0,0,0.1)' : 'rgba(255,255,255,0.2)');
}

// Shrinking, pinning title. It's position:fixed, so its on-screen top is set
// directly from scrollTop: eased from its header slot (#detail-title-space) to
// level with the back button over
// PARALLAX x that distance of scroll (so it drifts up slower than the photos),
// scaling down to TITLE_PINNED_PX on the way, then hold it there.
const detailTitle = document.getElementById('detail-title');
const TITLE_BAR_CENTRE = 36;   // matches the back button's centre (18 + 36/2)
const TITLE_PARALLAX = 1.6;
let titleMetrics = null;

const detailTitleSpace = document.getElementById('detail-title-space');

function measureDetailTitle() {
  const fontPx = parseFloat(getComputedStyle(detailTitle).fontSize);
  const pinnedPx = window.innerWidth < GALLERY_STACK_BELOW ? 22 : 28;
  const h = detailTitle.offsetHeight;
  detailTitleSpace.style.height = h + 'px';
  titleMetrics = { top: detailTitleSpace.offsetTop, h, s: Math.min(1, pinnedPx / fontPx) };
  updateDetailTitle();
}

function updateDetailTitle() {
  if (!titleMetrics) return;
  const { top, h, s: sMin } = titleMetrics;
  const pinnedTop = TITLE_BAR_CENTRE - (h * sMin) / 2;
  const range = Math.max(1, (top - pinnedTop) * TITLE_PARALLAX);
  const st = detail.scrollTop;
  const t = Math.min(1, Math.max(0, st / range));
  const scale = 1 + (sMin - 1) * t;
  const visualTop = top + (pinnedTop - top) * t;
  detailTitle.style.transform = `translateY(${visualTop}px) scale(${scale})`;
}

let titleFrame = null;
detail.addEventListener('scroll', () => {
  if (titleFrame) return;
  titleFrame = requestAnimationFrame(() => { titleFrame = null; updateDetailTitle(); });
}, { passive: true });
window.addEventListener('resize', () => { if (openNode) measureDetailTitle(); });

function openDetail(n) {
  openNode = n;
  const nodeX = n.x, nodeY = n.y;

  // opened from the Locations map the group is already a single city, so the
  // All / By Location tabs have nothing to split — hide them, force 'flat'
  const fromLocations = graphMode === 'location';
  viewToggle.style.display = fromLocations ? 'none' : '';
  if (fromLocations) viewMode = 'flat';
  viewToggleButtons.forEach(b => b.classList.toggle('active', b.dataset.mode === viewMode));
  if (!fromLocations) positionPill(viewToggle, false);

  applyGalleryTheme(n.centroid_hex);
  detailTitle.textContent = n.label;

  detailGrid.style.opacity = '1';
  // every photo starts hidden; once the coloured page has faded in they rise
  // in one at a time (see armReveal)
  buildDetailGrid(n, OPEN_REVEAL_DELAY);
  measureDetailTitle();

  // "fly into the node": the whole graph scales up toward the clicked node
  // and fades while the coloured page fades in over it
  svg.style.transformOrigin = nodeX + 'px ' + nodeY + 'px';
  svg.style.transform = 'scale(2.6)';
  svg.style.opacity = '0';
  svg.style.pointerEvents = 'none';
  detail.classList.add('open');
  detail.scrollTop = 0;
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
