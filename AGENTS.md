# Repository Guidelines

## Project Structure & Module Organization
This repository is docs-first and currently organized under `docs/`.
- `docs/spec/`: numbered canonical spec chapters (`00-meta.md` to `10-review-notes-*.md`).
- `docs/cards/`: feature cards (`F01`-`F15`) with scope, API surface, invariants, and tests.
- `docs/adr/`: architecture decision records (ADR-001+).
- Root references: `docs/INVARIANTS.md`, `docs/CONVENTIONS.md`, `docs/STATE_MACHINES.md`, `docs/ERROR_CODES.md`, `docs/HOT_FIELDS.md`.

## Build, Test, and Development Commands
There is no runtime build pipeline in this snapshot; contributors validate spec consistency.
- `rg --files docs` : list tracked documentation files.
- `rg -n "INV-[0-9]{3}[A-Z]?" docs` : verify invariant references are present and consistent.
- `rg -n "^## " docs/spec/05-api.md docs/spec/06-schemas.md docs/spec/07-data-model.md` : check API/schema/data-model sections before review.
- `Get-Content docs/spec/00-meta.md -Encoding UTF8 -Raw` : confirm current baseline/version context.

## Coding Style & Naming Conventions
Follow `docs/CONVENTIONS.md` as the source of truth.
- IDs: ULID (26 chars), optional stable table prefix (`proj_`, `ch_`, `run_`, etc.).
- Naming: tables/fields in `snake_case`; DB enums `lower_snake`; domain enums `PascalCase`.
- JSON: schema-validate before persistence; `schema_version` stays string `"1.2"`.
- Keep doc edits minimal and atomic; prefer updating spec/card/ADR together when behavior changes.

## Testing Guidelines
Use milestone gates in `docs/spec/08-milestones.md` as acceptance criteria.
- For finalize/idempotency changes, include M0b gates (conflict, crash recovery, op_id dedupe, idempotency key/hash conflict).
- For retrieval/graph/timeline changes, update affected card test bullets (for example `docs/cards/F07-timeline.md`).
- Any change touching protected writes must be checked against `docs/INVARIANTS.md` (violations are P0 by definition).

## Commit & Pull Request Guidelines
Git history is not included in this workspace snapshot, so no local convention can be inferred from commits. Use Conventional Commits by default:
- `docs(spec): align finalize apply response with invariants`
- `docs(adr): add rationale for storage choice`

PRs should include:
- concise scope and motivation,
- impacted files (spec/cards/adr/invariants),
- explicit invariant IDs and error codes affected,
- consistency notes for API (`05`), schema (`06`), and data model (`07`) when relevant.
