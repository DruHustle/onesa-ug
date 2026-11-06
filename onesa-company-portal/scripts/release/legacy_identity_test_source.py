"""Historical public inputs for synthetic tests of the unchanged 014 profile.

This is not a candidate inventory, hosted qualification, or installed authority.
The staging reconciliation preserves this exact ancestor. Tests need full Git
history and fail if it is missing; they never fetch or use a mutable fallback.
"""

import hashlib
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

COMMIT = "8752df4a376d6bd9918a0282e544cde5bbb7a4ea"
TREE = "2965317c18a610fd7a6ccadd9122f04a7bbedf13"
PRODUCT = "onesa-company-portal/"
BACKEND = "onesa-company-portal-backend/"
FRONTEND = "onesa-company-portal-frontend/"
ROOT = Path(__file__).resolve().parents[3]


def _git(*args):
    return subprocess.run(
        ["git", "--no-replace-objects", "--no-lazy-fetch", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


@lru_cache(maxsize=1)
def _entries():
    if _git("show", "-s", "--format=%T", COMMIT).decode().strip() != TREE:
        raise ValueError("Legacy identity fixture tree changed")
    _git("merge-base", "--is-ancestor", COMMIT, "HEAD")
    result = {}
    for entry in _git(
        "ls-tree", "-r", "-z", COMMIT, "--", PRODUCT + BACKEND, PRODUCT + FRONTEND
    ).split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.decode().split("\t", 1)
        mode, kind, oid = metadata.split()
        if mode not in {"100644", "100755"} or kind != "blob":
            raise ValueError("Legacy identity fixture requires regular public blobs")
        if not name.startswith((PRODUCT + BACKEND, PRODUCT + FRONTEND)):
            raise ValueError("Legacy identity fixture path escaped its product")
        result[name.removeprefix(PRODUCT)] = oid
    if not result:
        raise ValueError("Legacy identity fixture is missing")
    return result


@lru_cache(maxsize=None)
def _blob(name):
    return _git("cat-file", "blob", _entries()[name])


def backend_bytes():
    """Return a fresh mapping of exact historical bytes for disposable installers."""
    return {name: _blob(name) for name in _entries() if name.startswith(BACKEND)}


def frontend_inventory(names):
    """Hash actual historical bytes, so the unchanged literal pins are still tested."""
    if any(not name.startswith(FRONTEND) for name in names):
        raise ValueError("Legacy frontend fixture path escaped its product")
    return {name: hashlib.sha256(_blob(name)).hexdigest() for name in names}


if __name__ == "__main__":
    if sys.argv[1:] != ["--migration-sql"]:
        raise SystemExit("Only the historical migration test fixture is available")
    prefix = BACKEND + "migrations/"
    print(json.dumps({
        name.removeprefix(prefix): _blob(name).decode("utf-8")
        for name in _entries() if name.startswith(prefix) and name.endswith(".sql")
    }, sort_keys=True))
