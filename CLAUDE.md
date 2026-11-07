# Super Skipper

A Home Assistant helper integration (`custom_components/super_skipper`) that watches media players and skips, switches station or mutes when a keyword plays.

## GitHub: nothing without asking

- Do not push, create or edit releases, comment, label, or change anything else on GitHub unless Quinten asks for that specific action in the conversation. Commit locally, then ask.
- Never write issue or PR references (`#1`, `Fixes #2`, `See #2`) in commit messages: GitHub links every pushed commit that mentions an issue to that issue's timeline.

## Branches and releases

- All work happens on the `beta` branch. When Quinten asks for a push, it goes to `beta`.
- Merge or push to `main` only when Quinten says so explicitly in that conversation. Approval for one push does not carry over to the next one.
- A release from `beta` is a GitHub **pre-release** whose tag matches `manifest.json` (for example `v0.1.0b1` for version `0.1.0b1`). The Marketplace and HACS only offer it to people who turned on the *Pre-release* switch of this repository, so Quinten can test it in their own Home Assistant first.
- **Every push to `beta` ships as a new pre-release** (Quinten asked for this on 2026-11-07): bump the `b` number in `manifest.json` in the last commit, push, then `gh release create vX.Y.ZbN --prerelease --target beta` with short notes of what changed. Nothing else on GitHub without asking.
- A normal release (`vX.Y.Z`, no `b`) is made from `main`, after the merge Quinten asked for.

## Commits

- Commit as Radeaus `<99103370+Radeaus@users.noreply.github.com>` (repo-local git config).
- Add no `Co-Authored-By: Claude` trailer and no "Generated with Claude Code" line.

## Code

- Home Assistant 2025.8 is the minimum (`hacs.json`): no `visible=` form fields, no features newer than that.
- User-facing text lives in `translations/en.json` (and `nl.json`), follows the Home Assistant style guide (sentence case, "action" not "service", "Home Assistant" in full) and every field has a `data_description`.

## Tests

- Run `.venv/bin/pytest` before every commit; coverage must stay above 95 %.
