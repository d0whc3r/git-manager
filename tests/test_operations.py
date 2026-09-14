"""The three mutating actions: update, merge, discard."""

import os

import pytest

from conftest import commit, init_repo, sh
from git_manager import git as gm


def test_update_fast_forwards_the_checked_out_default(tmp_path, upstream, clone):
    commit(upstream, "second")
    ok, _ = gm.update_default(clone)
    assert ok
    assert gm.status(clone, tmp_path)[4:] == ("0", "0")


def test_update_leaves_your_feature_branch_alone(tmp_path, upstream, clone):
    """The default branch ref advances, but the working tree stays on the feature branch."""
    sh("git", "checkout", "-q", "-b", "feature", cwd=clone)
    commit(clone, "wip", "wip.txt", "work in progress\n")
    commit(upstream, "theirs")

    ok, _ = gm.update_default(clone)

    assert ok
    assert gm.current_branch(clone) == "feature"
    assert (clone / "wip.txt").read_text() == "work in progress\n"
    assert gm.status(clone, tmp_path)[4:] == ("1", "1")


def test_update_refuses_to_rewrite_a_diverged_default(upstream, clone):
    """Fast-forward only: a local commit on the default branch blocks the update."""
    commit(clone, "local only")
    commit(upstream, "theirs")
    ok, msg = gm.update_default(clone)
    assert not ok
    assert msg


def test_update_without_a_default_branch(tmp_path):
    repo = init_repo(tmp_path / "odd", branch="develop")
    assert gm.update_default(repo) == (False, "no default branch")


def test_update_reports_a_failing_fetch(clone):
    sh("git", "remote", "set-url", "origin", "/nonexistent/repo.git", cwd=clone)
    ok, msg = gm.update_default(clone)
    assert not ok
    assert msg.startswith("fetch failed:")


def test_merge_brings_the_default_into_your_branch(tmp_path, upstream, clone):
    sh("git", "checkout", "-q", "-b", "feature", cwd=clone)
    commit(clone, "mine", "mine.txt", "my work\n")
    commit(upstream, "theirs", "theirs.txt", "from the team\n")

    ok, _ = gm.merge_default(clone)

    assert ok
    assert (clone / "theirs.txt").read_text() == "from the team\n"
    assert (clone / "mine.txt").read_text() == "my work\n"
    assert gm.status(clone, tmp_path)[4] == "0"


def test_merge_reports_a_conflict_instead_of_guessing(upstream, clone):
    sh("git", "checkout", "-q", "-b", "feature", cwd=clone)
    commit(clone, "mine", "README.md", "mine\n")
    commit(upstream, "theirs", "README.md", "theirs\n")

    ok, msg = gm.merge_default(clone)

    assert not ok
    assert "CONFLICT" in msg or "conflict" in msg


def test_merge_without_a_default_branch(tmp_path):
    repo = init_repo(tmp_path / "odd", branch="develop")
    assert gm.merge_default(repo) == (False, "no default branch")


def test_discard_restores_modified_files_and_removes_untracked(clone):
    (clone / "README.md").write_text("ruined\n")
    (clone / "junk.txt").write_text("x")
    (clone / "junkdir").mkdir()
    (clone / "junkdir" / "more.txt").write_text("x")

    ok, _ = gm.discard(clone)

    assert ok
    assert (clone / "README.md").read_text() == "hello\n"
    assert not (clone / "junk.txt").exists()
    assert not (clone / "junkdir").exists()


def test_discard_keeps_committed_work(tmp_path, clone):
    """It throws away uncommitted changes only — commits are never touched."""
    commit(clone, "mine", "kept.txt", "keep me\n")
    (clone / "kept.txt").write_text("ruined\n")

    gm.discard(clone)

    assert (clone / "kept.txt").read_text() == "keep me\n"
    assert gm.status(clone, tmp_path)[4:] == ("0", "1")


def test_update_without_a_remote_says_so(tmp_path):
    """A local-only repository has nothing to update from — say that, not git's raw complaint."""
    repo = init_repo(tmp_path / "solo")
    assert gm.update_default(repo) == (False, "no remote to update from")


def test_merge_without_a_remote_uses_the_local_default(tmp_path):
    """No origin, so the local default branch is what gets merged in."""
    repo = init_repo(tmp_path / "solo")
    commit(repo, "theirs", "theirs.txt", "from main\n")
    sh("git", "checkout", "-q", "-b", "feature", "HEAD~1", cwd=repo)

    ok, _ = gm.merge_default(repo)

    assert ok
    assert (repo / "theirs.txt").read_text() == "from main\n"


def test_merge_reports_a_failing_fetch_instead_of_merging_a_stale_ref(clone):
    sh("git", "remote", "set-url", "origin", "/nonexistent/repo.git", cwd=clone)
    ok, msg = gm.merge_default(clone)
    assert not ok
    assert msg.startswith("fetch failed:")


def test_discard_reports_failure_instead_of_claiming_success(tmp_path):
    """The destructive action must never log "discarded" when git refused."""
    ok, msg = gm.discard(tmp_path)
    assert not ok
    assert msg.startswith("reset failed:")


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores the permissions this relies on")
def test_discard_reports_a_clean_that_could_not_finish(clone):
    """Files survived the clean, so the result must not read as success."""
    junk = clone / "locked"
    junk.mkdir()
    (junk / "file").write_text("x")
    junk.chmod(0o500)
    try:
        ok, msg = gm.discard(clone)
    finally:
        junk.chmod(0o700)

    assert not ok
    assert msg.startswith("clean failed:")
