#!/usr/bin/env python3
"""
One-command pipeline: extract dominant colours (incremental) -> cluster into
colour groups -> render the node-link diagram. Re-run any time after adding
photos to the source folder; already-processed photos are skipped.

Usage:
    python3 run.py "/path/to/photos" [--groups N] [--force] [--fresh]

--fresh re-clusters from scratch instead of warm-starting from the existing
groups (which keeps groups stable as photos are added or removed).
"""
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
CACHE = PROJECT_DIR / "cache" / "colours.json"
GROUPS = PROJECT_DIR / "output" / "groups.json"
HTML = PROJECT_DIR / "output" / "colour_map.html"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    photos_dir = sys.argv[1]
    force = "--force" in sys.argv
    n_groups = None
    if "--groups" in sys.argv:
        n_groups = sys.argv[sys.argv.index("--groups") + 1]

    extract_cmd = [sys.executable, str(PROJECT_DIR / "extract_colours.py"), photos_dir, str(CACHE)]
    if force:
        extract_cmd.append("--force")
    subprocess.run(extract_cmd, check=True)

    cluster_cmd = [sys.executable, str(PROJECT_DIR / "cluster.py"), str(CACHE), str(GROUPS)]
    if n_groups:
        cluster_cmd.append(n_groups)
    if "--fresh" in sys.argv:
        cluster_cmd.append("--fresh")
    subprocess.run(cluster_cmd, check=True)

    subprocess.run([sys.executable, str(PROJECT_DIR / "visualize.py"), str(GROUPS), str(HTML)], check=True)

    print(f"\nOpen the diagram:\n  open \"{HTML}\"")


if __name__ == "__main__":
    main()
