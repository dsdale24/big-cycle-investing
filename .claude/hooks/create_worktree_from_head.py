#!/usr/bin/env python3
"""WorktreeCreate hook: branch new worktrees from the current HEAD.

Claude Code's default behavior branches worktrees from origin/HEAD (the
remote default branch, typically main) regardless of which branch the
coordinator is on. That's wrong for this project's maker-checker workflow:
when the coordinator delegates from a feature branch with in-progress spec
updates or intermediate commits, the agent must see those updates.

This hook replaces the default with `git worktree add <path> HEAD` so the
worktree is based at whatever the coordinator currently has checked out.

Input (stdin): JSON with .worktree_path and .cwd (see Claude Code hook docs).
Output (stdout): the absolute worktree path, on success.
Exit: 0 on success, non-zero to abort worktree creation.

Cross-platform: stdlib only, no jq or bash required.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as err:
        print(f"create_worktree_from_head: invalid JSON on stdin: {err}", file=sys.stderr)
        return 1

    worktree_path = payload.get("worktree_path")
    project_cwd = payload.get("cwd")
    if not worktree_path or not project_cwd:
        print(
            "create_worktree_from_head: payload missing worktree_path or cwd. "
            f"Keys received: {sorted(payload.keys())}",
            file=sys.stderr,
        )
        return 1

    # worktree_name may or may not be present depending on how the worktree is
    # being created. Fall back to deriving it from the path's final component so
    # the branch always has a name.
    worktree_name = payload.get("worktree_name") or os.path.basename(worktree_path)

    # Match Claude Code's default branch-naming convention (worktree-<name>).
    # Without -b, the worktree is detached-HEAD and any commits the agent
    # makes are not reachable from a named branch.
    branch_name = f"worktree-{worktree_name}"
    result = subprocess.run(
        ["git", "worktree", "add", "-b", branch_name, worktree_path, "HEAD"],
        cwd=project_cwd,
        stdout=sys.stderr,
        stderr=sys.stderr,
    )
    if result.returncode != 0:
        print(
            f"create_worktree_from_head: git worktree add failed for {worktree_path}",
            file=sys.stderr,
        )
        return result.returncode

    print(worktree_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
