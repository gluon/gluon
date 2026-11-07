#!/usr/bin/env python3
"""Rewrite the block between the releases markers of a README with the
latest published releases of the owner's public, non-fork repositories."""

import json
import os
import sys
import urllib.request

OWNER = os.environ.get("RELEASES_OWNER", "gluon")
LIMIT = int(os.environ.get("RELEASES_LIMIT", "5"))
EXCLUDE = {n.strip() for n in os.environ.get("RELEASES_EXCLUDE", "").split(",") if n.strip()}
START = "<!-- releases:start -->"
END = "<!-- releases:end -->"

QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, privacy: PUBLIC, ownerAffiliations: OWNER,
                 isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        url
        isArchived
        releases(first: 5, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes { tagName url publishedAt isDraft isPrerelease }
        }
      }
    }
  }
}
"""


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {"login": OWNER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{OWNER}-profile-readme",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise SystemExit(f"GraphQL errors: {payload['errors']}")
    return payload["data"]["user"]["repositories"]["nodes"]


def latest(repos):
    rows = []
    for repo in repos:
        if repo["isArchived"] or repo["name"] in EXCLUDE:
            continue
        for rel in repo["releases"]["nodes"]:
            if rel["isDraft"] or rel["isPrerelease"] or not rel["publishedAt"]:
                continue
            rows.append((rel["publishedAt"], repo["name"], repo["url"],
                         rel["tagName"], rel["url"]))
            break
    rows.sort(reverse=True)
    return rows[:LIMIT]


def render(rows):
    if not rows:
        return "_No published release yet._"
    lines = ["| Project | Release | Date |", "|---|---|---|"]
    for published, name, repo_url, tag, rel_url in rows:
        lines.append(f"| [{name}]({repo_url}) | [{tag}]({rel_url}) | {published[:10]} |")
    return "\n".join(lines)


def splice(text, block):
    head, sep, rest = text.partition(START)
    _, sep2, tail = rest.partition(END)
    if not sep or not sep2:
        raise SystemExit(f"Markers {START} / {END} not found")
    return f"{head}{START}\n{block}\n{END}{tail}"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    new = splice(text, render(latest(fetch(token))))
    if new != text:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"{path} updated")
    else:
        print(f"{path} unchanged")


if __name__ == "__main__":
    main()
