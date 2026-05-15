---
name: speckit-git-commit
description: Auto-commit changes after a Spec Kit command completes
compatibility: Requires spec-kit project structure with .specify/ directory
metadata:
  author: github-spec-kit
  source: git:commands/speckit.git.commit.md
---

# Auto-Commit Changes

Automatically stage and commit all changes after a Spec Kit command completes.

## Behavior

This command is invoked as a hook after (or before) core commands. It:

1. Determines the event name from the hook context (e.g., if invoked as an `after_specify` hook, the event is `after_specify`; if `before_plan`, the event is `before_plan`)
2. Checks `.specify/extensions/git/git-config.yml` for the `auto_commit` section
3. Looks up the specific event key to see if auto-commit is enabled
4. Falls back to `auto_commit.default` if no event-specific key exists
5. Uses the per-command `message` if configured, otherwise a default message
6. If enabled and there are uncommitted changes, runs `git add .` + `git commit`

## Execution

1. Determine the event name from the hook context (e.g., `after_implement`, `before_plan`).

2. Read `.specify/extensions/git/git-config.yml` and check whether auto-commit is enabled for this event:
   - Look for `auto_commit.<event_name>.enabled: true`
   - Fall back to `auto_commit.default: true` if no event-specific key exists
   - If disabled or config missing: exit silently

3. Check for uncommitted changes:
   ```bash
   git status --porcelain
   ```
   If no changes: print `[specify] No changes to commit after <event>` and exit.

4. Gather context for the commit message:
   ```bash
   git diff --stat HEAD        # changed files + line counts
   git diff --name-only HEAD   # file list
   ```
   Also consider: the event name, the current branch name, and any task or spec context available in the conversation.

5. **Generate a descriptive commit message** — do NOT use the static `message` from git-config.yml. Write a meaningful message that describes what actually changed:
   - **Subject line** (≤72 chars): use conventional commits format, e.g. `feat(module): beschrijving` or `test(module): beschrijving`
   - **Body** (optional): bullet list of the most relevant changes — new files, key functions/classes added, tests written/passing
   - Base the module/scope on the changed file paths
   - Write in the same language as the rest of the project (Dutch for this project)
   - Example for `after_implement`:
     ```
     feat(ingredient-match): implementeer MatchReview datamodel

     - Voeg MatchReview frozen dataclass toe met status enum
     - Schrijf unit tests voor to_dict/from_dict roundtrip
     - Alle 12 nieuwe tests groen
     ```
   - Example for `before_plan`:
     ```
     chore(spec): sla voortgang op voor planning

     - spec.md bijgewerkt met clarificaties
     ```

6. Stage and commit:
   ```bash
   git add .
   git commit -m "<generated message>"
   ```

## Configuration

In `.specify/extensions/git/git-config.yml`, only `enabled` is used — `message` is ignored in favour of the generated message:

```yaml
auto_commit:
  default: false
  after_implement:
    enabled: true   # message field is ignored; Claude generates it
```

## Graceful Degradation

- If Git is not available or the current directory is not a repository: skips with a warning
- If no config file exists: skips (disabled by default)
- If no changes to commit: skips with a message