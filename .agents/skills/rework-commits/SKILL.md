---
name: rework-commits
description: >-
  Rework a branch into small semantic commits for review.
  Prefer a single commit when the change is one idea; otherwise
  independent additive commits. Use when the user asks to split,
  rework, rewrite, or clean up commits on a branch before review
  or opening a PR.
---

# Split branch into reviewable commits

Rework a branch into a reviewable commit history before opening or updating a PR.

## Goals

- Prefer **one commit** when the change is a single focused idea (the default for small PRs).
- If multiple commits are needed, make them **independent and additive**: each is a self-contained logical unit. Later commits must not fix, rewrite, or only make sense as patches on earlier commits on the same branch.
- Keep the overall PR focused; do not mix unrelated work.

## Important

- Prepend `GIT_EDITOR=true` to all git commands you run, especially ones looking at diffs, so you avoid getting blocked

## Instructions

1. **Plan the commits**: Read through ALL changes carefully. Decide whether one commit is enough. If not, plan a logical breakdown into small, independent, semantic commits (each should stand alone for review). Write a TODO for each in `/tmp/split-todos.md`.
2. **Create the commits**: Work through the TODOs one by one. Write excellent commit descriptions for human reviewers (capitalized imperative verb; explain the "why").
3. **Cleanup**: Delete temporary files.

## Notes

- Each commit should be self-contained and represent a logical unit of work
- Prefer collapsing WIP, fixups, and "address feedback" noise into clean history before review (unless the user asks to keep follow-up review commits as-is)
- Commit messages should explain the "why" behind the changes
- Align with `docs/about/contributing.md` commit and PR conventions
