#!/usr/bin/env python3
"""
ProjectCero Frontend Overhaul - Phase 10 Final Audit

Run from the ProjectCero repository root:

    python tools/frontend_phase10_audit.py

Optional:

    python tools/frontend_phase10_audit.py --fail-on-error
    python tools/frontend_phase10_audit.py --output docs/frontend-phase10-audit-report.md

What it checks:
- Key public pages return HTTP 200.
- Optional detail pages are tested if matching content exists in the database.
- Pages include a title, header, footer, and basic body content.
- Internal links found on audited pages are checked, while risky/side-effect links are skipped.
- Expected design-system imports are present.
- Expected Phase 1-9 files exist.

It does NOT modify database records.
It does NOT submit forms.
It skips order/payment creation URLs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

try:
    import django
    django.setup()
except Exception as exc:  # pragma: no cover
    print("ERROR: Could not initialise Django.")
    print(f"{type(exc).__name__}: {exc}")
    print("Run this from the ProjectCero repo root with your virtualenv activated.")
    sys.exit(2)

from django.test import Client
from django.urls import NoReverseMatch, reverse


@dataclass
class AuditResult:
    category: str
    name: str
    status: str
    detail: str = ""
    url: str = ""


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: set[str] = set()
        self.title_text: str = ""
        self._in_title = False
        self.has_header = False
        self.has_footer = False
        self.has_main = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k: v for k, v in attrs}
        if tag == "a":
            href = attrs_dict.get("href")
            if href:
                self.hrefs.add(href)
        elif tag == "title":
            self._in_title = True
        elif tag == "header":
            self.has_header = True
        elif tag == "footer":
            self.has_footer = True
        elif tag == "main":
            self.has_main = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_text += data.strip()


def safe_reverse(name: str, *args, **kwargs) -> str | None:
    try:
        return reverse(name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        return None


def add_url(results: list[AuditResult], pages: list[tuple[str, str]], label: str, url_name: str, *args, **kwargs) -> None:
    url = safe_reverse(url_name, *args, **kwargs)
    if url:
        pages.append((label, url))
    else:
        results.append(AuditResult("URL reverse", label, "SKIP", f"Could not reverse {url_name}"))


def get_optional_detail_pages(results: list[AuditResult]) -> list[tuple[str, str]]:
    pages: list[tuple[str, str]] = []

    try:
        from apps.events.models import Event
        event = Event.objects.filter(status=Event.Status.PUBLISHED).order_by("start_at").first()
        if event:
            add_url(results, pages, f"Event detail: {event.title}", "events:event_detail", event.slug)
        else:
            results.append(AuditResult("Detail pages", "Event detail", "SKIP", "No published event found"))
    except Exception as exc:
        results.append(AuditResult("Detail pages", "Event detail", "SKIP", f"{type(exc).__name__}: {exc}"))

    try:
        from apps.artists.models import Artist
        artist = Artist.objects.filter(is_active=True).order_by("feature_order", "name").first()
        if artist:
            add_url(results, pages, f"Artist detail: {artist.name}", "artists:artist_detail", artist.slug)
        else:
            results.append(AuditResult("Detail pages", "Artist detail", "SKIP", "No active artist found"))
    except Exception as exc:
        results.append(AuditResult("Detail pages", "Artist detail", "SKIP", f"{type(exc).__name__}: {exc}"))

    try:
        from apps.studio.models import StudioService
        service = StudioService.objects.filter(is_active=True).order_by("display_order", "name").first()
        if service:
            add_url(results, pages, f"Studio service detail: {service.name}", "studio:service_detail", service.slug)
        else:
            results.append(AuditResult("Detail pages", "Studio service detail", "SKIP", "No active studio service found"))
    except Exception as exc:
        results.append(AuditResult("Detail pages", "Studio service detail", "SKIP", f"{type(exc).__name__}: {exc}"))

    try:
        from apps.merch.models import MerchItem
        item = MerchItem.objects.filter(is_active=True).order_by("display_order", "name").first()
        if item:
            add_url(results, pages, f"Merch detail: {item.name}", "merch:merch_detail", item.slug)
        else:
            results.append(AuditResult("Detail pages", "Merch detail", "SKIP", "No active merch item found"))
    except Exception as exc:
        results.append(AuditResult("Detail pages", "Merch detail", "SKIP", f"{type(exc).__name__}: {exc}"))

    try:
        from apps.news.models import NewsPost
        post = NewsPost.objects.filter(status=NewsPost.Status.PUBLISHED).order_by("-published_at", "-created_at").first()
        if post:
            add_url(results, pages, f"News detail: {post.title}", "news:news_detail", post.slug)
        else:
            results.append(AuditResult("Detail pages", "News detail", "SKIP", "No published news post found"))
    except Exception as exc:
        results.append(AuditResult("Detail pages", "News detail", "SKIP", f"{type(exc).__name__}: {exc}"))

    return pages


def public_pages(results: list[AuditResult]) -> list[tuple[str, str]]:
    pages: list[tuple[str, str]] = []

    names = [
        ("Home", "pages:home"),
        ("About", "pages:about"),
        ("Contact", "pages:contact"),
        ("Events", "events:event_list"),
        ("Event calendar", "events:calendar"),
        ("Artists", "artists:artist_list"),
        ("Studio", "studio:home"),
        ("Merch", "merch:merch_list"),
        ("News", "news:news_list"),
        ("Bookings landing", "bookings:landing"),
        ("Booking request base", "bookings:request"),
        ("Studio booking request", "bookings:studio_request"),
        ("Venue booking request", "bookings:venue_request"),
        ("Enquiries landing", "enquiries:landing"),
        ("General enquiry", "enquiries:general"),
        ("Merch enquiry", "enquiries:merch"),
        ("Payment enquiry", "enquiries:payment"),
        ("Enquiry success", "enquiries:success"),
    ]

    for label, url_name in names:
        add_url(results, pages, label, url_name)

    # Important filtered/search states.
    base_events = safe_reverse("events:event_list")
    if base_events:
        pages.append(("Events search state", f"{base_events}?q=test"))

    base_artists = safe_reverse("artists:artist_list")
    if base_artists:
        pages.append(("Artists search state", f"{base_artists}?q=test"))

    base_studio = safe_reverse("studio:home")
    if base_studio:
        pages.append(("Studio search state", f"{base_studio}?q=test"))

    request_url = safe_reverse("bookings:request")
    if request_url:
        pages.append(("Booking request studio query", f"{request_url}?type=studio"))
        pages.append(("Booking request venue query", f"{request_url}?type=venue"))

    pages.extend(get_optional_detail_pages(results))
    return pages


def should_skip_link(href: str) -> tuple[bool, str]:
    href = href.strip()

    if not href:
        return True, "empty"
    if href.startswith("#"):
        return True, "anchor"
    if href.startswith(("mailto:", "tel:", "sms:", "whatsapp:")):
        return True, "non-http contact link"
    if href.startswith(("http://", "https://")):
        parsed = urlparse(href)
        if parsed.netloc and parsed.netloc not in {"testserver", "localhost", "127.0.0.1"}:
            return True, "external"
    if href.startswith(("/static/", "/media/")):
        return True, "static/media"
    if href.endswith(".ics") or "calendar-feed" in href:
        return True, "calendar/feed"
    if href.startswith("/admin/"):
        return True, "admin"
    if href.startswith("/orders/"):
        return True, "order/payment side-effect"
    if href.startswith("/bookings/unavailable"):
        return True, "availability feed"
    return False, ""


def normalise_internal_href(href: str) -> str:
    parsed = urlparse(href)
    if parsed.netloc in {"testserver", "localhost", "127.0.0.1"}:
        path = parsed.path
        if parsed.query:
            return f"{path}?{parsed.query}"
        return path
    return href


def check_page(client: Client, label: str, url: str) -> tuple[AuditResult, set[str]]:
    try:
        response = client.get(url)
    except Exception as exc:
        return AuditResult("Public pages", label, "FAIL", f"{type(exc).__name__}: {exc}", url), set()

    if response.status_code != 200:
        return AuditResult("Public pages", label, "FAIL", f"HTTP {response.status_code}", url), set()

    content = response.content.decode("utf-8", errors="replace")
    parser = LinkParser()
    parser.feed(content)

    warnings: list[str] = []

    if not parser.title_text:
        warnings.append("missing <title>")
    if not parser.has_header:
        warnings.append("missing <header>")
    if not parser.has_main:
        warnings.append("missing <main>")
    if not parser.has_footer:
        warnings.append("missing <footer>")
    if "Traceback" in content or "TemplateDoesNotExist" in content:
        warnings.append("possible template error text found")

    body_text = re.sub(r"<[^>]+>", " ", content)
    body_text = re.sub(r"\s+", " ", body_text).strip()
    if len(body_text) < 120:
        warnings.append("page body looks very short")

    if warnings:
        return AuditResult("Public pages", label, "WARN", "; ".join(warnings), url), parser.hrefs

    return AuditResult("Public pages", label, "PASS", "HTTP 200", url), parser.hrefs


def check_design_system_files(root: Path) -> list[AuditResult]:
    results: list[AuditResult] = []

    expected_files = [
        "static/css/design-system.css",
        "static/css/design-system/components/hero.css",
        "static/css/design-system/components/sections.css",
        "static/css/design-system/components/cards.css",
        "static/css/design-system/components/gallery.css",
        "static/css/design-system/components/shell.css",
        "static/css/design-system/pages/home.css",
        "static/css/design-system/pages/events.css",
        "static/css/design-system/pages/artists.css",
        "static/css/design-system/pages/studio.css",
        "static/css/design-system/pages/details.css",
        "static/css/design-system/pages/conversion.css",
        "static/css/design-system/pages/content.css",
        "static/css/design-system/utilities/responsive-qa.css",
        "templates/includes/cards/listing_event_card.html",
        "templates/includes/cards/listing_artist_card.html",
        "templates/includes/cards/listing_studio_service_card.html",
        "templates/includes/cards/listing_merch_card.html",
        "templates/includes/cards/listing_news_card.html",
        "templates/includes/cards/detail_event_teaser_card.html",
    ]

    for rel in expected_files:
        path = root / rel
        if path.exists():
            results.append(AuditResult("Files", rel, "PASS", "exists"))
        else:
            results.append(AuditResult("Files", rel, "FAIL", "missing"))

    css_path = root / "static/css/design-system.css"
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8", errors="replace")
        expected_imports = [
            "components/hero.css",
            "components/sections.css",
            "components/cards.css",
            "components/gallery.css",
            "components/shell.css",
            "pages/home.css",
            "pages/events.css",
            "pages/artists.css",
            "pages/studio.css",
            "pages/details.css",
            "pages/conversion.css",
            "pages/content.css",
            "utilities/responsive-qa.css",
        ]
        for item in expected_imports:
            if item in css:
                results.append(AuditResult("CSS imports", item, "PASS", "imported"))
            else:
                results.append(AuditResult("CSS imports", item, "FAIL", "missing import"))

    return results


def check_internal_links(client: Client, hrefs: Iterable[str]) -> list[AuditResult]:
    results: list[AuditResult] = []
    seen: set[str] = set()

    for href in sorted(hrefs):
        skip, reason = should_skip_link(href)
        if skip:
            continue

        url = normalise_internal_href(href)
        if not url.startswith("/"):
            continue
        if url in seen:
            continue
        seen.add(url)

        try:
            response = client.get(url)
        except Exception as exc:
            results.append(AuditResult("Internal links", url, "FAIL", f"{type(exc).__name__}: {exc}", url))
            continue

        if response.status_code >= 400:
            results.append(AuditResult("Internal links", url, "FAIL", f"HTTP {response.status_code}", url))
        elif response.status_code in {301, 302, 303, 307, 308}:
            results.append(AuditResult("Internal links", url, "WARN", f"Redirect {response.status_code}", url))
        else:
            results.append(AuditResult("Internal links", url, "PASS", f"HTTP {response.status_code}", url))

    if not results:
        results.append(AuditResult("Internal links", "No internal links checked", "WARN", "No eligible internal links found"))

    return results


def write_markdown_report(path: Path, results: list[AuditResult]) -> None:
    counts = {
        "PASS": sum(1 for r in results if r.status == "PASS"),
        "WARN": sum(1 for r in results if r.status == "WARN"),
        "FAIL": sum(1 for r in results if r.status == "FAIL"),
        "SKIP": sum(1 for r in results if r.status == "SKIP"),
    }

    grouped: dict[str, list[AuditResult]] = {}
    for result in results:
        grouped.setdefault(result.category, []).append(result)

    lines = [
        "# ProjectCero Phase 10 Frontend Audit Report",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Summary",
        "",
        f"- PASS: {counts['PASS']}",
        f"- WARN: {counts['WARN']}",
        f"- FAIL: {counts['FAIL']}",
        f"- SKIP: {counts['SKIP']}",
        "",
    ]

    for category, items in grouped.items():
        lines.extend([f"## {category}", ""])
        lines.append("| Status | Name | URL | Detail |")
        lines.append("|---|---|---|---|")
        for item in items:
            detail = item.detail.replace("|", "\\|")
            name = item.name.replace("|", "\\|")
            url = item.url.replace("|", "\\|")
            lines.append(f"| {item.status} | {name} | `{url}` | {detail} |")
        lines.append("")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="docs/frontend-phase10-audit-report.md",
        help="Markdown report path. Default: docs/frontend-phase10-audit-report.md",
    )
    parser.add_argument(
        "--json-output",
        default="",
        help="Optional JSON report path.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 when FAIL results are found.",
    )
    args = parser.parse_args()

    root = Path.cwd()
    client = Client(HTTP_HOST="testserver")

    results: list[AuditResult] = []
    hrefs: set[str] = set()

    results.extend(check_design_system_files(root))

    for label, url in public_pages(results):
        result, page_hrefs = check_page(client, label, url)
        results.append(result)
        if result.status in {"PASS", "WARN"}:
            hrefs.update(page_hrefs)

    results.extend(check_internal_links(client, hrefs))

    output_path = root / args.output
    write_markdown_report(output_path, results)

    if args.json_output:
        json_path = root / args.json_output
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps([asdict(r) for r in results], indent=2), encoding="utf-8")

    counts = {
        "PASS": sum(1 for r in results if r.status == "PASS"),
        "WARN": sum(1 for r in results if r.status == "WARN"),
        "FAIL": sum(1 for r in results if r.status == "FAIL"),
        "SKIP": sum(1 for r in results if r.status == "SKIP"),
    }

    print("ProjectCero Phase 10 Frontend Audit")
    print("-----------------------------------")
    print(f"PASS: {counts['PASS']}")
    print(f"WARN: {counts['WARN']}")
    print(f"FAIL: {counts['FAIL']}")
    print(f"SKIP: {counts['SKIP']}")
    print(f"Report: {output_path}")

    if counts["FAIL"]:
        print("\nFailures:")
        for result in results:
            if result.status == "FAIL":
                print(f"- [{result.category}] {result.name}: {result.detail} {result.url}")

    if args.fail_on_error and counts["FAIL"]:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
