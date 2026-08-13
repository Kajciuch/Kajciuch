#!/usr/bin/env python3
"""Zbiera statystyki jezykow ze wszystkich publicznych repozytoriow.

Liczby sa te same, ktore GitHub pokazuje na pasku jezykow w kazdym repo -
bajty rozpoznane przez linguist. Notebooki wychodza duze, bo trzymaja w sobie
zapisane wyjscia komorek; tak samo liczy je GitHub.

    python3 fetch_stats.py stats.json
"""

import collections
import json
import os
import subprocess
import sys

OWNER = os.environ.get("GITHUB_REPOSITORY_OWNER", "Kajciuch")


def gh(path: str, paginate: bool = False):
    # --paginate tylko dla list; na endpoincie zwracajacym obiekt gh sklejalby
    # kolejne strony w niepoprawny JSON
    out = subprocess.run(
        ["gh", "api", path] + (["--paginate"] if paginate else []),
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def own_repositories() -> list:
    repos = gh(f"/users/{OWNER}/repos?per_page=100", paginate=True)
    return [r["name"] for r in repos if not r["fork"]]


def collect() -> dict:
    repos = own_repositories()
    languages = collections.Counter()
    for name in repos:
        languages.update(gh(f"/repos/{OWNER}/{name}/languages"))
    return {"repos": len(repos), "languages": dict(languages)}


def main(path: str) -> None:
    stats = collect()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(stats, handle, ensure_ascii=False, indent=2)
    total = sum(stats["languages"].values())
    print(
        f"{path}: {stats['repos']} repo, {len(stats['languages'])} jezykow, "
        f"{total / 1e6:.2f} MB"
    )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "stats.json")
