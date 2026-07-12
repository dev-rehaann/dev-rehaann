#!/usr/bin/env python3
"""Fetch Andrew-style GitHub metrics for Rehan's public default branches."""
import json
import os
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
USER = os.environ.get("GH_PROFILE_USER", "dev-rehaann")
TOKEN = os.environ["GH_TOKEN"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "User-Agent": "dev-rehaann-profile"}


def graphql(query, variables):
    response = requests.post("https://api.github.com/graphql", headers=HEADERS,
                             json={"query": query, "variables": variables}, timeout=60)
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


overview = graphql("""
query($login:String!) {
  user(login:$login) {
    id
    followers { totalCount }
    repositories(first:100, ownerAffiliations:OWNER, privacy:PUBLIC) {
      totalCount nodes { nameWithOwner stargazerCount }
    }
    repositoriesContributedTo(first:100, contributionTypes:[COMMIT], includeUserRepositories:true) {
      totalCount nodes { nameWithOwner }
    }
  }
}
""", {"login": USER})["user"]

owned = overview["repositories"]
contributed = overview["repositoriesContributedTo"]
repo_names = {node["nameWithOwner"] for node in owned["nodes"]}
repo_names.update(node["nameWithOwner"] for node in contributed["nodes"])

history_query = """
query($owner:String!, $name:String!, $author:ID!, $cursor:String) {
  repository(owner:$owner, name:$name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first:100, after:$cursor, author:{id:$author}) {
            nodes { additions deletions }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
  }
}
"""
commits = added = removed = 0
for full_name in sorted(repo_names):
    owner, name = full_name.split("/", 1)
    cursor = None
    while True:
        repo = graphql(history_query, {"owner": owner, "name": name, "author": overview["id"], "cursor": cursor})["repository"]
        branch = repo and repo["defaultBranchRef"]
        if not branch:
            break
        history = branch["target"]["history"]
        commits += len(history["nodes"])
        added += sum(node["additions"] for node in history["nodes"])
        removed += sum(node["deletions"] for node in history["nodes"])
        if not history["pageInfo"]["hasNextPage"]:
            break
        cursor = history["pageInfo"]["endCursor"]

data = {
    "repos": owned["totalCount"],
    "stars": sum(repo["stargazerCount"] for repo in owned["nodes"]),
    "contributed_repos": contributed["totalCount"],
    "commits_total": commits,
    "followers": overview["followers"]["totalCount"],
    "loc": added - removed,
    "loc_added": added,
    "loc_removed": removed,
}
output = json.dumps(data, indent=2) + "\n"
if os.environ.get("PROFILE_STATS_STDOUT"):
    print(output, end="")
else:
    (ROOT / "data" / "profile_stats.json").write_text(output, encoding="utf-8")
    print(json.dumps(data))
