#!/usr/bin/env python3
"""Fetch the live public GitHub metrics shown in the profile card."""
import json
import os
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_PROFILE_USER", "dev-rehaann")
TOKEN = os.environ.get("GH_TOKEN", "")
QUERY = """
query($login:String!) {
  user(login:$login) {
    followers { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC) {
      totalCount nodes { stargazerCount }
    }
    contributionsCollection {
      totalCommitContributions
    }
  }
}
"""

response = requests.post(
    "https://api.github.com/graphql",
    headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "dev-rehaann-profile"},
    json={"query": QUERY, "variables": {"login": USER}}, timeout=30,
)
response.raise_for_status()
payload = response.json()
if payload.get("errors"):
    raise RuntimeError(payload["errors"])
user = payload["data"]["user"]
repos = user["repositories"]
data = {
    "repos": repos["totalCount"],
    "stars": sum(repo["stargazerCount"] for repo in repos["nodes"]),
    "commits_year": user["contributionsCollection"]["totalCommitContributions"],
    "followers": user["followers"]["totalCount"],
}
output = json.dumps(data, indent=2) + "\n"
if os.environ.get("PROFILE_STATS_STDOUT"):
    print(output, end="")
else:
    (ROOT / "data" / "profile_stats.json").write_text(output, encoding="utf-8")
    print(json.dumps(data))
