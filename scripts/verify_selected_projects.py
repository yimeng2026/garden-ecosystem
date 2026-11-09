"""Verify exact public GitHub repositories; do not equate metadata with code review."""
import concurrent.futures
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAMES = [
    "microsoft/agent-framework", "microsoft/autogen", "microsoft/semantic-kernel",
    "microsoft/TinyTroupe", "microsoft/AI2BMD", "microsoft/mattergen", "microsoft/BioEmu",
    "microsoft/aurora", "microsoft/promptflow",
    "langchain-ai/langgraph", "crewAIInc/crewAI", "camel-ai/camel", "camel-ai/oasis",
    "geekan/MetaGPT", "agentscope-ai/agentscope", "agentscope-ai/agentscope-runtime",
    "agentscope-ai/ReMe", "agentscope-ai/agentscope-java", "OpenBMB/AgentVerse",
    "OpenBMB/ChatDev", "All-Hands-AI/OpenHands", "FoundationAgents/OpenManus",
    "666ghj/MiroFish", "tsinghua-fib-lab/AgentSociety", "SolaceLabs/solace-agent-mesh",
    "e2b-dev/e2b", "NVIDIA/NeMo-Guardrails", "guardrails-ai/guardrails",
    "Arize-ai/phoenix", "langfuse/langfuse", "BerriAI/litellm", "Portkey-AI/gateway",
    "volcengine/OpenViking", "mem0ai/mem0", "topoteretes/cognee", "letta-ai/letta",
    "run-llama/llama_index", "deepset-ai/haystack", "pydantic/pydantic-ai",
    "ComposioHQ/composio", "openai/openai-agents-python", "google/adk-python",
    "SakanaAI/AI-Scientist", "google-deepmind/funsearch", "google-deepmind/alphafold3",
    "facebookresearch/vjepa2", "facebookresearch/fairchem", "lean-dojo/LeanDojo",
    "lean-dojo/LeanCopilot", "leanprover-community/repl", "leanprover/Pantograph",
    "stanford-centaur/PyPantograph", "ulamai/ulamai", "ruc-datalab/DeepAnalyze",
    "zjunlp/SciAtlas", "ai4s-research/open-science", "K-Dense-AI/scientific-agent-skills",
    "ai4s-research/awesome-ai-for-science", "synthetic-sciences/openscience",
]


def fetch(name: str) -> dict:
    url = f"https://api.github.com/repos/{name}"
    request = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json", "User-Agent": "garden-ecosystem-research/0.1"
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            repo = json.load(response)
        return {
            "name": repo["full_name"], "url": repo["html_url"],
            "description": repo.get("description"), "license": (repo.get("license") or {}).get("spdx_id"),
            "language": repo.get("language"), "default_branch": repo.get("default_branch"),
            "created_at": repo.get("created_at"), "pushed_at": repo.get("pushed_at"),
            "stars": repo.get("stargazers_count"), "fork": repo.get("fork"),
            "archived": repo.get("archived"), "size_kib": repo.get("size"),
            "metadata_verified": True, "source_code_reviewed": False,
        }
    except urllib.error.HTTPError as error:
        return {"name": name, "url": f"https://github.com/{name}", "metadata_verified": False,
                "error": f"HTTP {error.code}", "source_code_reviewed": False}
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        return {"name": name, "url": f"https://github.com/{name}", "metadata_verified": False,
                "error": f"{type(error).__name__}: {error}", "source_code_reviewed": False}


def main() -> None:
    path = ROOT / "research" / "selected-github-projects.json"
    previous = []
    if path.exists():
        previous = json.loads(path.read_text(encoding="utf-8"))
    # Retry only earlier transport failures once; successful reads are not repeated.
    missing = [row["name"] for row in previous if not row["metadata_verified"]]
    requested = missing or NAMES if previous else NAMES
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        fetched = list(executor.map(fetch, requested))
    rows = list({row["name"]: row for row in previous + fetched}.values())
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for row in rows:
        print(f"{row['name']} | {row.get('license') or row.get('error')} | {row.get('pushed_at', 'not verified')}")
    print(f"Verified {sum(row['metadata_verified'] for row in rows)}/{len(rows)} exact repositories")


if __name__ == "__main__":
    main()
