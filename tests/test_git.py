"""Self-check for the git domain layer: `make test`.

Creates throwaway repositories in a temp folder and asserts discovery, default branch
detection, and the dirty/behind/ahead columns. Touches nothing outside that folder.
"""

import subprocess
import tempfile
from pathlib import Path

from git_manager import git as gm


def sh(*a, cwd=None):
    subprocess.run(a, cwd=cwd, check=True, capture_output=True)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        upstream = root / "upstream"
        upstream.mkdir()
        sh("git", "init", "-q", "-b", "main", cwd=upstream)
        sh(
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "init",
            cwd=upstream,
        )

        nested = root / "a" / "b"
        nested.mkdir(parents=True)
        clone = nested / "repo"
        sh("git", "clone", "-q", str(upstream), str(clone))
        (root / "a" / "not_a_repo").mkdir()
        (root / "node_modules").mkdir()

        repos = gm.find_repos(root)
        assert repos == [clone, upstream], repos
        assert gm.default_branch(clone) == "main"

        name, branch, default, dirty, behind, ahead = gm.status(clone, root)
        assert name == "a/b/repo" and branch == "main" and default == "main"
        assert (dirty, behind, ahead) == ("-", "0", "0"), (dirty, behind, ahead)

        # upstream moves ahead -> behind must be 1
        sh(
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "second",
            cwd=upstream,
        )
        sh("git", "fetch", "-q", cwd=clone)
        assert gm.status(clone, root)[4] == "1"

        # dirty detection
        (clone / "x.txt").write_text("x")
        assert gm.status(clone, root)[3] == "dirty"
    print("ok")


main()
