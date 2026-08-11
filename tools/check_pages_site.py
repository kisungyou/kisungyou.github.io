#!/usr/bin/env python3
"""Validate the combined personal website and pySHT Pages artifact."""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

PY_SHT_BASE_URL = "https://www.kisungyou.com/pysht/"
ROOT_SITEMAP = "Sitemap: https://www.kisungyou.com/sitemap.xml"
PY_SHT_SITEMAP = "Sitemap: https://www.kisungyou.com/pysht/sitemap.xml"
IGNORED_SCHEMES = {"data", "http", "https", "javascript", "mailto", "tel"}

REQUIRED_FILES = (
    "index.html",
    "software.html",
    "Teaching/note01-spherical-distance.html",
    ".nojekyll",
    "robots.txt",
    "pysht/index.html",
    "pysht/api/index.html",
    "pysht/validation/simplex-uniformity.html",
    "pysht/searchindex.js",
    "pysht/objects.inv",
    "pysht/_static/styles/theme.css",
    "pysht/_static/css/custom.css",
    "pysht/sitemap.xml",
)


class _AssetParser(HTMLParser):
    """Collect local links and assets from rendered HTML attributes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del tag
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.targets.append(value)


def _fail(message: str) -> None:
    raise ValueError(message)


def _assert_required_files(site_root: Path) -> None:
    missing = [name for name in REQUIRED_FILES if not (site_root / name).is_file()]
    if missing:
        _fail("missing required artifact files: " + ", ".join(missing))


def _assert_exact_lowercase_path(site_root: Path) -> None:
    root_entries = {path.name for path in site_root.iterdir()}
    if "pysht" not in root_entries:
        _fail("the documentation directory must be named exactly 'pysht'")
    if "pySHT" in root_entries:
        _fail("an uppercase 'pySHT' documentation directory was staged")


def _assert_safe_tree(site_root: Path) -> None:
    cname_files = [
        str(path.relative_to(site_root))
        for path in site_root.rglob("CNAME")
        if path.is_file()
    ]
    if cname_files:
        _fail(
            "the Actions artifact must use the Pages custom-domain setting, not "
            "CNAME files: " + ", ".join(cname_files)
        )

    symlinks = [
        str(path.relative_to(site_root))
        for path in site_root.rglob("*")
        if path.is_symlink()
    ]
    if symlinks:
        _fail("symbolic links are not allowed: " + ", ".join(symlinks[:5]))

    leaked = [
        str(path.relative_to(site_root))
        for path in site_root.rglob("*")
        if path.name in {".git", ".github"}
    ]
    if leaked:
        _fail("repository metadata leaked into the artifact: " + ", ".join(leaked))

    total_size = sum(
        path.stat().st_size for path in site_root.rglob("*") if path.is_file()
    )
    if total_size >= 1_000_000_000:
        _fail(f"artifact is unexpectedly large: {total_size} bytes")


def _assert_personal_site_preserved(source_root: Path, site_root: Path) -> None:
    ignored = {Path("CNAME"), Path("robots.txt")}
    for source in source_root.rglob("*"):
        if not source.is_file():
            continue
        relative = source.relative_to(source_root)
        if relative in ignored:
            continue
        staged = site_root / relative
        if not staged.is_file() or staged.read_bytes() != source.read_bytes():
            _fail(f"personal-site output changed unexpectedly: {relative}")

    allowed_top_level = {".nojekyll", "pysht", "robots.txt"}
    for staged in site_root.rglob("*"):
        if not staged.is_file():
            continue
        relative = staged.relative_to(site_root)
        if relative.parts[0] in allowed_top_level:
            continue
        source = source_root / relative
        if not source.is_file():
            _fail(f"unexpected file outside the pySHT subtree: {relative}")

    source_robots = (source_root / "robots.txt").read_text(encoding="utf-8")
    expected_lines = source_robots.splitlines()
    if PY_SHT_SITEMAP not in expected_lines:
        expected_lines.append(PY_SHT_SITEMAP)
    expected_robots = "\n".join(expected_lines) + "\n"
    actual_robots = (site_root / "robots.txt").read_text(encoding="utf-8")
    if actual_robots != expected_robots:
        _fail("the deployed robots.txt differs from the expected two-sitemap form")
    if ROOT_SITEMAP not in actual_robots or PY_SHT_SITEMAP not in actual_robots:
        _fail("robots.txt must advertise both the personal and pySHT sitemaps")


def _assert_sitemap(site_root: Path) -> int:
    sitemap = site_root / "pysht" / "sitemap.xml"
    namespace = {"sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [
        element.text or ""
        for element in ET.parse(sitemap).findall("sitemap:url/sitemap:loc", namespace)
    ]
    if len(locations) < 50:
        _fail(f"pySHT sitemap is unexpectedly small: {len(locations)} URLs")
    invalid = [url for url in locations if not url.startswith(PY_SHT_BASE_URL)]
    if invalid:
        _fail("pySHT sitemap contains an unexpected base URL: " + invalid[0])
    if any("/pySHT/" in url for url in locations):
        _fail("pySHT sitemap contains the mixed-case project path")
    return len(locations)


def _resolve_local_target(site_root: Path, page: Path, raw_target: str) -> Path | None:
    if raw_target.startswith("#"):
        return None
    parsed = urlsplit(raw_target)
    if parsed.scheme.lower() in IGNORED_SCHEMES or parsed.netloc:
        return None
    if not parsed.path:
        return None

    decoded = unquote(parsed.path)
    target = (
        site_root / decoded.lstrip("/")
        if decoded.startswith("/")
        else page.parent / decoded
    )
    target = target.resolve(strict=False)
    try:
        target.relative_to(site_root)
    except ValueError:
        _fail(f"local link escapes the site root in {page}: {raw_target}")

    if target.is_dir():
        target = target / "index.html"
    return target


def _assert_pysht_local_links(site_root: Path) -> tuple[int, int]:
    docs_root = site_root / "pysht"
    pages = [
        page for page in docs_root.rglob("*.html") if page.name != "webpack-macros.html"
    ]
    failures: list[str] = []
    checked = 0
    for page in pages:
        parser = _AssetParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for raw_target in parser.targets:
            target = _resolve_local_target(site_root, page, raw_target)
            if target is None:
                continue
            checked += 1
            if not target.exists():
                failures.append(f"{page.relative_to(site_root)} -> {raw_target}")
    if failures:
        _fail("missing local pySHT targets:\n" + "\n".join(failures[:20]))
    return len(pages), checked


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("personal_site", type=Path, help="tracked personal-site docs")
    parser.add_argument("artifact", type=Path, help="combined Pages artifact")
    args = parser.parse_args()

    source_root = args.personal_site.resolve(strict=True)
    site_root = args.artifact.resolve(strict=True)
    try:
        _assert_required_files(site_root)
        _assert_exact_lowercase_path(site_root)
        _assert_safe_tree(site_root)
        _assert_personal_site_preserved(source_root, site_root)
        sitemap_count = _assert_sitemap(site_root)
        page_count, link_count = _assert_pysht_local_links(site_root)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Pages artifact validation failed: {error}", file=sys.stderr)
        return 1

    print(
        "Pages artifact validated: "
        f"{page_count} pySHT HTML pages, {link_count} local targets, "
        f"{sitemap_count} sitemap URLs."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
