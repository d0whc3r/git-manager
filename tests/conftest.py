"""Shared fixtures. Every test runs against throwaway repositories under pytest's tmp_path.

Git is isolated from the machine's real configuration: no global or system config is read, and
identity comes from environment variables, so results do not depend on who runs the suite.
"""

import subprocess

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolate_git(tmp_path_factory):
    """Stop git from reading the developer's own config, and give it a fixed identity."""
    empty = tmp_path_factory.mktemp("gitconfig") / "none"
    env = {
        "GIT_CONFIG_GLOBAL": str(empty),
        "GIT_CONFIG_SYSTEM": str(empty),
        "GIT_AUTHOR_NAME": "test",
        "GIT_AUTHOR_EMAIL": "test@example.invalid",
        "GIT_COMMITTER_NAME": "test",
        "GIT_COMMITTER_EMAIL": "test@example.invalid",
    }
    with pytest.MonkeyPatch.context() as mp:
        for k, v in env.items():
            mp.setenv(k, v)
        yield


def sh(*args, cwd):
    """Run a git command that must succeed, raising with its stderr if it does not."""
    return subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True).stdout


def commit(repo, msg, path=None, content=""):
    """Commit `content` to `path` in `repo`, or an empty commit when `path` is None."""
    if path is None:
        sh("git", "commit", "-q", "--allow-empty", "-m", msg, cwd=repo)
        return
    (repo / path).write_text(content)
    sh("git", "add", path, cwd=repo)
    sh("git", "commit", "-q", "-m", msg, cwd=repo)


def init_repo(path, branch="main"):
    """Create a repository at `path` with one commit on `branch`."""
    path.mkdir(parents=True, exist_ok=True)
    sh("git", "init", "-q", "-b", branch, cwd=path)
    commit(path, "init", "README.md", "hello\n")
    return path


@pytest.fixture
def upstream(tmp_path):
    """A repository other clones are made from, with `main` as its default branch."""
    return init_repo(tmp_path / "upstream")


@pytest.fixture
def clone(tmp_path, upstream):
    """A clone of `upstream`, nested two folders deep under tmp_path."""
    target = tmp_path / "a" / "b" / "repo"
    target.parent.mkdir(parents=True)
    sh("git", "clone", "-q", str(upstream), str(target), cwd=tmp_path)
    return target
