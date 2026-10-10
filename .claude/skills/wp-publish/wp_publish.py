# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown>=3.6", "python-frontmatter>=1.1", "Pygments>=2.18"]
# ///
"""Post a Markdown file to WordPress through the REST API.

    uv run --script wp_publish.py POST.md [--dry-run] [--force]
    uv run --script wp_publish.py POST.md --html      # print what would be sent, no network
    uv run --script wp_publish.py POST.md --classic   # plain HTML instead of Gutenberg blocks
    uv run --script wp_publish.py --whoami            # prove the credentials work

Content is sent as Gutenberg blocks. Undelimited HTML still renders, but the
editor treats the whole post as one Classic block and block-aware plugins
never fire -- on this site that means code arrives unhighlighted. --classic
is the escape hatch for a post that the serializer mangles.

The file's YAML frontmatter is the control surface:

    status: draft | publish   # ABSENT -> nothing is sent, exit 0
    title:                    # default: first '# ' heading, which is then removed from the body
    slug:                     # default: filename stem
    excerpt:
    categories: [Name, ...]   # must already exist on the site (structure is Peter's call)
    tags: [name, ...]         # created if missing
    date: 2026-09-12T09:00    # optional, site-local time
    wp_id: 123                # written back here by this script after the first create

Re-running with a wp_id updates the same post. Moving a published post back to
draft is refused unless --force is given.

Credentials: a netrc-format file, default ~/.config/wp-publish/netrc, mode 0600:

    machine peter.fitzgibbons.info login USERNAME password APPPASSWORD

Paste the application password WITHOUT its spaces. WordPress strips
non-alphanumerics before comparing, and netrc tokenizes on whitespace.
"""

import argparse
import html
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

import frontmatter
import markdown

SITE = os.environ.get("WP_SITE", "https://peter.fitzgibbons.info").rstrip("/")
NETRC = Path(os.environ.get("WP_NETRC", "~/.config/wp-publish/netrc")).expanduser()
ALLOWED_STATUS = ("draft", "publish")
MD_EXTENSIONS = ["extra", "sane_lists"]


def die(msg: str, code: int = 1) -> None:
    print(f"wp_publish: {msg}", file=sys.stderr)
    sys.exit(code)


# --- auth -------------------------------------------------------------------

def basic_auth() -> str:
    if not NETRC.exists():
        die(f"credentials file not found: {NETRC} (see docstring for format)")
    mode = stat.S_IMODE(NETRC.stat().st_mode)
    if mode & 0o077:
        die(f"{NETRC} is mode {mode:04o}; refusing to read a credentials file "
            f"readable by group/other. Fix: chmod 600 {NETRC}")
    host = urllib.parse.urlparse(SITE).hostname
    auth = netrc.netrc(str(NETRC)).authenticators(host)
    if not auth:
        die(f"no 'machine {host}' entry in {NETRC}")
    login, _, password = auth
    import base64
    return "Basic " + base64.b64encode(f"{login}:{password}".encode()).decode()


# --- REST -------------------------------------------------------------------

def api(method: str, path: str, params: dict | None = None, body: dict | None = None):
    url = f"{SITE}/wp-json/wp/v2{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": basic_auth(),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "wp_publish.py",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        try:
            msg = json.load(e).get("message", e.reason)
        except Exception:
            msg = e.reason
        die(f"HTTP {e.code} on {method} {path}: {msg}")
    except urllib.error.URLError as e:
        die(f"cannot reach {SITE}: {e.reason}")


TERM_LABEL = {"categories": "category", "tags": "tag"}


def term_ids(taxonomy: str, names: list[str], create: bool, dry_run: bool) -> list[int | None]:
    """Resolve term names to ids. Categories must exist; tags are created on demand.

    The split is about taxonomy structure, not about capability. Categories are
    the site's shape and that is Peter's decision, so a missing one is an error.
    Tags are free-form labels, so a missing one is created.

    Creating a tag is safe for the `wp_publisher` role to do. Measured against
    the live site on 2026-10-10: without `manage_categories` the account creates
    a tag happily, and is refused on editing or deleting ANY term, including one
    it just created. WordPress draws create-without-destroy here on its own.

    Every missing category is collected before failing, so one run names all of
    them rather than one per attempt.
    """
    label = TERM_LABEL.get(taxonomy, taxonomy)
    ids: list[int | None] = []
    missing: list[str] = []
    for name in names:
        found = api("GET", f"/{taxonomy}", {"search": name, "per_page": 100, "_fields": "id,name"})
        match = next((t for t in found if html.unescape(t["name"]).casefold() == name.casefold()), None)
        if match:
            ids.append(match["id"])
        elif not create:
            missing.append(name)
        elif dry_run:
            print(f"  would create {label} {name!r}")
            ids.append(None)
        else:
            ids.append(api("POST", f"/{taxonomy}", body={"name": name})["id"])
    if missing:
        lines = [f"no such {label} on the site: " + ", ".join(repr(m) for m in missing),
                 "nothing was sent. Taxonomy structure is a human decision, so create them in "
                 "WP Admin, or with the admin credential:"]
        for m in missing:
            lines.append(
                f"  curl -sS --netrc-file ~/.config/wp-publish/netrc-admin "
                f"-X POST {SITE}/wp-json/wp/v2/{taxonomy} "
                f"-H 'Content-Type: application/json' -d '{json.dumps({'name': m})}'")
        die("\n".join(lines))
    return ids


# --- post -------------------------------------------------------------------

def load_post(path: Path):
    post = frontmatter.load(path)
    body = post.content
    title = post.get("title")
    if not title:
        m = re.match(r"\s*#[ \t]+(.+?)[ \t]*\r?\n", body)
        if not m:
            die("no title: add 'title:' to the frontmatter or start the body with a '# ' heading")
        title, body = m.group(1), body[m.end():]
    return post, title, body


def write_back_id(path: Path, wp_id: int) -> None:
    text = path.read_text()
    if not text.startswith("---\n"):
        die(f"cannot write wp_id back: {path} does not start with a frontmatter block")
    path.write_text("---\n" + f"wp_id: {wp_id}\n" + text[4:])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="resolve everything, send nothing")
    ap.add_argument("--force", action="store_true", help="allow publish -> draft")
    ap.add_argument("--html", action="store_true", help="print the rendered content and exit (no network)")
    ap.add_argument("--classic", action="store_true",
                    help="send plain HTML; skip the Gutenberg block delimiters")
    ap.add_argument("--blocks", action="store_true",
                    help=argparse.SUPPRESS)  # blocks are the default; accepted so the old command still runs
    ap.add_argument("--whoami", action="store_true", help="GET /users/me and exit")
    args = ap.parse_args()

    if args.whoami:
        me = api("GET", "/users/me", {"context": "edit", "_fields": "id,name,slug,roles"})
        print(f"authenticated to {SITE} as {me['name']} (id {me['id']}, roles {', '.join(me['roles'])})")
        return 0

    if not args.file:
        ap.error("a post file is required")
    path = args.file
    if not path.is_file():
        die(f"not a file: {path}")

    post, title, body = load_post(path)
    rendered = markdown.markdown(body, extensions=MD_EXTENSIONS)
    if not args.classic:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from blocks import to_blocks
        rendered = to_blocks(rendered)

    if args.html:
        print(rendered)
        return 0

    status = post.get("status")
    if status is None:
        print(f"{path}: no 'status:' in frontmatter — not marked for posting, nothing sent")
        return 0
    if status not in ALLOWED_STATUS:
        die(f"status {status!r} not allowed; use one of {ALLOWED_STATUS}")

    wp_id = post.get("wp_id")
    action = f"update post #{wp_id}" if wp_id else "create"
    print(f"{'DRY RUN — ' if args.dry_run else ''}{action} on {SITE}")
    print(f"  title:  {title}")
    slug = post.get("slug") or path.stem
    print(f"  slug:   {slug}")
    print(f"  status: {status}")

    if wp_id:
        remote = api("GET", f"/posts/{wp_id}", {"context": "edit", "_fields": "id,status,link"})
        print(f"  remote: currently {remote['status']} at {remote['link']}")
        if remote["status"] == "publish" and status == "draft" and not args.force:
            die("refusing to move a published post back to draft; pass --force if you mean it")

    payload: dict = {"title": title, "slug": slug, "status": status, "content": rendered}
    for key in ("excerpt", "date"):
        if post.get(key):
            payload[key] = str(post[key])
    if post.get("categories"):
        payload["categories"] = term_ids("categories", list(post["categories"]),
                                         create=False, dry_run=args.dry_run)
        print(f"  categories: {dict(zip(post['categories'], payload['categories']))}")
    if post.get("tags"):
        payload["tags"] = term_ids("tags", list(post["tags"]),
                                   create=True, dry_run=args.dry_run)
        print(f"  tags:       {dict(zip(post['tags'], payload['tags']))}")
    kind = "HTML (--classic)" if args.classic else "Gutenberg blocks"
    print(f"  content: {len(rendered)} bytes of {kind} from {len(body)} bytes of Markdown")

    if args.dry_run:
        print("nothing sent")
        return 0

    result = api("POST", f"/posts/{wp_id}" if wp_id else "/posts", body=payload)
    if not wp_id:
        write_back_id(path, result["id"])
        print(f"  wrote wp_id: {result['id']} into {path}")
    print(f"done: post #{result['id']} is {result['status']} — {result['link']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
