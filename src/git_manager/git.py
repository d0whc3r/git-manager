"""Git domain: repository discovery and read-only inspection.

Everything here shells out to the `git` binary and returns plain data. No UI, no state.
"""

import subprocess
from pathlib import Path

#: Folder names never descended into while scanning.
SKIP = {"node_modules", "venv", ".venv", "target", "vendor", "Library"}

#: How many levels below the scan root to look for repositories.
MAX_DEPTH = 6

#: Seconds a single git command may run before it is given up on. A fetch against an
#: unreachable remote is the case this exists for.
TIMEOUT = 120


def git(repo, *args, timeout=TIMEOUT):
    """Run `git -C <repo> <args>`. Returns (returncode, stdout, stderr), both streams stripped.

    A hung or missing git is reported as a failing return code, never raised, so one bad
    repository cannot abort a batch of them.
    """
    # S603/S607: resolving `git` from PATH is deliberate — the tool documents `git` as its one
    # external requirement, and every argument here is built by this module, never by user input.
    try:
        p = subprocess.run(  # noqa: S603
            ["git", "-C", str(repo), *args],  # noqa: S607
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return 1, "", f"timed out after {timeout}s"
    except FileNotFoundError:
        return 1, "", "git not found on PATH"
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def find_repos(root, max_depth=MAX_DEPTH):
    """Return every git repository under `root`, nearest first.

    Descent continues past a repository, so submodules and other nested checkouts are listed
    alongside their parent.
    """
    root = Path(root)
    found = []

    def walk(d, depth):
        if (d / ".git").exists():
            found.append(d)
        if depth >= max_depth:
            return
        try:
            entries = sorted(d.iterdir())
        except OSError:
            return
        for e in entries:
            if (
                e.is_dir()
                and not e.is_symlink()
                and e.name not in SKIP
                and not e.name.startswith(".")
            ):
                walk(e, depth + 1)

    walk(root, 0)
    return found


def has_ref(repo, ref):
    """True when `ref` resolves in `repo`. Accepts any revision git understands."""
    return git(repo, "rev-parse", "--verify", "--quiet", ref)[0] == 0


def current_branch(repo):
    """Name of the checked-out branch, "HEAD" when detached, or "?" when unreadable."""
    return git(repo, "rev-parse", "--abbrev-ref", "HEAD")[1] or "?"


def default_branch(repo):
    """Default branch name from `origin/HEAD`, falling back to `main` then `master`.

    Returns "" when none of those exist.
    """
    rc, out, _ = git(repo, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    if rc == 0 and out:
        return out.rsplit("/", 1)[-1]
    for b in ("main", "master"):
        if has_ref(repo, f"refs/heads/{b}"):
            return b
    return ""


def _remote_default_ref(repo, default):
    """`origin/<default>` when that remote-tracking ref exists, None for a repo without one."""
    ref = f"origin/{default}"
    return ref if has_ref(repo, f"refs/remotes/{ref}") else None


def status(repo, root):
    """One table row for `repo`: (path, branch, default, state, behind, ahead).

    `behind`/`ahead` compare the current branch against `origin/<default>`, or the local
    default branch when the remote-tracking ref is missing. Unknown values render as "-".
    """
    branch = current_branch(repo)
    default = default_branch(repo)
    dirty = "dirty" if git(repo, "status", "--porcelain")[1] else "-"

    behind = ahead = "-"
    if default:
        ref = _remote_default_ref(repo, default) or default
        rc, out, _ = git(repo, "rev-list", "--left-right", "--count", f"{ref}...HEAD")
        if rc == 0 and len(out.split()) == 2:
            behind, ahead = out.split()
    return (str(repo.relative_to(root)), branch, default or "?", dirty, behind, ahead)


def update_default(repo):
    """Fetch, then bring the local default branch up to date. Returns (ok, message).

    Fast-forward only: if the default branch has diverged locally, this reports the failure
    instead of creating a merge commit.
    """
    rc, _, err = git(repo, "fetch", "--all", "--prune")
    if rc:
        return False, f"fetch failed: {err}"

    default = default_branch(repo)
    if not default:
        return False, "no default branch"
    ref = _remote_default_ref(repo, default)
    if not ref:
        return False, "no remote to update from"

    # On the default branch git has to move the working tree; anywhere else the ref is
    # advanced directly, leaving the checked-out branch untouched.
    if current_branch(repo) == default:
        rc, out, err = git(repo, "merge", "--ff-only", ref)
    else:
        rc, out, err = git(repo, "fetch", "origin", f"{default}:{default}")
    return rc == 0, out or err or "up to date"


def merge_default(repo):
    """Merge the default branch into the checked-out branch. Returns (ok, message).

    Uses `origin/<default>` when the repository has a remote, the local branch otherwise.
    Leaves conflicts in place for the user to resolve outside this tool.
    """
    default = default_branch(repo)
    if not default:
        return False, "no default branch"

    ref = _remote_default_ref(repo, default)
    if ref:
        rc, _, err = git(repo, "fetch", "origin", default)
        if rc:
            return False, f"fetch failed: {err}"

    rc, out, err = git(repo, "merge", ref or default)
    return rc == 0, out or err or "merged"


def discard(repo):
    """Throw away every uncommitted change and untracked file. Destructive, not undoable."""
    rc, _, err = git(repo, "reset", "--hard")
    if rc:
        return False, f"reset failed: {err}"

    rc, _, err = git(repo, "clean", "-fd")
    if rc:
        return False, f"clean failed: {err}"
    return True, "discarded"
