# Legacy v4 reference worktree — READ-ONLY

## Purpose

During the v5 refactor (especially the test-parity pass following `phase-6-gate`), we need easy side-by-side access to the pre-refactor v4 code. Rather than constantly switching branches or cloning a second copy, we use a **git worktree** to check out `main` (v4) at a sibling path inside this repo: `.agents/legacy-v4/`.

## Strict rules

- **NEVER edit** files under `.agents/legacy-v4/`.
- **NEVER `git commit`** from inside it.
- **NEVER `git push`** from inside it.
- **NEVER create new branches** from inside it.
- Treat it as a petrified copy. Read, grep, copy-paste-adapt into `opgee/` — that's it.

If you need to update the reference (e.g. `main` moved), do it explicitly: `cd .agents/legacy-v4 && git pull --ff-only origin main` — only after confirming the new state.

## Setup

Idempotent. Safe to run repeatedly:

```bash
./scripts/setup-legacy-reference.sh
```

This runs `git worktree add .agents/legacy-v4 main` on first invocation; on subsequent runs it verifies the worktree is already present and exits 0.

## Layout

```
current/                      ← this repo (refactor/v5-deep-clean)
└── .agents/
    └── legacy-v4/           ← worktree at main (v4 code). Gitignored.
```

`.agents/legacy-v4/` is listed in this repo's `.gitignore` so its contents never appear as untracked files in `git status`. Git's worktree mechanism ensures the nested checkout's files never become part of the parent branch's tree.

## Why a worktree, not a submodule

A submodule would require pointing at an external repo URL and re-cloning the entire history into a subdirectory — wasteful when v4 already lives at `main` of this same repo. A worktree shares this repo's object store: second checkout, zero extra disk for history.

## Teardown (if needed)

```bash
git worktree remove .agents/legacy-v4
```
