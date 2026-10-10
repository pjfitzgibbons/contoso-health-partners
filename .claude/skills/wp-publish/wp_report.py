#!/usr/bin/env python3
"""Report engagement for a post on the WordPress site: comments, and whether traffic is measurable.

    python3 wp_report.py blog/POST.md          # reads wp_id from the file's frontmatter
    python3 wp_report.py --id 8282469942
    python3 wp_report.py --id N --comments     # comments only, skip the traffic probe
    python3 wp_report.py --id N --json

Read-only. Every request is a GET; nothing on the site is modified, so this is
safe to run yourself.

COMMENTS come from the REST API and are real counts, including the ones a
visitor never sees -- held for moderation, spam, trashed.

TRAFFIC has no source on this site, and the point of the probe is to prove that
rather than assume it. WordPress core stores no view counter: a page view
leaves no row in the database. Any "views" number comes from a plugin or a
third-party beacon, so the probe looks in the three places one could hide:

    1. REST namespaces           -- an analytics plugin almost always registers one
    2. the active plugin list    -- requires auth
    3. the rendered post HTML    -- catches a beacon hardcoded in the theme

If all three come back empty the honest answer is "unknown, and unknowable from
here" -- not zero. The only remaining record is the web server's access log,
which lives with the host and is not reachable through any API. Do not
substitute a comment count, a share count, or a guess for a view count.

Stdlib only, by design: a reporting tool that needs no dependency resolution
always runs. Credentials are the same netrc file wp_publish.py uses.
"""

import argparse
import base64
import json
import netrc
import os
import re
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SITE = os.environ.get("WP_SITE", "https://peter.fitzgibbons.info").rstrip("/")
NETRC = Path(os.environ.get("WP_NETRC", "~/.config/wp-publish/netrc")).expanduser()

COMMENT_STATUSES = ("approve", "hold", "spam", "trash")

# An analytics product betrays itself in at least one of these three ways. Each
# list is matched case-insensitively as a substring, so a version suffix or a
# vendor rename still hits.
ANALYTICS_NAMESPACES = (
    "jetpack/", "wpcom/", "wp-statistics/", "matomo/", "burst/", "koko-analytics/",
    "google-site-kit/", "statify/", "independent-analytics/", "slimstat/", "pirsch/",
)
ANALYTICS_PLUGINS = (
    "jetpack", "wp-statistics", "matomo", "burst-statistics", "independent-analytics",
    "google-site-kit", "koko-analytics", "wp-slimstat", "statify", "wp-piwik",
    "ga-google-analytics", "google-analytics-for-wordpress", "pixelyoursite",
    "analytics-insights", "clicky", "statcounter",
)
ANALYTICS_BEACONS = (
    "googletagmanager.com", "google-analytics.com", "gtag(", "stats.wp.com",
    "plausible.io", "usefathom.com", "matomo.js", "piwik.js", "umami",
    "cloudflareinsights.com", "clarity.ms", "statcounter.com", "hotjar",
    "mixpanel", "cdn.segment.com", "posthog", "counter.dev", "simpleanalytics",
    "pirsch.io", "goatcounter",
)


def die(msg: str, code: int = 1) -> None:
    print(f"wp_report: {msg}", file=sys.stderr)
    sys.exit(code)


# --- auth -------------------------------------------------------------------

def basic_auth() -> str:
    """Same contract as wp_publish.basic_auth: refuse a credentials file others can read."""
    if not NETRC.exists():
        die(f"credentials file not found: {NETRC}")
    mode = stat.S_IMODE(NETRC.stat().st_mode)
    if mode & 0o077:
        die(f"{NETRC} is mode {mode:04o}; refusing to read a credentials file "
            f"readable by group/other. Fix: chmod 600 {NETRC}")
    host = urllib.parse.urlparse(SITE).hostname
    auth = netrc.netrc(str(NETRC)).authenticators(host)
    if not auth:
        die(f"no 'machine {host}' entry in {NETRC}")
    login, _, password = auth
    return "Basic " + base64.b64encode(f"{login}:{password}".encode()).decode()


# --- REST -------------------------------------------------------------------

def get(path: str, params: dict | None = None, auth: bool = True, fatal: bool = True):
    """GET and return (payload, headers). On a non-fatal HTTP error return (None, {})."""
    url = f"{SITE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = {"Accept": "application/json", "User-Agent": "wp_report.py"}
    if auth:
        headers["Authorization"] = basic_auth()
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r), dict(r.headers)
    except urllib.error.HTTPError as e:
        if not fatal:
            return None, {}
        try:
            msg = json.load(e).get("message", e.reason)
        except Exception:
            msg = e.reason
        die(f"HTTP {e.code} on GET {path}: {msg}")
    except urllib.error.URLError as e:
        if not fatal:
            return None, {}
        die(f"cannot reach {SITE}: {e.reason}")


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "wp_report.py"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read(2_000_000).decode("utf8", "replace")
    except Exception:
        return ""


# --- the post ---------------------------------------------------------------

def resolve_id(args) -> int:
    if args.id:
        return args.id
    if not args.file:
        die("give a post: either a blog/*.md file with a wp_id, or --id N")
    path = Path(args.file)
    if not path.exists():
        die(f"no such file: {path}")
    head = path.read_text()[:4000]
    m = re.search(r"^wp_id:\s*(\d+)\s*$", head, re.M)
    if not m:
        die(f"{path} has no 'wp_id:' line — it has never been posted, so there is "
            f"nothing to report on")
    return int(m.group(1))


def post_facts(post_id: int) -> dict:
    p, _ = get(f"/wp-json/wp/v2/posts/{post_id}", {"context": "edit"})
    return {
        "id": p["id"],
        "title": p["title"]["raw"] or p["title"]["rendered"],
        "status": p["status"],
        "link": p["link"],
        "slug": p["slug"],
        "date_gmt": p["date_gmt"],
        "modified_gmt": p["modified_gmt"],
        "comment_status": p["comment_status"],
        "sticky": p.get("sticky"),
    }


# --- comments ---------------------------------------------------------------

def comments(post_id: int) -> dict:
    """Counts per status plus the comments themselves.

    Queried one status at a time rather than with status=all: the collection's
    X-WP-Total header then gives an authoritative count per status without
    paging, and a status the site has disabled fails in isolation instead of
    taking the whole report with it.
    """
    out: dict = {"counts": {}, "items": []}
    for status in COMMENT_STATUSES:
        payload, headers = get("/wp-json/wp/v2/comments", {
            "post": post_id, "status": status, "per_page": 100,
            "context": "edit", "orderby": "date_gmt", "order": "asc",
        }, fatal=False)
        if payload is None:
            out["counts"][status] = None  # not queryable, not zero
            continue
        out["counts"][status] = int(headers.get("X-WP-Total", len(payload)))
        for c in payload:
            out["items"].append({
                "id": c["id"],
                "status": status,
                "author": c.get("author_name") or "(anonymous)",
                "author_url": c.get("author_url") or "",
                "date_gmt": c["date_gmt"],
                "parent": c.get("parent", 0),
                "text": re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", c["content"]["rendered"])).strip(),
            })
    out["items"].sort(key=lambda c: c["date_gmt"])
    known = [v for v in out["counts"].values() if v is not None]
    out["total"] = sum(known) if known else None
    return out


# --- traffic ----------------------------------------------------------------

def traffic_probe(link: str) -> dict:
    """Look for an analytics source in the three places one can be installed."""
    found: dict = {"namespaces": [], "plugins": [], "beacons": [], "checked": []}

    root, _ = get("/wp-json/", auth=False, fatal=False)
    if root is None:
        found["checked"].append("REST root: unreachable")
    else:
        ns = root.get("namespaces", [])
        found["checked"].append(f"REST namespaces: {len(ns)} registered")
        found["namespaces"] = [n for n in ns
                               if any(a.rstrip("/") in n.lower() for a in ANALYTICS_NAMESPACES)]

    plugins, _ = get("/wp-json/wp/v2/plugins", fatal=False)
    if plugins is None:
        found["checked"].append("plugin list: not readable with these credentials")
    else:
        active = [p for p in plugins if p.get("status") == "active"]
        found["checked"].append(f"plugins: {len(active)} active of {len(plugins)}")
        found["plugins"] = [p["plugin"] for p in active
                            if any(a in p["plugin"].lower() for a in ANALYTICS_PLUGINS)]

    html = fetch_text(link) if link else ""
    if not html:
        found["checked"].append("rendered page: could not fetch")
    else:
        found["checked"].append(f"rendered page: {len(html)} bytes scanned")
        low = html.lower()
        found["beacons"] = sorted({b for b in ANALYTICS_BEACONS if b in low})

    found["instrumented"] = bool(found["namespaces"] or found["plugins"] or found["beacons"])
    return found


# --- output -----------------------------------------------------------------

def report(facts: dict, cmts: dict | None, traffic: dict | None) -> None:
    print(f"{facts['title']}")
    print(f"  id {facts['id']}  ·  {facts['status']}  ·  comments {facts['comment_status']}")
    print(f"  posted   {facts['date_gmt']}Z")
    print(f"  modified {facts['modified_gmt']}Z")
    print(f"  {facts['link']}")

    if cmts is not None:
        print("\nComments")
        parts = ", ".join(
            f"{k} {'?' if v is None else v}" for k, v in cmts["counts"].items())
        total = cmts["total"]
        print(f"  total {'unknown' if total is None else total}   ({parts})")
        if not cmts["items"]:
            print("  none")
        for c in cmts["items"]:
            text = c["text"]
            if len(text) > 300:
                text = text[:300] + "…"
            reply = f" reply to {c['parent']}" if c["parent"] else ""
            print(f"\n  [{c['status']}] {c['author']}  {c['date_gmt']}Z{reply}")
            if c["author_url"]:
                print(f"    {c['author_url']}")
            print(f"    {text}")

    if traffic is not None:
        print("\nTraffic")
        for line in traffic["checked"]:
            print(f"  checked  {line}")
        if traffic["instrumented"]:
            for n in traffic["namespaces"]:
                print(f"  FOUND    REST namespace {n}")
            for p in traffic["plugins"]:
                print(f"  FOUND    active plugin {p}")
            for b in traffic["beacons"]:
                print(f"  FOUND    beacon {b}")
            print("\n  An analytics source exists. This script does not read it — each one has "
                  "its own\n  API and its own auth. Query the source named above for view counts.")
        else:
            print("\n  No analytics source. WordPress core keeps no view counter, so there is no\n"
                  "  number to report and none is being withheld: page views for this post are\n"
                  "  UNKNOWN, not zero. The only surviving record is the web server's access log,\n"
                  "  held by the host and not reachable through any API.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="a blog/*.md file carrying a wp_id")
    ap.add_argument("--id", type=int, help="post id, instead of a file")
    ap.add_argument("--comments", action="store_true", help="comments only, skip the traffic probe")
    ap.add_argument("--traffic", action="store_true", help="traffic probe only, skip comments")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    post_id = resolve_id(args)
    facts = post_facts(post_id)
    want_comments = not args.traffic
    want_traffic = not args.comments
    cmts = comments(post_id) if want_comments else None
    traffic = traffic_probe(facts["link"]) if want_traffic else None

    if args.json:
        print(json.dumps({"post": facts, "comments": cmts, "traffic": traffic}, indent=2))
    else:
        report(facts, cmts, traffic)
    return 0


if __name__ == "__main__":
    sys.exit(main())
