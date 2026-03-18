# Changelog

## 0.3.1 - 2026-03-14

### What's New

This release expands Symlegion from simple one-repo symlink management into a more flexible cross-repo sync tool.

### Added

- `recursive` mode for discovering matching repos under one or more search roots and creating links inside each match.
- `search` + `depth` support for recursive configs.
- Warnings for missing recursive search roots, without stopping the run.
- Relative `search` paths in recursive mode, resolved from the YAML config file folder.
- `--config` / `-c` to run `sync`, `check`, `clean`, or `init` against a specific YAML file.
- Enriched `init` template with starter mappings for:
  - OpenCode.
  - Claude Code.
  - Pi.
  - Goose.
- Expanded CLI help so `symlegion --help` explains config lookup, path resolution, modes, flags, and typical usage.

### Changed

- The original behavior is now explicitly `mode: direct`, and it remains the default when `mode` is omitted.
- Recursive configs now default `depth` to `5` when not specified.
- `type` is no longer accepted; use `mode` only.
- The starter config now assumes OpenCode as the source of truth for rules and commands.

### Documentation

- README now documents:
  - direct vs recursive behavior.
  - config lookup order.
  - path resolution rules.
  - recursive matching behavior.
  - `--config` usage.
  - starter harness mappings.

### Verification

- Test suite updated across config parsing, integration flows, recursive discovery, custom config targeting, and CLI help.
- Current release verified with `17 passed`.
