[Русский](README.md) | **English** | [日本語](README.ja.md)

# SVOD-1

**SVOD-1** (СВОД-1) — Standards, Versions, Descriptions, Discipline (a Russian acronym, written in Cyrillic as "СВОД"). Technical name: `armarium-linux-cli-plugin`.

**About the names.** In commands, paths and skill names the plugin is called `armarium` (`/armarium:run-audit`, `~/.claude/armarium.json`, `armarium@vugsk-plugins`). This is the technical name and it never changes. SVOD-1 and `armarium` are the same plugin.

A personal Claude Code plugin, SVOD-1 (code word `armarium`, Latin for "tool cabinet"): 19 skills for working by your own personal standards (two of them are manual runs of checks) and a hook that reminds you to run an audit.

> The standards the skills work with, and some of the skill texts, are written in Russian. This page is a translation of the Russian README.

## What it is for

The plugin guides project work by your own standards: names for projects and devices, six project stages with exit criteria, notes (idea, requirements, architecture, plan with milestones, decisions), tests, security and dependency checks, retrospectives. Some skills are mentors for code, firmware and hardware: they explain, and the user writes the code. The standards live in your Obsidian vault. If you have none, the `setup` wizard asks questions and creates drafts.

## Requirements

Tested on Linux with Claude Code 2.1.310. The programs `python3`, `bash`, `jq`, `git` and `claude` are needed. The plugin has no external libraries (only the Python standard library).

## What is inside

| Folder | What it is |
| --- | --- |
| `skills/` | 19 skills: project names and stages, mentors for code, firmware and hardware, board check, tests, security, dependencies, reverse engineering, project retrospectives, standards audit, the `setup` wizard, and the manual runs `run-audit` (consistency check) and `run-trigger-check` (skill trigger check; spends account tokens and asks for confirmation) |
| `docs/` | references for the skills: `settings.md` (settings file `~/.claude/armarium.json`), `standards-contract.md` (the contract on the structure of the standards, used by the wizard) |
| `hooks/` | `audit-reminder.sh` and `hooks.json`: after a standard or a skill is edited, the hook reminds you to run `standards-audit` and refresh the copy |
| `checks/` | the check set: `queries.json`, `run_trigger.py`, `make_fixtures.py`, description and scenarios |
| `tools/` | `make_vault_copy.py` (a copy and descriptions in the Obsidian vault; needed by the plugin author) |
| `tests/` | plugin tests (how to run them: see "For development") |

The standards (`Стандарт по названию проектов.md`, `Стандарт по названию устройств.md`, `Стандарт проектных заметок.md`) live in the `Проекты/` folder of your vault (the vault root is set in `~/.claude/armarium.json`), not in the plugin: the skills read them from there.

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

## Known limitations

- The path to the vault comes from `~/.claude/armarium.json` (field `vault`, see `docs/settings.md`); the layout inside the vault is fixed (`Проекты/`, `Документация/Скиллы Claude/`). The wizard creates the settings file and drafts of missing standards: say "настрой armarium" (skill `setup`). The wizard configures only dictionaries, type groups, stage criteria and naming rules; the other conventions (note names, stages, tag formats) are built into the skills and listed in `docs/standards-contract.md`.
- Skill triggering inside the plugin (with the `armarium:` prefix) was checked with a set of 73 queries: the last full run passed 71/73; two queries do not trigger reliably (`project-stages` on a request about a new expense-tracking program, `code-coach` on "write a function in python"). Run it with `/armarium:run-trigger-check` (spends tokens).
- The skills read files in the vault; text in them is treated as data, not as instructions (`docs/settings.md`). This was checked with two trial runs and is not proof of complete protection against injected instructions.
- License: MIT, copyright holder `vugsk` (file `LICENSE`, field `license` in `plugin.json`).

## For development

The source of the skills is this repository. The backup copy and the skill descriptions in the author's vault (`Документация/Скиллы Claude/` inside the vault from `~/.claude/armarium.json`) are built from it:

```
python3 -I tools/make_vault_copy.py --yes
```

Tests (Python standard library, no tokens spent):

```
python3 -m unittest discover -s tests -v
```

Three wizard scenarios (`tests/test_09_wizard_scenarios.py`) are skipped by default: they run `claude -p`, spend tokens and temporarily replace your real `~/.claude/armarium.json` (with a backup and a restore). Enable them with the variable `ARMARIUM_WIZARD_TEST=1`. The skill trigger check is `/armarium:run-trigger-check` (also spends tokens).
