"""Qualification checks for the preserved shared-memory contribution."""

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, urlopen

BASE = "a49ff9d84c592ed8f20c6edb0d833939b958749d"
PAGE = "docs/06-ai-agents/03-agent-communication/03-shared-memory.md"
SOURCE_HASH = "b63bc05f70434e05c85366c21056432f6d5a6def9235573a9797099742f218a8"
CONFIG_HASH = "03f597b5907d627b33ac10e5aa1817aa40216a14dc8ce562adf80bdf27e819da"
CANDIDATE_HASH = "fc7ba87e715aa2fe04c7185b7c49d0723b4b8b99dac7f1d423177c8165ca5427"
URLS = (
    "https://clickhouse.github.io/loom/use-cases/multi-agent/",
    "https://clickhouse.github.io/loom/use-cases/memory-linked-to-code/",
)


def git(*args):
    return subprocess.check_output(["git", *args])


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.add(attrs["href"])


def source():
    original = git("show", f"{BASE}:{PAGE}")
    candidate = Path(PAGE).read_bytes()
    assert hashlib.sha256(original).hexdigest() == SOURCE_HASH
    assert hashlib.sha256(candidate).hexdigest() == CANDIDATE_HASH
    subprocess.run(["git", "merge-base", "--is-ancestor", BASE, "HEAD"], check=True)
    changed = set(git("diff", "--name-only", BASE, "HEAD").decode().splitlines())
    assert changed == {PAGE, "mkdocs.yaml", ".github/workflows/e4-qualification.yml", ".github/qualification/check_e4.py"}, changed
    assert hashlib.sha256(Path("mkdocs.yaml").read_bytes()).hexdigest() == CONFIG_HASH
    for path in ("requirements.txt", "hooks/normalize_headings.py", ".github/workflows/ci.yaml"):
        assert Path(path).read_bytes() == git("show", f"{BASE}:{path}"), path
    fences = r"(?ms)^```.*?^```[^\n]*"
    assert re.findall(fences, original.decode()) == re.findall(fences, candidate.decode())
    nav_entry = "03-shared-memory: " + PAGE.removeprefix("docs/")
    assert nav_entry in Path("mkdocs.yaml").read_text()
    print(json.dumps({"candidate_sha256": CANDIDATE_HASH, "source_sha256": SOURCE_HASH, "unchanged_code_and_diagrams": True, "changed_page_navigation_entry": True}))


def links():
    for url in URLS:
        request = Request(url, headers={"User-Agent": "E4-contribution-qualification/1.0"})
        with urlopen(request, timeout=30) as response:
            assert response.status == 200, (url, response.status)
            assert response.url == url, (url, response.url)
            assert "text/html" in response.headers.get("Content-Type", ""), url
            assert response.read(2_000_000), url
            print(json.dumps({"url": url, "status": response.status, "final_url": response.url}))


def rendered():
    page = Path("site/06-ai-agents/03-agent-communication/03-shared-memory/index.html")
    text = page.read_text()
    parsed = Elements()
    parsed.feed(text)
    assert "workflow-progress-and-reusable-lessons" in parsed.ids
    assert "A stored lesson is context for a decision" in text
    assert set(URLS) <= parsed.links
    home = Elements()
    home.feed(Path("site/index.html").read_text())
    assert "06-ai-agents/03-agent-communication/03-shared-memory/" in home.links
    print(json.dumps({"rendered_page": str(page), "new_section": True, "new_links": True, "home_navigation": True}))


if __name__ == "__main__":
    {"source": source, "links": links, "rendered": rendered}[sys.argv[1]]()
