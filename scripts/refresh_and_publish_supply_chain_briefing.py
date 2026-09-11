#!/usr/bin/env python3
"""Refresh the SupplyX briefing and publish it from a local scheduled task."""

from pathlib import Path
import subprocess
import sys


REPO_ROOT = Path(__file__).parents[1]
BRIEFING = "supplyx/daily-briefing.html"


def run(*command, check=True):
    print("+", " ".join(command))
    return subprocess.run(command, cwd=REPO_ROOT, check=check)


def main():
    # Preserve unrelated local work, such as the requirements workbook, while syncing.
    run("git", "pull", "--rebase", "--autostash", "origin", "main")
    run(sys.executable, "scripts/build_supply_chain_briefing.py")
    run("git", "add", BRIEFING)

    changes_pending = run("git", "diff", "--cached", "--quiet", check=False).returncode != 0
    if not changes_pending:
        print("Briefing is already current; nothing to publish.")
        return

    run("git", "commit", "-m", "Refresh supply chain daily briefing")
    run("git", "push", "origin", "main")
    print("SupplyX briefing published.")


if __name__ == "__main__":
    main()