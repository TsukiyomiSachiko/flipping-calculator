---
trigger: always_on
---

# Pull Request Automation Rule

## Context
Always create a Pull Request on GitHub when a feature, optimization, or bug fix branch is completed and ready for merge. This rule takes effect after all development work, verification, and testing are done.

## Pre-conditions
Before running this automation:
1. Ensure all changes are committed and pushed to the current remote branch.
2. Confirm that the entire test suite (e.g., `pytest`) passes without errors.
3. Verify that the current branch is up-to-date with `main`.

## Instruction
When all pre-conditions are met, automatically create a Pull Request to the `main` branch using the GitHub CLI (`gh`).
Run the following command in WSL:
```bash
wsl gh pr create --base main --head $(wsl git branch --show-current) --title "<title>" --body "<body>"
```

## Never Do
Merge pull requests on your own without specific instruction to merge it