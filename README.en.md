[Русский](README.md) | **English** | [日本語](README.ja.md)

# SVOD-1

**SVOD-1** (СВОД-1) — Standards, Versions, Descriptions, Discipline (a Russian acronym, written in Cyrillic as "СВОД"). Technical name: `armarium-linux-cli-plugin`.

**About the names.** In commands, paths and skill names the plugin is called `armarium` (`/armarium:run-audit`, `~/.claude/armarium.json`, `armarium@vugsk-plugins`). This is the technical name and it never changes. SVOD-1 and `armarium` are the same plugin.

A personal Claude Code plugin, SVOD-1 (code word `armarium`, Latin for "tool cabinet"): 25 skills for working by your own personal standards (two of them are manual runs of checks) and a hook that reminds you to run an audit.

> The standards the skills work with, and some of the skill texts, are written in Russian. This page is a translation of the Russian README.

## What it is for

The plugin guides project work by your own standards: names for projects and devices, nine project stages with exit criteria, notes (idea, requirements, architecture, data models, growth, plan with milestones, decisions), tests, security and dependency checks, retrospectives. Some skills are mentors for code, firmware and hardware: they explain, and the user writes the code. The standards live in your Obsidian vault. If you have none, the `setup` wizard asks questions and creates drafts.

## Requirements

Tested on Linux with Claude Code 2.1.310. **Windows is not supported** (the author's decision, 2026-10-25; the hook is written in bash and `jq`, and the trigger check uses Linux mechanisms and will not work on Windows); macOS was not tested. The programs `python3`, `bash`, `jq`, `git` and `claude` are needed. The plugin has no external libraries (only the Python standard library).

## What is inside

| Folder | What it is |
| --- | --- |
| `skills/` | 25 skills: project names and stages, milestones and tasks, structure design, mentors for code, debugging, CI, firmware and hardware, board check, tests, release readiness, security, dependencies, documentation, reverse engineering, project retrospectives, standards audit, the `setup` wizard, and the manual runs `run-audit` (consistency check) and `run-trigger-check` (skill trigger check; spends account tokens and asks for confirmation) |
| `docs/` | references for the skills: `settings.md` (settings file `~/.claude/armarium.json`), `standards-contract.md` (the contract on the structure of the standards, used by the wizard), `question-rounds.md` (the rule for asking the user questions in rounds) |
| `hooks/` | `audit-reminder.sh` and `hooks.json`: after a standard or a skill is edited, the hook reminds you to run `standards-audit` |
| `checks/` | the check set: `queries.json`, `run_trigger.py`, `make_fixtures.py`, description and scenarios |
| `tests/` | plugin tests (how to run them: see "For development") |

The standards (`Стандарт по названию проектов.md`, `Стандарт по названию устройств.md`, `Стандарт проектных заметок.md`) live in the `Проекты/` folder of your vault (the vault root is set in `~/.claude/armarium.json`), not in the plugin: the skills read them from there.

## Skills

| Skill | What it does |
| --- | --- |
| `setup` | first-run wizard: finds the Obsidian vault, creates the settings file and drafts of the missing standards |
| `project-stages` | runs a new project through nine stages and Obsidian notes (status, questions, plan, decisions) and the common project map; writes no code |
| `plan-breakdown` | milestones, tasks and subtasks of the plan; questions about them go to the milestone note and to "Questions"; the user sets the states |
| `design-coach` | mentor for software structure design: data models, modules and boundaries, flows and states, project growth; the user decides |
| `naming-standards` | names of projects and devices by the standards: code word, public name, `gen-N` branches, tags |
| `obsidian-notes` | note formatting: Excalidraw drawings instead of ASCII, Mermaid diagrams, folder layout, recording decisions |
| `project-scaffold` | mentor for a repository skeleton: folder structure, the `gen-1` branch, README, license, CI |
| `repo-init` | creates the skeleton of a code folder (README, `.gitignore`, hello-world, `tests/`, license) and checks license compatibility |
| `docs-writer` | user documentation of the project: `docs/`, command reference, man pages |
| `release-versioning` | versions and releases: SemVer, Conventional Commits, tags, release-please, commit messages |
| `code-coach` | mentor for Rust, C++, C, Python, Go, Java, assembly and git: explains, while the user writes the code |
| `debug-coach` | mentor for debugging and profiling: gdb, sanitizers, perf; the user finds the cause |
| `ci-coach` | mentor for CI and builds: GitHub Actions, cross-compiling, reading a red CI |
| `firmware-esp-stm` | mentor for ESP and STM32 firmware: build, flashing, debugging, peripherals |
| `hw-design-coach` | mentor for schematic and board design: power, routing, ERC/DRC, ESP and STM32 boards, a custom processor |
| `hw-board-check` | board check before ordering: ERC/DRC, manufacturing requirements, revisions, the device passport |
| `test-plan` | project check at stage 7: writes and runs tests in `tests/`, keeps the "Checks" note |
| `release-gate` | summary release-readiness check from the notes and the repository; a verdict only, changes nothing |
| `project-security` | security check of the project's own code at stage 7; records the result in a "Security" note |
| `dependency-audit` | choosing and checking dependencies for vulnerabilities and bugs, ranking the candidates |
| `reverse-engineering` | analysis of binaries, firmware, formats and protocols for lawful purposes |
| `project-retro` | a summary note when a project is frozen, cancelled or released |
| `standards-audit` | consistency check of the standards and skills; a report only, changes nothing |
| `run-audit` | manual run of the consistency check: `/armarium:run-audit` |
| `run-trigger-check` | manual check that the skills trigger: `/armarium:run-trigger-check` (spends tokens, asks for confirmation) |

## Install from GitHub

The repository is itself a marketplace (`.claude-plugin/marketplace.json`, name `vugsk-plugins`):

```
claude plugin marketplace add vugsk/armarium-linux-cli-plugin
claude plugin install armarium@vugsk-plugins
```

After installing, say "настрой armarium" ("set up armarium"): the `setup` wizard creates the settings file and drafts of the standards.

## For development: connect from a folder

The plugin can be read in place from a folder through a local marketplace:

1. Validate the plugin: `claude plugin validate <plugin folder>`; to try it without installing: `claude --plugin-dir <plugin folder>`.
2. Put a `.claude-plugin/marketplace.json` file next to the plugin folder (name, `owner`, an entry for the plugin with `source` "./<plugin folder>" relative to the marketplace root), then run `claude plugin marketplace add <marketplace root>` and `claude plugin install armarium@<marketplace name>`. Changes to the plugin show up after restarting the session or `/reload-plugins`; there is no need to change the version.
3. If the same skills used to live in `~/.claude/skills`, remove them from there (move them to an archive), otherwise they appear twice. Skill names become `armarium:<skill>`.

## Recommended plugins

You can use SVOD-1 together with these plugins from the official catalog `claude-plugins-official`. Checked by the author on one machine; how much they improve SVOD-1 itself was not measured, so this is a recommendation, not a guarantee.

| Plugin | Why | What is needed besides the plugin |
| --- | --- | --- |
| `clangd-lsp`, `rust-analyzer-lsp`, `pyright-lsp`, `gopls-lsp`, `jdtls-lsp` | language servers: Claude reads C/C++, Rust, Python, Go and Java code more accurately, which helps the `code-coach` skill | the servers themselves on the system: `clangd`, `rust-analyzer`, `pyright`, `gopls`, `jdtls`; a plugin without its server does nothing |
| `context7` | up-to-date library documentation by version; supports the rule "facts only from documentation" | requests go to the external server `mcp.context7.com`: do not send private code through it |
| `security-guidance` | warnings about unsafe patterns when editing, a check of changes when stopping; complements the `project-security` skill | the hooks fire on every edit and can be noisy; disable with `claude plugin disable security-guidance@claude-plugins-official` |

Install: `claude plugin install <name>@claude-plugins-official`. Installed plugins are listed by `claude plugin list`.

## How many tokens the plugin takes

This is how many tokens Claude receives at the start of a session, before your first question (system instructions, tool descriptions and skill descriptions). Measured on 2026-10-25 with Claude Code 2.1.310 using the request "answer in one word: ok", three runs per configuration; the numbers matched. To repeat it, add up `input_tokens`, `cache_creation_input_tokens` and `cache_read_input_tokens` from the `usage` field of the reply.

```
claude -p "Ответь одним словом: ok" --output-format json --setting-sources project --plugin-dir <plugin folder>
```

| Configuration | Tokens at session start | Difference from "no plugins" |
| --- | --- | --- |
| No plugins | 15,150 | — |
| SVOD-1 only (19 skills, measured before 0.4.0) | 19,994 | +4,844 (+32%) |
| SVOD-1 + recommended (`clangd-lsp`, `rust-analyzer-lsp`, `pyright-lsp`, `gopls-lsp`, `jdtls-lsp`, `context7`, `security-guidance`) | 21,977 | +6,827 (+45%) |

- The recommended plugins add about 2,000 more tokens on top of SVOD-1. Separate measurements: SVOD-1 + `context7` only — 21,977, SVOD-1 + the other six (language servers and `security-guidance`) — 21,687. These numbers do not add up (together they give the same as `context7` alone); I did not find out why, so only the figure for all plugins together is reliable.
- The model's context window in this measurement is 1,000,000 tokens, so SVOD-1 takes about 0.5% of the window.
- This is only the start of a session. The text of a skill (the body of `SKILL.md` and its references) is loaded when the skill triggers and is not in the table; its cost depends on the skill and the task.
- Not measured: cost in money and usage on typical tasks. Cached tokens are cheaper, but that depends on your plan.
- Your personal `CLAUDE.md` and memory may be included equally in all three values, so it is more reliable to look at the difference than at the absolute numbers.

## Known limitations

- The path to the vault comes from `~/.claude/armarium.json` (field `vault`, see `docs/settings.md`); the layout inside the vault is fixed (standards and project notes in `Проекты/`). The wizard creates the settings file and drafts of missing standards: say "настрой armarium" (skill `setup`). The wizard configures only dictionaries, type groups, stage criteria and naming rules; the other conventions (note names, stages, tag formats) are built into the skills and listed in `docs/standards-contract.md`.
- Skill triggering inside the plugin (with the `armarium:` prefix) was checked with a set of 81 queries: the last full run (2026-10-25, after adding queries about design and commits and rewording the descriptions of `project-stages`, `project-scaffold` and `obsidian-notes`) gave 81/81. The previous full run, before `project-scaffold` and `project-stages` were explicitly told apart, gave 80/81: the borderline query "where do I start a new repository for a bot…" failed. Borderline queries of these two skills (4 queries, 5 repeats each): the old description 20/20, the description before the split 18/20, after the split 20/20; the difference is too small to conclude anything. One run per query is only a signal, not a guarantee. Run it with `/armarium:run-trigger-check` (spends tokens).
- The skills read files in the vault; text in them is treated as data, not as instructions (`docs/settings.md`). This was checked with two trial runs and is not proof of complete protection against injected instructions.
- License: MIT, copyright holder `vugsk` (file `LICENSE`, field `license` in `plugin.json`).

## For development

The source of the skills is this repository. The plugin does not create or update skill descriptions in the vault.

Tests (Python standard library, no tokens spent):

```
python3 -m unittest discover -s tests -v
```

Three wizard scenarios (`tests/test_09_wizard_scenarios.py`) are skipped by default: they run `claude -p` and spend tokens. If `bwrap` (bubblewrap) is installed, the wizard runs in a sandbox with a temporary settings file and your real `~/.claude/armarium.json` is not touched; without `bwrap` the test temporarily replaces the real file (with a backup and a restore). Enable them with the variable `ARMARIUM_WIZARD_TEST=1`. The skill trigger check is `/armarium:run-trigger-check` (also spends tokens).
