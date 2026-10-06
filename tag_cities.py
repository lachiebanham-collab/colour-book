#!/usr/bin/env python3
"""
Generates a self-contained HTML tool for manually tagging each photo with the
city it was taken in — a fallback for when GPS EXIF isn't recoverable.

Photos are sorted by capture time and grouped into "sessions" (a run of shots
with no gap longer than --gap-hours between them, default 4h). In practice a
session is usually a single city/day, so you tag ~15-25 session cards instead
of 141 individual photos. Each card shows every photo in that session; one
city text field applies to the whole group.

Progress auto-saves to the browser's localStorage as you type. The "Export
tags" button downloads a flat {photo_path: city} JSON — hand that back and
the colour-map pipeline can pick it up (e.g. to label nodes by city, or filter
the diagram per city). "Load tags" re-imports a previously exported file if
you're resuming on a different day or after clearing browser data.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_GAP_HOURS = 4

TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Tag Cities — __TOTAL__ photos, __SESSIONS__ sessions</title>
<style>
  :root {
    --bg: #f5f5f4; --panel: #ffffff; --ink: #1a1a1a; --ink-muted: #6b6b6b;
    --border: rgba(0,0,0,0.08); --accent: #2563eb;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #15151a; --panel: #202027; --ink: #ededee; --ink-muted: #9a9aa2;
      --border: rgba(255,255,255,0.10); --accent: #5b9dff;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif; }
  #topbar { position: sticky; top: 0; z-index: 10; background: var(--panel);
    border-bottom: 1px solid var(--border); padding: 14px 24px; display: flex;
    align-items: center; gap: 14px; flex-wrap: wrap; }
  #topbar h1 { font-size: 16px; font-weight: 600; margin: 0; flex: none; }
  #topbar .status { font-size: 12px; color: var(--ink-muted); }
  #topbar .spacer { flex: 1; }
  button { font: inherit; font-size: 13px; font-weight: 500; border: none; border-radius: 8px;
    padding: 8px 14px; cursor: pointer; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-secondary { background: var(--bg); color: var(--ink); border: 1px solid var(--border); }
  #sessions { padding: 20px 24px 80px; display: flex; flex-direction: column; gap: 16px; max-width: 1100px; margin: 0 auto; }
  .session { background: var(--panel); border-radius: 16px; padding: 16px; border: 1px solid var(--border); }
  .session.tagged { border-color: var(--accent); }
  .session-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
  .session-range { font-size: 13px; color: var(--ink-muted); }
  .session-count { font-size: 12px; color: var(--ink-muted); }
  .session input[type=text] { font: inherit; font-size: 15px; padding: 8px 12px; border-radius: 8px;
    border: 1px solid var(--border); background: var(--bg); color: var(--ink); width: 220px; }
  .session input[type=text]:focus { outline: 2px solid var(--accent); outline-offset: -1px; }
  .thumb-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(88px, 1fr)); gap: 6px; }
  .thumb { aspect-ratio: 1; border-radius: 8px; overflow: hidden; background: var(--bg); }
  .thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
</style>
</head>
<body>
<div id="topbar">
  <h1>Tag Cities</h1>
  <div class="status" id="status">__TOTAL__ photos · __SESSIONS__ sessions</div>
  <div class="spacer"></div>
  <input type="file" id="load-input" accept="application/json" style="display:none">
  <button class="btn-secondary" id="clear-btn">Clear all</button>
  <button class="btn-secondary" id="load-btn">Load tags</button>
  <button class="btn-primary" id="export-btn">Export tags</button>
</div>
<div id="sessions"></div>

<datalist id="city-suggestions"></datalist>

<script id="session-data" type="application/json">__DATA__</script>
<script>
const sessions = JSON.parse(document.getElementById('session-data').textContent);
const container = document.getElementById('sessions');
const STORAGE_KEY = 'colourbook-city-tags-v1';

function loadSaved() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch { return {}; }
}
let saved = loadSaved(); // { sessionId: city }

function refreshSuggestions() {
  const dl = document.getElementById('city-suggestions');
  const cities = new Set(Object.values(saved).filter(Boolean));
  dl.innerHTML = '';
  for (const c of cities) {
    const opt = document.createElement('option');
    opt.value = c;
    dl.appendChild(opt);
  }
}

function updateStatus() {
  const tagged = sessions.filter(s => saved[s.id]).length;
  document.getElementById('status').textContent =
    `__TOTAL__ photos · __SESSIONS__ sessions · ${tagged}/${sessions.length} tagged`;
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(saved));
  refreshSuggestions();
  updateStatus();
}

for (const s of sessions) {
  const card = document.createElement('div');
  card.className = 'session';
  card.dataset.id = s.id;

  const head = document.createElement('div');
  head.className = 'session-head';

  const input = document.createElement('input');
  input.type = 'text';
  input.placeholder = 'City…';
  input.autocomplete = 'off';
  input.setAttribute('list', 'city-suggestions');
  input.value = saved[s.id] || '';
  if (input.value) card.classList.add('tagged');
  input.addEventListener('input', () => {
    saved[s.id] = input.value.trim();
    card.classList.toggle('tagged', !!saved[s.id]);
    persist();
  });

  const range = document.createElement('div');
  range.className = 'session-range';
  range.textContent = s.range;
  const count = document.createElement('div');
  count.className = 'session-count';
  count.textContent = s.photos.length + (s.photos.length === 1 ? ' photo' : ' photos');

  head.appendChild(input);
  head.appendChild(range);
  head.appendChild(count);
  card.appendChild(head);

  const grid = document.createElement('div');
  grid.className = 'thumb-grid';
  for (const p of s.photos) {
    const t = document.createElement('div');
    t.className = 'thumb';
    const img = document.createElement('img');
    img.src = p.thumbnail;
    img.loading = 'lazy';
    t.appendChild(img);
    grid.appendChild(t);
  }
  card.appendChild(grid);

  container.appendChild(card);
}

refreshSuggestions();
updateStatus();

document.getElementById('export-btn').addEventListener('click', () => {
  const flat = {};
  for (const s of sessions) {
    const city = saved[s.id];
    if (!city) continue;
    for (const p of s.photos) flat[p.path] = city;
  }
  const blob = new Blob([JSON.stringify(flat, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'city_tags.json';
  a.click();
});

document.getElementById('clear-btn').addEventListener('click', () => {
  if (!confirm('Clear all tagged cities? This cannot be undone.')) return;
  saved = {};
  persist();
  for (const s of sessions) {
    const card = container.querySelector(`[data-id="${s.id}"]`);
    card.querySelector('input').value = '';
    card.classList.remove('tagged');
  }
});

document.getElementById('load-btn').addEventListener('click', () => {
  document.getElementById('load-input').click();
});
document.getElementById('load-input').addEventListener('change', (ev) => {
  const file = ev.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    let flat;
    try { flat = JSON.parse(reader.result); } catch { alert('Could not parse that file as JSON.'); return; }
    // flat is {photo_path: city} — derive a per-session city as the mode of its photos' tags
    for (const s of sessions) {
      const counts = {};
      for (const p of s.photos) {
        const c = flat[p.path];
        if (c) counts[c] = (counts[c] || 0) + 1;
      }
      const entries = Object.entries(counts);
      if (entries.length) {
        entries.sort((a, b) => b[1] - a[1]);
        saved[s.id] = entries[0][0];
      }
    }
    persist();
    // repaint inputs
    for (const s of sessions) {
      const card = container.querySelector(`[data-id="${s.id}"]`);
      const input = card.querySelector('input');
      input.value = saved[s.id] || '';
      card.classList.toggle('tagged', !!saved[s.id]);
    }
  };
  reader.readAsText(file);
});
</script>
</body>
</html>
"""


def cluster_sessions(cache, gap_hours):
    items = []
    for key, entry in cache.items():
        taken_at = entry.get("taken_at")
        dt = None
        if taken_at:
            try:
                dt = datetime.fromisoformat(taken_at.split(".")[0])
            except ValueError:
                dt = None
        items.append((dt, key, entry))

    # known-time photos sorted chronologically; unknown-time photos appended, sorted by filename
    known = sorted([i for i in items if i[0] is not None], key=lambda i: i[0])
    unknown = sorted([i for i in items if i[0] is None], key=lambda i: i[1])

    sessions = []
    current = []
    gap = gap_hours * 3600

    def flush():
        if not current:
            return
        start, end = current[0][0], current[-1][0]
        if start.date() == end.date():
            range_label = f"{start.strftime('%-d %b %Y')}, {start.strftime('%-I:%M%p').lower()}–{end.strftime('%-I:%M%p').lower()}"
        else:
            range_label = f"{start.strftime('%-d %b')} – {end.strftime('%-d %b %Y')}"
        sessions.append({
            "id": f"s{len(sessions)}",
            "range": range_label,
            "photos": [
                {"path": key, "thumbnail": entry.get("thumbnail"), "hex": entry["colours"][0]["hex"]}
                for _, key, entry in current
            ],
        })

    for dt, key, entry in known:
        if current and (dt - current[-1][0]).total_seconds() > gap:
            flush()
            current = []
        current.append((dt, key, entry))
    flush()

    if unknown:
        sessions.append({
            "id": f"s{len(sessions)}",
            "range": "Unknown time",
            "photos": [
                {"path": key, "thumbnail": entry.get("thumbnail"), "hex": entry["colours"][0]["hex"]}
                for _, key, entry in unknown
            ],
        })

    return sessions


def main():
    if len(sys.argv) < 3:
        print("usage: tag_cities.py <cache_json> <output_html> [--gap-hours N]")
        sys.exit(1)

    cache_path = Path(sys.argv[1]).expanduser().resolve()
    out_path = Path(sys.argv[2]).expanduser().resolve()
    gap_hours = DEFAULT_GAP_HOURS
    if "--gap-hours" in sys.argv:
        gap_hours = float(sys.argv[sys.argv.index("--gap-hours") + 1])

    with open(cache_path) as f:
        cache = json.load(f)

    sessions = cluster_sessions(cache, gap_hours)
    total_photos = sum(len(s["photos"]) for s in sessions)

    payload = json.dumps(sessions).replace("</script>", "<\\/script>")
    html = (TEMPLATE
            .replace("__DATA__", payload)
            .replace("__TOTAL__", str(total_photos))
            .replace("__SESSIONS__", str(len(sessions))))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)

    print(f"{total_photos} photos -> {len(sessions)} sessions (gap threshold: {gap_hours}h)")
    for s in sessions:
        print(f"  {s['id']:>4}  {s['range']:<40} {len(s['photos']):>3} photos")
    print(f"Wrote {out_path} ({len(html)/1024:.0f} KB)")


if __name__ == "__main__":
    main()
