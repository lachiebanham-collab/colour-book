#!/usr/bin/env python3
"""
Groups photos into colour clusters from the dominant-colour cache, then computes
similarity edges between clusters so related colour groups can be linked in the
node-link diagram.

Clustering runs in CIELAB space (perceptually uniform, unlike raw RGB) on each
photo's single most dominant extracted colour.
"""
import json
import sys
from pathlib import Path

import numpy as np

DEFAULT_GROUPS = 9
RESTARTS = 8
ITERATIONS = 300  # upper bound; each run stops as soon as assignments settle
DUP_HAMMING_THRESHOLD = 6  # dHash bits that may differ and still count as the same photo


def hamming(hex_a, hex_b):
    return bin(int(hex_a, 16) ^ int(hex_b, 16)).count("1")


def dedupe_keys(cache, keys):
    """Collapse duplicate photos (e.g. "IMG_1234.JPG" + "IMG_1234 2.JPG"
    export pairs) to a single representative. Two photos are the same if
    either their EXIF capture time matches to the millisecond (a crop or
    re-edit of one original — cropping changes the perceptual hash, so the
    hash alone misses these) or their perceptual hashes are near-identical.
    The tallest version wins (a 9:16 crop over the 4:3 original), then the
    shorter/plainer filename. O(n^2) but n is photo-collection-sized, so fine."""
    ordered = sorted(keys, key=lambda k: (cache[k].get("aspect") or 1.0, len(k), k))
    kept, kept_hashes, kept_times = [], [], set()
    dup_count = 0
    for k in ordered:
        h = cache[k].get("phash")
        t = cache[k].get("taken_at")
        # only sub-second timestamps are precise enough to call two files the
        # same shot; a bare "HH:MM:SS" could be a burst of different frames
        same_shot = t is not None and "." in t and t in kept_times
        if same_shot or (h is not None and any(
                kh is not None and hamming(h, kh) <= DUP_HAMMING_THRESHOLD for kh in kept_hashes)):
            dup_count += 1
            continue
        kept.append(k)
        kept_hashes.append(h)
        if t is not None:
            kept_times.add(t)
    return kept, dup_count


def srgb_to_lab(rgb):
    """rgb: (N, 3) array, 0-255 -> Lab (N, 3)."""
    rgb = rgb / 255.0
    mask = rgb > 0.04045
    rgb_lin = np.where(mask, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)

    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ])
    xyz = rgb_lin @ M.T

    white = np.array([0.95047, 1.0, 1.08883])
    xyz_n = xyz / white

    delta = 6.0 / 29.0
    mask2 = xyz_n > delta ** 3
    f = np.where(mask2, np.cbrt(xyz_n), xyz_n / (3 * delta ** 2) + 4.0 / 29.0)

    L = 116 * f[:, 1] - 16
    a = 500 * (f[:, 0] - f[:, 1])
    b = 200 * (f[:, 1] - f[:, 2])
    return np.stack([L, a, b], axis=1)


def lab_to_srgb(lab):
    """lab: (N, 3) -> rgb 0-255 (N, 3), clipped."""
    L, a, b = lab[:, 0], lab[:, 1], lab[:, 2]
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200

    delta = 6.0 / 29.0

    def finv(t):
        return np.where(t > delta, t ** 3, 3 * delta ** 2 * (t - 4.0 / 29.0))

    white = np.array([0.95047, 1.0, 1.08883])
    xyz = np.stack([finv(fx) * white[0], finv(fy) * white[1], finv(fz) * white[2]], axis=1)

    M_inv = np.array([
        [3.2404542, -1.5371385, -0.4985314],
        [-0.9692660, 1.8760108, 0.0415560],
        [0.0556434, -0.2040259, 1.0572252],
    ])
    rgb_lin = xyz @ M_inv.T
    rgb_lin = np.clip(rgb_lin, 0, 1)

    mask = rgb_lin > 0.0031308
    rgb = np.where(mask, 1.055 * (rgb_lin ** (1 / 2.4)) - 0.055, rgb_lin * 12.92)
    return np.clip(rgb * 255, 0, 255)


def kmeans(points, k, iterations=ITERATIONS, restarts=RESTARTS, seed=7, init=None):
    """Best-of-`restarts` k-means. With `init` (k starting centroids, e.g. the
    previous run's groups) it runs once from there instead: random restarts
    land in different local optima whenever the photo set changes even
    slightly, which reshuffles every group; warm-starting keeps existing groups
    and just lets them drift to absorb added/removed photos."""
    rng = np.random.default_rng(seed)
    best_inertia = None
    best_centroids = None
    best_assignments = None

    for r in range(1 if init is not None else restarts):
        if init is not None:
            centroids = np.array(init, dtype=np.float64)
        else:
            centroids = points[rng.choice(len(points), size=k, replace=False)].copy()
        assignments = None
        for _ in range(iterations):
            dists = ((points[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
            new_assignments = dists.argmin(axis=1)
            # run to convergence: stopping early left re-runs (warm-started
            # from the saved groups) still settling, so a borderline photo
            # could hop groups on a rebuild where nothing had changed
            if assignments is not None and np.array_equal(new_assignments, assignments):
                break
            assignments = new_assignments
            for i in range(k):
                members = points[assignments == i]
                if len(members) > 0:
                    centroids[i] = members.mean(axis=0)
                else:
                    centroids[i] = points[rng.integers(0, len(points))]
        dists = ((points[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
        assignments = dists.argmin(axis=1)
        inertia = dists[np.arange(len(points)), assignments].sum()
        if best_inertia is None or inertia < best_inertia:
            best_inertia = inertia
            best_centroids = centroids.copy()
            best_assignments = assignments.copy()

    return best_centroids, best_assignments


def rgb_to_hex(rgb):
    r, g, b = (int(round(c)) for c in np.clip(rgb, 0, 255))
    return f"#{r:02x}{g:02x}{b:02x}"


def main():
    if len(sys.argv) < 3:
        print("usage: cluster.py <cache_json> <groups_json> [num_groups]")
        sys.exit(1)

    cache_path = Path(sys.argv[1]).expanduser().resolve()
    groups_path = Path(sys.argv[2]).expanduser().resolve()
    n_groups = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else DEFAULT_GROUPS

    if "--cities" in sys.argv:
        cities_path = Path(sys.argv[sys.argv.index("--cities") + 1]).expanduser().resolve()
    else:
        cities_path = cache_path.parent.parent / "data" / "city_tags.json"  # project/cache/.. -> project/data/

    city_tags = {}
    if cities_path.exists():
        with open(cities_path) as f:
            city_tags = json.load(f)
        print(f"Loaded city tags for {len(city_tags)} photos from {cities_path}")

    with open(cache_path) as f:
        cache = json.load(f)

    if not cache:
        print("Cache is empty — run extract_colours.py first.")
        sys.exit(1)

    keys, dup_count = dedupe_keys(cache, list(cache.keys()))
    if dup_count:
        print(f"Skipped {dup_count} duplicate photo(s) (near-identical to one already kept)")
    dominant_rgb = np.array([cache[k]["colours"][0]["rgb"] for k in keys], dtype=np.float64)
    lab = srgb_to_lab(dominant_rgb)

    n_groups = min(n_groups, len(keys))

    # warm start from the previous groups.json when it has the same number of
    # groups (pass --fresh to re-cluster from scratch)
    init = None
    if groups_path.exists() and "--fresh" not in sys.argv:
        with open(groups_path) as f:
            prev = json.load(f).get("groups", [])
        if len(prev) == n_groups:
            prev_rgb = np.array([[int(g["centroid_hex"][i:i + 2], 16) for i in (1, 3, 5)] for g in prev],
                                dtype=np.float64)
            init = srgb_to_lab(prev_rgb)
            print(f"Warm-starting from the {n_groups} groups in {groups_path.name}")
    centroids_lab, assignments = kmeans(lab, n_groups, init=init)
    centroids_rgb = lab_to_srgb(centroids_lab)

    groups = []
    for i in range(n_groups):
        member_idx = np.where(assignments == i)[0]
        if len(member_idx) == 0:
            continue
        # order by closeness to the group's centroid, so the UI's representative
        # preview thumbnails (shown directly on the node) are the photos that
        # best embody the group's colour, not an arbitrary subset
        member_idx = sorted(
            member_idx,
            key=lambda idx: float(((lab[idx] - centroids_lab[i]) ** 2).sum()),
        )
        photos = []
        for idx in member_idx:
            k = keys[idx]
            photos.append({
                "path": k,
                "hex": cache[k]["colours"][0]["hex"],
                "thumbnail": cache[k].get("thumbnail"),
                "display": cache[k].get("display"),
                "aspect": cache[k].get("aspect"),
                "camera": cache[k].get("camera"),
                "palette": [c["hex"] for c in cache[k]["colours"]],
                "city": city_tags.get(k),
                "taken_at": cache[k].get("taken_at"),
            })
        city_counts = {}
        for p in photos:
            if p["city"]:
                city_counts[p["city"]] = city_counts.get(p["city"], 0) + 1
        cities_summary = sorted(city_counts.items(), key=lambda kv: -kv[1])

        groups.append({
            "id": len(groups),
            "centroid_hex": rgb_to_hex(centroids_rgb[i]),
            "centroid_lab": centroids_lab[i].tolist(),
            "count": len(photos),
            "photos": photos,
            "cities": [{"city": c, "count": n} for c, n in cities_summary],
        })

    # order groups by hue-ish for a nicer default layout (by Lab a/b angle)
    groups.sort(key=lambda g: -g["count"])
    # re-assign ids to match this final array order — edges below are built from
    # array indices, and must line up with the "id" each group is shipped under
    for new_id, g in enumerate(groups):
        g["id"] = new_id

    # inter-group similarity edges: connect each group to its nearest neighbours
    centroid_arr = np.array([g["centroid_lab"] for g in groups])
    n = len(groups)
    dist_matrix = np.sqrt(((centroid_arr[:, None, :] - centroid_arr[None, :, :]) ** 2).sum(axis=2))
    np.fill_diagonal(dist_matrix, np.inf)

    max_dist = np.nanmax(dist_matrix[np.isfinite(dist_matrix)]) if n > 1 else 1.0
    neighbours_per_node = 2
    edges = []
    seen = set()
    for i in range(n):
        nearest = np.argsort(dist_matrix[i])[:neighbours_per_node]
        for j in nearest:
            j = int(j)
            if j == i:
                continue
            pair = tuple(sorted((i, j)))
            if pair in seen:
                continue
            seen.add(pair)
            d = dist_matrix[i, j]
            similarity = 1.0 - min(d / max_dist, 1.0)
            edges.append({"source": pair[0], "target": pair[1], "similarity": round(float(similarity), 4)})

    output = {
        "groups": [
            {
                "id": g["id"],
                "centroid_hex": g["centroid_hex"],
                "count": g["count"],
                "photos": g["photos"],
                "cities": g["cities"],
            }
            for g in groups
        ],
        "edges": edges,
    }

    groups_path.parent.mkdir(parents=True, exist_ok=True)
    with open(groups_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"{len(keys)} photos -> {len(groups)} colour groups, {len(edges)} edges")
    for g in groups:
        print(f"  group {g['id']:>2}  {g['centroid_hex']}  {g['count']:>3} photos")
    print(f"Written to {groups_path}")


if __name__ == "__main__":
    main()
