#!/usr/bin/env bash
# setup-legacy-reference.sh — idempotently create the v4 legacy reference worktree.
#
# Purpose: check out the pre-refactor v4 code (branch `main`) into
# `.agents/legacy-v4/` as a read-only reference during the v5 refactor
# and test-parity work. See .agents/docs/legacy-reference.md.
#
# This worktree is REFERENCE-ONLY. Do NOT edit, commit, or push from it.
#
# Safe to run repeatedly — exits 0 if the worktree is already set up correctly.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

WORKTREE_PATH=".agents/legacy-v4"
REF="main"

if git worktree list --porcelain | grep -qx "worktree $REPO_ROOT/$WORKTREE_PATH"; then
    echo "OK: legacy reference worktree already present at $WORKTREE_PATH"
    exit 0
fi

if [ -e "$WORKTREE_PATH" ]; then
    echo "ERROR: $WORKTREE_PATH exists but is not a registered git worktree." >&2
    echo "       Remove it or register it manually; refusing to clobber." >&2
    exit 1
fi

echo "Creating legacy reference worktree at $WORKTREE_PATH (ref: $REF)..."
git worktree add "$WORKTREE_PATH" "$REF"
echo "Done. Remember: $WORKTREE_PATH is REFERENCE-ONLY. Do not edit."
