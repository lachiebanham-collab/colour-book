# colour-book

Groups a folder of photos into recurring colour themes, for laying out a
photography book (or any project) by colour rather than by place or date.
Same dominant-colour-extraction idea as the Tone app's `ColourExtractor` —
resize → drop near-white/near-black pixels → k-means cluster — reused here
for your own photos instead of matching against Sanzo Wada combinations.

## Usage

```bash
python3 run.py "/path/to/photos" --groups 9
open output/colour_map.html
```

Processing is local — no uploads, no network calls. Small thumbnails for the
map are inlined as base64 in the HTML; sharp 1600px copies for the detail
gallery are written to `output/photos/`, so keep that folder next to
`colour_map.html` when moving or hosting it.

**Adding more photos later**: drop new files into the same folder and re-run
the same command. `extract_colours.py` fingerprints each file by mtime+size
and only processes what's new — it won't recompute colours for photos it's
already seen. Deleted photos are dropped from the cache automatically.

`--groups N` controls how many colour themes to split into (default 9).
Re-running with a different N just re-clusters the existing cache — fast,
since extraction (the slow part) is skipped.

**Stable groups**: re-runs warm-start the clustering from the existing
`output/groups.json` (same N), so adding or removing a few photos nudges the
groups rather than reshuffling them. Pass `--fresh` to re-cluster from scratch.

**Leaving a photo out**: add its filename to `data/excluded.json` (e.g.
`["IMG_7578.JPG"]`) and re-run. The original stays in your photos folder; it's
dropped from the cache, the map and `output/photos/`.

## Pipeline

1. **`extract_colours.py`** — per-photo colour via k-means (k=5, 10
   iterations) on sampled pixels, mirroring `ColourExtractor.swift`'s
   resize/filter/cluster approach. Clusters are then ranked by **saturation**,
   not pixel count (`saturation × 0.75 + brightness × 0.25`, with a noise-floor
   weight and dull/near-black/near-white filters) — a small vivid subject
   (a red door, a teal shutter) wins over a large grey wall or sky behind it.
   Also computes a perceptual hash (dHash) per photo for duplicate detection.
   Reads EXIF date + camera settings (model, 35mm-equivalent focal length,
   aperture, shutter, ISO) and the photo's aspect ratio. Caches everything +
   an inlined thumbnail in `cache/colours.json`, and writes a 1600px display
   copy to `output/photos/`.
2. **`cluster.py`** — first **dedupes** near-identical photos (e.g. a
   `"IMG_1234.JPG"` + `"IMG_1234 2.JPG"` export pair) by comparing perceptual
   hashes, so duplicates don't inflate a group's count or clutter its preview.
   Takes each remaining photo's saturation-ranked colour, converts to CIELAB
   (perceptually uniform), k-means clusters into N colour groups, orders each
   group's photos by closeness to the centroid (most representative first),
   and computes similarity edges between group centroids. Writes
   `output/groups.json`.
3. **`visualize.py`** — renders `output/colour_map.html`: a force-directed
   node-link diagram. Each node is a golden-angle-packed cluster of square
   photo thumbnails (not a flat colour circle) — bigger tiles are closer
   colour matches, the best match sits centred and largest. Edges = colour
   similarity between groups. Click a node to zoom into a full-screen
   gallery of every photo in the group: an editorial scatter (natural aspect
   ratios, mixed sizes, staggered across a 12-column grid, fading in as you
   scroll) with place + time captions, and camera settings, palette and
   filename on hover. Under 700px wide it's a single column with everything
   shown; groups of ≤4 photos (≤2 on a phone) fit one row with no scroll. The page ground takes the group's own colour,
   with its hex as a large DotGothic heading and an All / By Location toggle
   (per-city sections, from `data/city_tags.json`, each headed by the city in
   translucent DotGothic and separated by a hand-drawn wobbly rule) beneath. Vanilla JS, no
   CDN/network dependency.

## City tagging (optional)

Photos don't reliably carry GPS EXIF (stripped by Lightroom export, iOS share
sheets, etc. — check with `exiftool -gpsposition photo.jpg` if you're not
sure). `tag_cities.py` is a manual fallback: a local tagging tool, not an
automated one — nothing in this script analyses image content or calls out
to any service.

```bash
python3 tag_cities.py cache/colours.json output/city_tagger.html
open output/city_tagger.html
```

It groups photos into time-based "sessions" (no gap > 4h by default —
`--gap-hours N` to adjust) so you're typically tagging ~15–25 session cards
instead of every individual photo; one city field applies to a whole session.
Progress auto-saves to the browser's localStorage as you type. "Export tags"
downloads a flat `{photo_path: city}` JSON — save it as `data/city_tags.json`
in this project and re-run `cluster.py` to pick it up.

**Be careful with AI-assisted browsers.** If your browser has an agentic
AI feature (Gemini-in-Chrome or similar), it can silently auto-fill empty
form fields by analysing on-page images — including firing off real web
searches with content inferred from your private photos, with no prompt and
no record of what it sent where. This actually happened while building this
tool. If fields fill in by themselves, don't trust it as ground truth — the
tool's "Clear all" button wipes auto-filled data so you can retype for real,
and the "City…" inputs are set `autocomplete="off"` to reduce (not
guarantee) the chance of it recurring.

## Re-theming a place

If a colour group ends up spanning more than one place and you'd rather see
groups *within* a single location, just re-run the pipeline pointed at a
subfolder for that place:

```bash
python3 run.py "/path/to/photos/Venice" --groups 5
```

(Point `--groups` lower for a single place — fewer photos, fewer natural
themes.) Each run overwrites `output/groups.json` and `colour_map.html`; copy
them elsewhere first if you want to keep a particular run's result.
