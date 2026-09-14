"""Finding repositories, and working out which branch is which."""

from conftest import commit, init_repo, sh
from git_manager import git as gm


def test_finds_nested_repos_sorted(tmp_path, upstream, clone):
    assert gm.find_repos(tmp_path) == [clone, upstream]


def test_lists_repos_nested_inside_a_repo(tmp_path, upstream):
    """A repository inside a repository gets its own row, so submodules are listed too."""
    nested = init_repo(upstream / "vendored")
    assert gm.find_repos(tmp_path) == [upstream, nested]


def test_skips_noise_folders_and_dotfolders(tmp_path):
    for name in ("node_modules", ".venv", "target", ".cache"):
        init_repo(tmp_path / name / "repo")
    wanted = init_repo(tmp_path / "real")
    assert gm.find_repos(tmp_path) == [wanted]


def test_respects_max_depth(tmp_path):
    deep = init_repo(tmp_path / "a" / "b" / "c" / "repo")
    assert gm.find_repos(tmp_path, max_depth=2) == []
    assert gm.find_repos(tmp_path, max_depth=4) == [deep]


def test_root_that_is_itself_a_repo(upstream):
    assert gm.find_repos(upstream) == [upstream]


def test_unreadable_folder_is_skipped_not_fatal(tmp_path, monkeypatch):
    """A folder we cannot list must not abort the whole scan."""
    init_repo(tmp_path / "repo")
    (tmp_path / "locked").mkdir()
    original = type(tmp_path).iterdir

    def explode(self):
        if self.name == "locked":
            raise PermissionError(self)
        return original(self)

    monkeypatch.setattr(type(tmp_path), "iterdir", explode)
    assert gm.find_repos(tmp_path) == [tmp_path / "repo"]


def test_default_branch_from_origin_head(clone):
    assert gm.default_branch(clone) == "main"


def test_default_branch_falls_back_to_local_main(upstream):
    """No origin at all, so the name has to come from the local branches."""
    assert gm.default_branch(upstream) == "main"


def test_default_branch_falls_back_to_master(tmp_path):
    repo = init_repo(tmp_path / "old", branch="master")
    assert gm.default_branch(repo) == "master"


def test_default_branch_empty_when_there_is_none(tmp_path):
    repo = init_repo(tmp_path / "odd", branch="develop")
    assert gm.default_branch(repo) == ""


def test_current_branch(clone):
    sh("git", "checkout", "-q", "-b", "feature", cwd=clone)
    assert gm.current_branch(clone) == "feature"


def test_current_branch_when_detached(clone):
    commit(clone, "second")
    sh("git", "checkout", "-q", "--detach", "HEAD~1", cwd=clone)
    assert gm.current_branch(clone) == "HEAD"


def test_a_hung_git_command_fails_instead_of_raising(clone):
    """One slow repository must not take down a whole batch with an exception."""
    rc, out, err = gm.git(clone, "log", timeout=0.000001)
    assert (rc, out) == (1, "")
    assert "timed out" in err


def test_a_missing_git_binary_fails_instead_of_raising(clone, monkeypatch):
    def no_git(*args, **kwargs):
        raise FileNotFoundError(2, "No such file or directory", "git")

    monkeypatch.setattr("subprocess.run", no_git)
    assert gm.git(clone, "status") == (1, "", "git not found on PATH")
