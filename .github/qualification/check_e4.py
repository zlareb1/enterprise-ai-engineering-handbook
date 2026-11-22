"""Qualification checks for the preserved shared-memory contribution."""

import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import Request, urlopen

BASE = "a49ff9d84c592ed8f20c6edb0d833939b958749d"
PAGE = "docs/06-ai-agents/03-agent-communication/03-shared-memory.md"
SOURCE_HASH = "b63bc05f70434e05c85366c21056432f6d5a6def9235573a9797099742f218a8"
REPAIR_HASHES = {
    "docs/01-machine-learning/index.md": "4fc53549ddf264640e45fb7308e026a8c436ec56bc370a440fa7b9123bab0b63",
    "docs/02-deep-learning/13-tensorflow-and-keras-fundamentals.md": "47d4aeb024d5c0a847840e9a7ec97eee35f3fec011967ed80373d4db09c9a02e",
    "docs/02-deep-learning/index.md": "1ab9c1ecc2e615cfae2b26918175698a443161d602e3ebd486fafd5c717d9a69",
    "docs/03-generative-ai/16-llm-evaluation.md": "b9065912d85cc4d1a61b001d671f5d5045c613b21945839fbb22a23e5043b756",
    "docs/05-advanced-retrieval-augmented-generation/04-vector-search-engineering/04-faiss-vs-chromadb-vs-milvus.md": "d1437b16135be2ce9f20cca6c97ab0e6b05ad7426843d70e56415c86e0df0aaf",
    "docs/05-advanced-retrieval-augmented-generation/06-advanced-rag-architecture/06-agentic-rag.md": "93c182f871844ce602b272ab1b761003e11cae10044cc3e66f89417f7e21e8ad",
    "docs/05-advanced-retrieval-augmented-generation/07-production-rag-engineering/01-prompt-assembly.md": "00229c7016ca5ffb5afc8377cd2f8c3f90137d4220adcbdab90c07f1cdd7fd3d",
    "docs/05-advanced-retrieval-augmented-generation/index.md": "d3cb9f50204ef217f153d9755c587e99ffc74dabad359b744871acaba6060e9b",
    "docs/06-ai-agents/05-agent-security/05-agent-authorization.md": "cddbbc8dadd9f336948794ec1900188d2559ce818c787e645be92312571c884d",
    "docs/06-ai-agents/05-agent-security/06-secrets-management.md": "3bb47df8df5ca26fd547f10da1ce224774db1f1221797473fa04c480e36d590f",
    "docs/06-ai-agents/05-agent-security/07-data-privacy.md": "1a3782124257c08581cbe58ff95d30e35bf5cb2590ec1c999de42cbfad7550bb",
    "docs/06-ai-agents/05-agent-security/08-agent-sandboxing.md": "159eafedd8ad0c69c7a0e5d21611d4ac14437455f1f3c9f0ec2b3f6e6e51e0e3",
    "docs/06-ai-agents/05-agent-security/09-agent-guardrails.md": "0a5504470720dfecf5f09f3e2033cfa2dddeb02b282775391223032eff7b3b7e",
    "docs/06-ai-agents/05-agent-security/10-agent-risk-management.md": "21f90257476c1e7675ae352661b71e47a36f2bf22363955175265f1d27c2f73c",
    "docs/06-ai-agents/06-agent-deployment/01-agent-deployment-overview.md": "09c112169d8a3856f00eb4152737114f83b1755262dcaa95cbbb897fe89577e2",
    "docs/06-ai-agents/06-agent-deployment/02-agent-runtime-and-execution.md": "2cdd8b8f3f82978bd926f4d796e03fbbf47a34f15006464cff2a1d44d4fe2201",
    "docs/06-ai-agents/06-agent-deployment/03-agent-scaling-and-resilience.md": "e4b767528868fd6bca7d6790dbbe88c2b85f4f250e511a9902cdeabe474e7080",
    "docs/06-ai-agents/06-agent-deployment/04-production-agent-deployment.md": "368142def0868392c76557f04deda87e098dbd623de2e39c0fa77e198242716e",
    "docs/06-ai-agents/index.md": "88cb47bacf4759efccb5ddb4d2e2229352ea22d5063f8dcb86532ce0df94b406",
    "docs/08-ai-engineering-frameworks/a2a-engineering/01-a2a-protocol-engineering-fundamentals.md": "cce4806139e92c306ed9a9b6650cd37e83cc9781c08be71d6b64f9b8b584c93f",
    "docs/08-ai-engineering-frameworks/langgraph/01-langgraph-fundamentals.md": "b00bdf73d74f54fcfd0834a94b4f23ab15df4cf375b39d8f0597089c4f06395c",
    "docs/08-ai-engineering-frameworks/langgraph/02-graph-based-agent-architecture.md": "dbdfe2f12478a9421b46a38a71144acaf6366a35970406c66544b07fc905f357",
    "docs/08-ai-engineering-frameworks/langgraph/03-langgraph-state-and-checkpointing.md": "167c6306bee509187b6836579ad8f08852b8182eff97741c562ed7ff4bb08c2f",
    "docs/08-ai-engineering-frameworks/llamaindex/08-llamaindex-limitations-and-tradeoffs.md": "5522d7f3e536f22b2980ff26a52aabdbcbff66f49ae928b02e9b48f970a246ca",
    "docs/08-ai-engineering-frameworks/mcp-engineering/05-advanced-mcp-capabilities.md": "cc77fa98bbf6318867c398b50aac1f2c74682b8491ea8033815e05c53c846e47",
    "docs/10-cloud-ai-engineering/01-azure-ai/ai-agents/03-integrating-agents-with-mcp-servers.md": "d2aac1cceb768a7b16479c344dcb12f2f8beeb4633d786f4e39dc27d6c258691",
    "docs/10-cloud-ai-engineering/02-aws-ai/data-architecture/02-aws-etl-and-distributed-processing.md": "cd876ba1cfc43ed28d01233c9e6ea0d6a5efb53bafd0bfe2323ecfdd357b17e8",
    "docs/10-cloud-ai-engineering/02-aws-ai/sagemaker-ai-architecture/01-sagemaker-ai-platform-overview.md": "b1809e62dcf1b160f95fc438882a4a6155fd169e87a6bde1d5cb0f09abceb146",
    "docs/10-cloud-ai-engineering/02-aws-ai/sagemaker-ai-architecture/02-training-processing-and-tuning-workflows.md": "30e76e9cd8a89d856b6c8757eb017f93c8e359123c8c6b9de1e723ce13e7804d",
    "docs/10-cloud-ai-engineering/02-aws-ai/sagemaker-ai-architecture/03-model-evaluation-registry-and-approval.md": "c77b0dc7c484e77b996a4138379f935ca589d259b53bc5727e6484d7bd6c4f5d",
    "docs/10-cloud-ai-engineering/index.md": "587a14780d148e34f55e60631751047f8adefbe29a14fb1111cb2982bd4670f5",
    "mkdocs.yaml": "40b8537bd9499a8858dec0763bf593020715fd17c9bffdfe56b33d18879ae280"
}
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
    assert changed == {PAGE, ".github/workflows/e4-qualification.yml", ".github/qualification/check_e4.py"} | set(REPAIR_HASHES), changed
    for path, expected in REPAIR_HASHES.items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected, path
        if path.endswith(".md"):
            pattern = r"(?ms)^```.*?^```[^\n]*"
            assert re.findall(pattern, git("show", f"{BASE}:{path}").decode()) == re.findall(pattern, Path(path).read_text()), path
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
    rag = Elements()
    rag.feed(Path("site/04-retrieval-augmented-generation/index.html").read_text())
    assert "3-rag-fundamentals" in rag.ids
    print(json.dumps({"rendered_page": str(page), "new_section": True, "new_links": True, "home_navigation": True, "repaired_rag_fragment": True}))


def baseline():
    destination = Path(os.environ["RUNNER_TEMP"]) / "e4-repaired-baseline"
    repair = git("diff", BASE, "HEAD", "--", *sorted(REPAIR_HASHES))
    subprocess.run(["git", "worktree", "add", "--detach", str(destination), BASE], check=True)
    subprocess.run(["git", "-C", str(destination), "apply", "-"], input=repair, check=True)
    for path, expected in REPAIR_HASHES.items():
        actual = hashlib.sha256((destination / path).read_bytes()).hexdigest()
        assert actual == expected, path
    assert hashlib.sha256((destination / PAGE).read_bytes()).hexdigest() == SOURCE_HASH
    print(json.dumps({"baseline": "original source plus exact source repairs, no E4 prose", "repair_paths": sorted(REPAIR_HASHES)}), flush=True)
    print("Running mkdocs build --strict in repaired baseline", flush=True)
    subprocess.run(["mkdocs", "build", "--strict"], cwd=destination, check=True)


if __name__ == "__main__":
    {"source": source, "links": links, "rendered": rendered, "baseline": baseline}[sys.argv[1]]()
