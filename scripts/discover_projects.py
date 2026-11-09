"""Collect public project metadata without credentials or downloading source code.

The result is a discovery aid, not proof of quality or permission to copy.
"""
from __future__ import annotations

import concurrent.futures
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "research" / "raw"
QUERIES = {
    "github": [
        "topic:multi-agent", "topic:agent-framework", "topic:agentic-ai",
        "topic:world-model", "topic:llm-agent", "topic:agent-memory",
        "AI scientist in:name,description,readme",
        "agent guardrails in:name,description,readme",
        "formal theorem proving agent in:name,description,readme",
        "multi agent simulation in:name,description,readme",
    ],
    # Gitee's public search endpoint returned [] even for some known projects.
    # Keep the empty responses as evidence; supplement them with direct repository reads.
    "gitee": ["多智能体", "智能体框架", "世界模型", "科学智能体", "AgentScope"],
    # GitLab uses `search`, not `q`; sorting by activity hid relevant small projects.
    "gitlab": ["multi agent", "agent framework", "world model", "scientific agent"],
    # Codeberg phrase search is restrictive; use both generic and hyphenated variants.
    "codeberg": ["agent", "multi-agent", "agent framework", "world-model"],
    "huggingface": ["world model", "agent", "theorem proving"],
}


def endpoint(site: str, query: str) -> str:
    encoded = urllib.parse.urlencode({"q": query, "per_page": 50})
    if site == "github":
        return f"https://api.github.com/search/repositories?{encoded}&sort=updated"
    if site == "gitee":
        return f"https://gitee.com/api/v5/search/repositories?{encoded}"
    if site == "gitlab":
        return f"https://gitlab.com/api/v4/projects?{urllib.parse.urlencode({'search': query, 'per_page': 50})}&simple=true&order_by=star_count&sort=desc"
    if site == "codeberg":
        return f"https://codeberg.org/api/v1/repos/search?{urllib.parse.urlencode({'q': query, 'limit': 50})}"
    return f"https://huggingface.co/api/models?{urllib.parse.urlencode({'search': query, 'limit': 50, 'full': 'true'})}"


def fetch(site: str, query: str) -> dict:
    url = endpoint(site, query)
    request = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "garden-ecosystem-research/0.1"
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
        return {"site": site, "query": query, "url": url, "ok": True, "data": data}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        return {"site": site, "query": query, "url": url, "ok": False,
                "error": f"{type(error).__name__}: {error}"}


def items(site: str, payload: object) -> list[dict]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        return payload["items"]
    if site == "codeberg" and isinstance(payload, dict):
        return payload.get("data") or []
    return []


def normalize(site: str, query: str, item: dict) -> dict:
    if site == "github":
        name, url = item.get("full_name"), item.get("html_url")
        license_value = (item.get("license") or {}).get("spdx_id")
        updated, stars = item.get("pushed_at"), item.get("stargazers_count")
    elif site == "gitee":
        name = item.get("full_name") or item.get("path")
        url = item.get("html_url")
        license_value, updated, stars = item.get("license"), item.get("pushed_at"), item.get("stargazers_count")
    elif site == "gitlab":
        name, url = item.get("path_with_namespace"), item.get("web_url")
        license_value, updated, stars = None, item.get("last_activity_at"), item.get("star_count")
    elif site == "codeberg":
        name, url = item.get("full_name"), item.get("html_url")
        license_value, updated, stars = item.get("license"), item.get("updated_at"), item.get("stars_count")
    else:
        name = item.get("modelId") or item.get("id")
        url = f"https://huggingface.co/{name}" if name else None
        tags = item.get("tags") or []
        license_value = next((str(x).split(":", 1)[1] for x in tags if str(x).startswith("license:")), None)
        updated, stars = item.get("lastModified"), item.get("likes")
    return {
        "site": site, "query": query, "name": name, "url": url,
        "description": item.get("description"), "license": license_value or "not_verified",
        "updated_at": updated, "stars_or_likes": stars,
        "language": item.get("language"), "fork": item.get("fork"),
        "archived": item.get("archived"), "verification": "metadata_only",
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    jobs = [(site, query) for site, queries in QUERIES.items() for query in queries]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda job: fetch(*job), jobs))
    catalog = []
    for index, result in enumerate(results):
        (RAW / f"{result['site']}-{index:02d}.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if result["ok"]:
            catalog.extend(normalize(result["site"], result["query"], item)
                             for item in items(result["site"], result["data"]))
        print(f"{result['site']} | {result['query']} | {'ok' if result['ok'] else result['error']}")
    unique = list({(row["site"], row["name"]): row for row in catalog if row["name"]}.values())
    unique.sort(key=lambda row: (row["site"], row["name"].lower()))
    summary = {
        "scope": "Public discovery queries; neither an exhaustive census nor a quality certification",
        "queries": [{"site": r["site"], "query": r["query"], "ok": r["ok"],
                     **({} if r["ok"] else {"error": r["error"]})} for r in results],
        "records_before_deduplication": len(catalog),
        "unique_projects_or_models": len(unique),
        "projects": unique,
    }
    (ROOT / "research" / "project-catalog.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in summary.items() if key not in {"projects", "queries"}},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
