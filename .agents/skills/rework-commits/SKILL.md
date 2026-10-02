---
name: rework-commits
description: >-
  Rework a branch into small semantic commits for review.
  Use when the user asks to split, rework, rewrite, or clean up
  commits on a branch before review or opening a PR.
---

# Split branch into reviewable commits

Rework a branch into a sequence of small, semantic commits for review.

## Important

- Prepend `GIT_EDITOR=true` to all git commands you run, especially ones looking at diffs, so you avoid getting blocked

## Instructions

1. **Plan the commits**: Read through ALL changes carefully. Plan a logical breakdown into small, sequential, semantic commits. Write a TODO for each in `/tmp/split-todos.md`.
2. **Create the commits**: Work through the TODOs one by one. Write excellent commit descriptions for human reviewers.
3. **Cleanup**: Delete temporary files.

## Notes

- Each commit should be self-contained and represent a logical unit of work
- Commit messages should explain the "why" behind the changes
