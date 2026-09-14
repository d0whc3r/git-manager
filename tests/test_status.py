"""The six columns shown for each repository."""

from conftest import commit, init_repo, sh
from git_manager import git as gm


def test_clean_clone_is_level_with_its_default(tmp_path, clone):
    assert gm.status(clone, tmp_path) == ("a/b/repo", "main", "main", "-", "0", "0")


def test_path_is_relative_to_the_scan_root(clone):
    assert gm.status(clone, clone.parent)[0] == "repo"


def test_behind_counts_commits_only_the_default_has(tmp_path, upstream, clone):
    commit(upstream, "second")
    sh("git", "fetch", "-q", cwd=clone)
    assert gm.status(clone, tmp_path)[4:] == ("1", "0")


def test_ahead_counts_commits_only_we_have(tmp_path, clone):
    commit(clone, "mine")
    assert gm.status(clone, tmp_path)[4:] == ("0", "1")


def test_diverged_branches_report_both_sides(tmp_path, upstream, clone):
    commit(upstream, "theirs")
    commit(clone, "mine")
    sh("git", "fetch", "-q", cwd=clone)
    assert gm.status(clone, tmp_path)[4:] == ("1", "1")


def test_modified_tracked_file_is_dirty(tmp_path, clone):
    (clone / "README.md").write_text("changed\n")
    assert gm.status(clone, tmp_path)[3] == "dirty"


def test_untracked_file_is_dirty(tmp_path, clone):
    (clone / "scratch.txt").write_text("x")
    assert gm.status(clone, tmp_path)[3] == "dirty"


def test_staged_change_is_dirty(tmp_path, clone):
    (clone / "new.txt").write_text("x")
    sh("git", "add", "new.txt", cwd=clone)
    assert gm.status(clone, tmp_path)[3] == "dirty"


def test_no_default_branch_leaves_the_comparison_blank(tmp_path):
    """`?` for the name and `-` for the counts, rather than a wrong number."""
    repo = init_repo(tmp_path / "odd", branch="develop")
    assert gm.status(repo, tmp_path) == ("odd", "develop", "?", "-", "-", "-")


def test_falls_back_to_the_local_default_without_a_remote(tmp_path, upstream):
    """No origin, so the comparison uses the local default branch instead."""
    sh("git", "checkout", "-q", "-b", "feature", cwd=upstream)
    commit(upstream, "work")
    assert gm.status(upstream, tmp_path) == ("upstream", "feature", "main", "-", "0", "1")
