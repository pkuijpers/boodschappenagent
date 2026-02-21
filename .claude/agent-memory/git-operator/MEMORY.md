# Git Operator Memory

## Branch Conventions
- Feature branches use prefix `agent/` for agent-related work (e.g., `agent/frontend`)
- Main branch is `main`

## Commit Style Observed
- Recent commits mix Dutch and English; Dutch preferred for domain descriptions
- Some commits omit conventional commit type prefix (older style): "Recept met spekjes verplaats naar vlees categorie"
- Newer commits use full conventional format with type(scope): description
- Co-authored-by footer used when Claude creates commits

## Scopes in Use
- `ci` — tooling, agent config, CI configuration
- `web` — FastAPI routes, HTMX templates
- `tests` / `e2e` — test files

## Project-Specific Notes
- `.claude/agents/` directory contains Claude Code sub-agent definitions — treat as `chore(ci)` commits
- `.claude/agent-memory/` directory contains persistent agent memory — commit when updated
- Branch `agent/frontend` is the active development branch for the Web UI phase

## Commit Language
- Use Dutch for domain/feature descriptions ("voeg ... toe", "herstel ...", "verplaats ...")
- English acceptable for technical terms within Dutch sentences
