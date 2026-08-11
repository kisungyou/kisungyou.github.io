#!/usr/bin/env python3
"""Stage the existing personal site for a combined Pages deployment."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PY_SHT_SITEMAP = "Sitemap: https://www.kisungyou.com/pysht/sitemap.xml"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("personal_site", type=Path, help="tracked personal-site docs")
    parser.add_argument("artifact", type=Path, help="new combined Pages directory")
    args = parser.parse_args()

    source_root = args.personal_site.resolve(strict=True)
    site_root = args.artifact.resolve(strict=False)
    if site_root.exists():
        parser.error(f"artifact directory already exists: {site_root}")
    if "pysht" in {path.name for path in source_root.iterdir()}:
        parser.error(
            "docs/pysht is generated during deployment and must not be committed"
        )

    shutil.copytree(source_root, site_root)
    (site_root / "CNAME").unlink(missing_ok=True)

    robots = site_root / "robots.txt"
    robot_lines = robots.read_text(encoding="utf-8").splitlines()
    if PY_SHT_SITEMAP not in robot_lines:
        robot_lines.append(PY_SHT_SITEMAP)
    robots.write_text("\n".join(robot_lines) + "\n", encoding="utf-8")
    (site_root / ".nojekyll").touch()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
