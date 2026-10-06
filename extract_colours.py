#!/usr/bin/env python3
"""
Per-photo dominant-colour extraction, mirroring the Tone app's ColourExtractor.swift:
resize small, drop near-white/near-black pixels, k-means cluster the rest. Results
are cached so re-running after adding new photos only processes what's new.

Colour selection prioritises saturation over pixel count (a small vivid awning
or door should win over a large grey wall) — the same idea as ColourExtractor's
pickVividColour, adapted for photos rather than curated colour combinations (no
hue exclusion; travel photos are full of legitimately dominant blues/greens from
sky and nature, which Tone's card-colour picker deliberately avoids).
"""
import base64
import colorsys
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import ExifTags, Image, ImageOps

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
MAX_DIM = 120
K = 5  # finer clusters than a flat dominant-colour split, so a small saturated
       # subject (e.g. a red door) forms its own cluster instead of being averaged
       # into the grey/neutral majority
ITERATIONS = 10
NEAR_WHITE_LUMINANCE = 0.95
NEAR_BLACK_LUMINANCE = 0.05
# 200px so the map's bubble thumbnails stay sharp when MAP_SCALE enlarges them
# on big/4K screens (72px read as blurry there)
THUMB_DIM = 200
THUMB_QUALITY = 70
# sharp copies for the detail view — written as files next to the HTML (not
# inlined) so the page stays light and the browser lazy-loads them per group
DISPLAY_DIM = 1600
DISPLAY_QUALITY = 82

# saturation-priority selection (mirrors ColourExtractor.pickVividColour's scoring,
# without the green/blue hue exclusion — that's specific to Tone's combination
# cards, not appropriate for photos where sky/sea/foliage are legitimately dominant)
MIN_CLUSTER_WEIGHT = 0.035  # ignore clusters under ~3.5% of sampled pixels (noise)
SAT_FLOOR = 0.18
VAL_FLOOR = 0.12
VAL_CEIL = 0.97


def luminance(rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def kmeans(pixels, k, iterations):
    rng = np.random.default_rng(42)
    if len(pixels) < k:
        k = max(1, len(pixels))
    centroids = pixels[rng.choice(len(pixels), size=k, replace=False)].astype(np.float64)
    for _ in range(iterations):
        dists = ((pixels[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        assignments = dists.argmin(axis=1)
        new_centroids = np.copy(centroids)
        for i in range(k):
            members = pixels[assignments == i]
            if len(members) > 0:
                new_centroids[i] = members.mean(axis=0)
        centroids = new_centroids
    sizes = np.array([(assignments == i).sum() for i in range(k)])
    order = np.argsort(-sizes)
    return centroids[order], sizes[order]


def order_by_vividness(centroids, sizes):
    """Return (centroids, sizes) reordered so the most saturated *qualifying*
    cluster comes first, rather than the largest-by-pixel-count one. Falls back
    gracefully (relax the weight floor, then the saturation/brightness floors,
    then just the globally most saturated) so a result is always returned."""
    total = sizes.sum()
    candidates = []
    for i, (centroid, size) in enumerate(zip(centroids, sizes)):
        r, g, b = (centroid / 255.0).clip(0, 1)
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        weight = float(size) / float(total) if total else 0.0
        candidates.append({"i": i, "sat": s, "val": v, "weight": weight})

    def vividness(c):
        return c["sat"] * 0.75 + c["val"] * 0.25

    sizeable = [c for c in candidates if c["weight"] >= MIN_CLUSTER_WEIGHT]
    pool = sizeable if sizeable else candidates

    qualifying = [c for c in pool if c["sat"] >= SAT_FLOOR and VAL_FLOOR <= c["val"] <= VAL_CEIL]
    ranked_front = qualifying if qualifying else pool

    front_idx = [c["i"] for c in sorted(ranked_front, key=vividness, reverse=True)]
    remaining_idx = [c["i"] for c in sorted(candidates, key=lambda c: -c["weight"]) if c["i"] not in front_idx]
    order = front_idx + remaining_idx

    return centroids[order], sizes[order]


def make_thumbnail(img):
    thumb = ImageOps.fit(img, (THUMB_DIM, THUMB_DIM), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    thumb.save(buf, format="JPEG", quality=THUMB_QUALITY, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def display_filename(key):
    """Flat, URL-safe-ish filename for a photo's display copy (subfolders in the
    source dir are folded into the name so copies all live in one folder)."""
    return str(Path(key).with_suffix(".jpg")).replace("/", "__")


def write_display_copy(img, out_path):
    copy = img.copy()
    copy.thumbnail((DISPLAY_DIM, DISPLAY_DIM), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    copy.save(out_path, format="JPEG", quality=DISPLAY_QUALITY, optimize=True, progressive=True)


def dhash(img, hash_size=8):
    """Difference hash — cheap perceptual fingerprint used to catch duplicate/
    near-duplicate photos (e.g. a "IMG_1234.JPG" + "IMG_1234 2.JPG" export pair)
    even when filenames differ. Returns a 64-bit hash as a hex string."""
    small = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(small, dtype=np.int16)
    diff = pixels[:, 1:] > pixels[:, :-1]
    bits = diff.flatten()
    value = 0
    for bit in bits:
        value = (value << 1) | int(bit)
    return f"{value:0{hash_size * hash_size // 4}x}"


def read_taken_at(img):
    """DateTimeOriginal (+ sub-second, when present) as a sortable ISO-ish
    string — used for session clustering in the city-tagging tool, and as a
    precise fingerprint for matching against un-edited originals elsewhere
    (e.g. to recover GPS from a separately-exported copy)."""
    try:
        exif = img._getexif()
    except Exception:
        exif = None
    if not exif:
        return None
    tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
    raw = tags.get("DateTimeOriginal") or tags.get("DateTime")
    if not raw:
        return None
    # EXIF format: "2026:07:28 13:40:19" -> "2026-07-28T13:40:19"
    try:
        date_part, time_part = raw.split(" ")
        iso = date_part.replace(":", "-") + "T" + time_part
    except ValueError:
        return None
    subsec = tags.get("SubsecTimeOriginal") or tags.get("SubsecTime")
    if subsec:
        iso += "." + str(subsec)
    return iso


def read_camera(img):
    """Camera + exposure settings for the detail gallery's captions. Values are
    plain numbers (focal length is the 35mm equivalent — "77mm" reads better
    than an iPhone's physical "9mm"). Missing tags are simply left out."""
    try:
        exif = img.getexif()
        tags = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        tags.update({ExifTags.TAGS.get(k, k): v for k, v in exif.get_ifd(0x8769).items()})
    except Exception:
        return None

    def num(v):
        if isinstance(v, (tuple, list)):
            v = v[0] if v else None
        try:
            return float(v)
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    camera = {
        "model": str(tags["Model"]).strip() if tags.get("Model") else None,
        "focal35": num(tags.get("FocalLengthIn35mmFilm")) or num(tags.get("FocalLength")),
        "fnumber": num(tags.get("FNumber")),
        "exposure": num(tags.get("ExposureTime")),
        "iso": num(tags.get("ISOSpeedRatings") or tags.get("PhotographicSensitivity")),
    }
    camera = {k: v for k, v in camera.items() if v}
    return camera or None


def extract_dominant_colours(path, display_path, k=K):
    img = Image.open(path)
    taken_at = read_taken_at(img)
    camera = read_camera(img)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    aspect = round(img.width / img.height, 4)

    write_display_copy(img, display_path)
    thumbnail_data_url = make_thumbnail(img)
    phash = dhash(img)

    img.thumbnail((MAX_DIM, MAX_DIM), Image.Resampling.LANCZOS)

    arr = np.asarray(img).reshape(-1, 3).astype(np.float64)
    norm = arr / 255.0
    lum = luminance(norm)
    mask = (lum > NEAR_BLACK_LUMINANCE) & (lum < NEAR_WHITE_LUMINANCE)
    filtered = arr[mask]
    if len(filtered) < k * 4:
        filtered = arr  # fallback: image is mostly extreme tones (e.g. B&W, snow)

    centroids, sizes = kmeans(filtered, k, ITERATIONS)
    centroids, sizes = order_by_vividness(centroids, sizes)
    total = sizes.sum()
    results = []
    for centroid, size in zip(centroids, sizes):
        r, g, b = (int(round(c)) for c in centroid.clip(0, 255))
        results.append({
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "rgb": [r, g, b],
            "weight": round(float(size) / float(total), 4) if total else 0.0,
        })
    return results, thumbnail_data_url, phash, taken_at, camera, aspect


def load_cache(cache_path):
    if cache_path.exists():
        with open(cache_path) as f:
            return json.load(f)
    return {}


def save_cache(cache_path, cache):
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2, sort_keys=True)


def main():
    if len(sys.argv) < 3:
        print("usage: extract_colours.py <photos_dir> <cache_json> [--force]")
        sys.exit(1)

    photos_dir = Path(sys.argv[1]).expanduser().resolve()
    cache_path = Path(sys.argv[2]).expanduser().resolve()
    force = "--force" in sys.argv[3:]

    cache = {} if force else load_cache(cache_path)
    # project/cache/colours.json -> project/output/photos/ (same convention as
    # cluster.py's data/ lookup); cache stores paths relative to output/
    display_dir = cache_path.parent.parent / "output" / "photos"

    # photos to leave out of the map entirely (filenames relative to the photos
    # dir, e.g. ["IMG_7578.JPG"]) — the originals are untouched, but they're
    # treated as absent, so their cache entry + display copy get cleaned up below
    excluded_path = cache_path.parent.parent / "data" / "excluded.json"
    excluded = set(json.loads(excluded_path.read_text())) if excluded_path.exists() else set()

    photo_paths = sorted(
        p for p in photos_dir.rglob("*")
        if p.suffix.lower() in IMAGE_EXTS and p.is_file()
        and str(p.relative_to(photos_dir)) not in excluded
    )
    if excluded:
        print(f"Excluding {len(excluded)} photo(s) listed in {excluded_path}")

    new_count = 0
    stale_count = 0
    backfilled_count = 0
    display_count = 0
    skipped_heic = 0
    for p in photo_paths:
        key = str(p.relative_to(photos_dir))
        stat = p.stat()
        fingerprint = f"{stat.st_mtime_ns}:{stat.st_size}"

        display_name = display_filename(key)
        display_path = display_dir / display_name

        entry = cache.get(key)
        if entry is not None and entry.get("fingerprint") == fingerprint:
            # cheap patches for entries cached before a field existed — EXIF
            # date/camera, aspect ratio, display copy — no colour recompute
            needs_display = not display_path.exists()
            needs_thumb = entry.get("thumb_dim") != THUMB_DIM
            if needs_display or needs_thumb or any(f not in entry for f in ("taken_at", "camera", "aspect")):
                try:
                    with Image.open(p) as img:
                        if "taken_at" not in entry:
                            entry["taken_at"] = read_taken_at(img)
                        if "camera" not in entry:
                            entry["camera"] = read_camera(img)
                        oriented = ImageOps.exif_transpose(img)
                        entry["aspect"] = round(oriented.width / oriented.height, 4)
                        if needs_display:
                            write_display_copy(oriented.convert("RGB"), display_path)
                            display_count += 1
                        if needs_thumb:
                            entry["thumbnail"] = make_thumbnail(oriented.convert("RGB"))
                            entry["thumb_dim"] = THUMB_DIM
                    backfilled_count += 1
                except Exception as e:
                    print(f"  ! couldn't backfill {key}: {e}")
            entry["display"] = f"photos/{display_name}"
            continue

        try:
            colours, thumbnail, phash, taken_at, camera, aspect = extract_dominant_colours(p, display_path)
        except Exception as e:
            print(f"  ! skipped {key}: {e}")
            if p.suffix.lower() in (".heic", ".heif"):
                skipped_heic += 1
            continue

        cache[key] = {
            "fingerprint": fingerprint,
            "colours": colours,
            "thumbnail": thumbnail,
            "thumb_dim": THUMB_DIM,
            "display": f"photos/{display_name}",
            "phash": phash,
            "taken_at": taken_at,
            "camera": camera,
            "aspect": aspect,
        }
        if entry is None:
            new_count += 1
        else:
            stale_count += 1

    # drop cache entries for photos that no longer exist
    live_keys = {str(p.relative_to(photos_dir)) for p in photo_paths}
    removed = [k for k in cache if k not in live_keys]
    for k in removed:
        del cache[k]
    # ...and their display copies
    live_display = {display_filename(k) for k in live_keys}
    if display_dir.exists():
        for f in display_dir.glob("*.jpg"):
            if f.name not in live_display:
                f.unlink()

    save_cache(cache_path, cache)

    print(f"Scanned {len(photo_paths)} photos in {photos_dir}")
    print(f"  new: {new_count}, updated: {stale_count}, removed: {len(removed)}, "
          f"unchanged: {len(photo_paths) - new_count - stale_count}")
    if backfilled_count:
        print(f"  backfilled missing fields for {backfilled_count} existing entries")
    if display_count:
        print(f"  wrote display copies for {display_count} existing entries")
    if skipped_heic:
        print(f"  ! {skipped_heic} HEIC/HEIF files skipped — install pillow-heif "
              f"(pip install pillow-heif) and re-run with --force to include them")
    print(f"Cache written to {cache_path} ({len(cache)} entries)")


if __name__ == "__main__":
    main()
