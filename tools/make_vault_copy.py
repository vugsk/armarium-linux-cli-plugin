#!/usr/bin/env python3
"""Строит резервную копию, описания и карту скиллов в хранилище Obsidian ИЗ ПЛАГИНА armarium.

Источник истины — папка плагина (skills/, checks/, hooks/). Скрипт ничего не меняет в плагине:
он только перезаписывает в хранилище папки `Копия/`, `Описания/`, `Проверки/`, `Хук/` и файл `Карта скиллов.md`
в `Документация/Скиллы Claude/`.

Использование:
    python3 -I make_vault_copy.py
"""
import re
import shutil
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent   # корень плагина (рядом с папкой tools)
SKILLS = PLUGIN / "skills"                        # источник скиллов — плагин
OUT = Path.home() / "Documents/disk_docs/Book/Документация/Скиллы Claude"

# Встроенные скиллы, на которые наши скиллы могут ссылаться (не копируются).
BUILTIN = ["security-review", "init", "deep-research", "claude-api", "schedule", "loop",
           "update-config", "fewer-permission-prompts", "run", "code-review", "simplify",
           "skill-creator", "standards-audit-builtin"]

# Кто пишет код в этом скилле (по решениям пользователя).
MODE = {
    "naming-standards": "Предлагает имена, выбирает пользователь. Код не пишет.",
    "obsidian-notes": "Пишет заметки Claude. Код не пишет; скрипты (например, чертежи) только по явной просьбе «напиши».",
    "project-stages": "Заметки пишет Claude. Код проекта пишет пользователь; скрипты, шаблоны и конфиги для заметок только по явной просьбе «напиши», с полными комментариями.",
    "project-scaffold": "Режим наставника: файлы и код пишет пользователь, git-команды Claude даёт прямо.",
    "repo-init": "Исключение: служебные файлы заготовки (README, .gitignore, hello-world, tests/, LICENSE) создаёт Claude с полными комментариями. Код проекта и конфиги пишет пользователь; git-команды даёт, выполняет пользователь.",
    "release-versioning": "Режим наставника: конфиги и скрипты пишет пользователь, git-команды Claude даёт прямо; текст коммитов предлагает на английском с русским переводом.",
    "firmware-esp-stm": "Режим наставника: код прошивки пишет пользователь.",
    "code-coach": "Режим наставника: код проекта пишет пользователь; git-команды даются прямо; на вопросы о языке отвечает полноценно.",
    "hw-design-coach": "Режим наставника: схему и плату проектирует пользователь.",
    "hw-board-check": "Только проверка и отчёт, проект EDA не меняет.",
    "test-plan": "Исключение: код тестов в tests/ пишет Claude (каждый тест отдельным файлом с комментарием). Код проекта не правит.",
    "standards-audit": "Только чтение и отчёт; исправляет по прямому «да» пользователя.",
    "dependency-audit": "Только проверка и отчёт; исправляет проблемы пользователь.",
    "project-security": "Проверка и отчёт; код проекта исправляет пользователь; тесты под находки пишутся в tests/ по просьбе.",
    "project-retro": "Заметку «Итоги» пишет Claude с согласия пользователя; выводы и причины даёт пользователь. Код не пишет.",
    "reverse-engineering": "Анализ и отчёт; скрипты анализа только по явной просьбе «напиши»; код проекта пишет пользователь.",
}

# Короткое назначение для карты скиллов.
PURPOSE = {
    "naming-standards": "Имена проектов, устройств, веток, тегов и публичное имя по стандартам.",
    "obsidian-notes": "Оформление заметок и чертежей в Obsidian, правила фиксации решений.",
    "project-stages": "Проекты по этапам: статус, вопросы, заметки, план с вехами, карта проектов.",
    "project-scaffold": "Наставник по настройке репозитория (как, а не создание файлов).",
    "repo-init": "Заготовка репозитория, выбор лицензии, наполнение README.",
    "release-versioning": "Версии, теги, release-please, текст коммитов.",
    "firmware-esp-stm": "Наставник по прошивкам ESP и STM32.",
    "code-coach": "Наставник по языкам, git, отладке, сборке и предметным областям.",
    "hw-design-coach": "Наставник по проектированию схем и плат, своего процессора.",
    "hw-board-check": "Проверка платы перед заказом: ERC/DRC, требования производства, паспорт.",
    "test-plan": "Тесты этапа 4: написание, запуск, заметки с результатами.",
    "standards-audit": "Проверка согласованности стандартов и скиллов.",
    "dependency-audit": "Выбор и проверка зависимостей на уязвимости и ошибки.",
    "project-security": "Проверка безопасности кода проекта.",
    "project-retro": "Итоги проекта при заморозке, отмене и выпуске.",
    "reverse-engineering": "Анализ бинарников, прошивок, форматов и протоколов с проверкой права на анализ.",
}


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def frontmatter_desc(skill_md: str) -> str:
    """Достаёт поле description из шапки SKILL.md."""
    m = re.search(r"^description:\s*(.+)$", skill_md, re.M)
    return m.group(1).strip() if m else ""


def all_text(skill_dir: Path) -> dict[str, str]:
    """Тексты всех .md файлов скилла по относительным путям."""
    return {str(p.relative_to(skill_dir)): read(p) for p in sorted(skill_dir.rglob("*.md"))}


def mentions(text: str, name: str) -> bool:
    return re.search(r"`" + re.escape(name) + r"`", text) is not None or re.search(r"скилл\w*\s+" + re.escape(name) + r"\b", text) is not None


def first_context(text: str, name: str) -> str:
    """Первая строка, где упомянут скилл: коротко объясняет, зачем ссылка."""
    for line in text.splitlines():
        if mentions(line, name):
            line = re.sub(r"\s+", " ", line).strip()
            return line[:170] + ("…" if len(line) > 170 else "")
    return ""


def main() -> None:
    names = sorted(p.name for p in SKILLS.iterdir() if p.is_dir() and p.name != "synced")
    (OUT / "Копия").mkdir(parents=True, exist_ok=True)
    (OUT / "Описания").mkdir(parents=True, exist_ok=True)

    texts = {n: all_text(SKILLS / n) for n in names}

    # 1. Полная копия папок скиллов.
    for n in names:
        dst = OUT / "Копия" / n
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(SKILLS / n, dst)

    # 2. Кто на кого ссылается.
    uses: dict[str, dict[str, str]] = {n: {} for n in names}
    used_by: dict[str, list[str]] = {n: [] for n in names}
    builtin_uses: dict[str, dict[str, str]] = {n: {} for n in names}
    for n in names:
        joined = "\n".join(texts[n].values())
        for other in names:
            if other != n and mentions(joined, other):
                uses[n][other] = first_context(joined, other)
                used_by[other].append(n)
        for b in BUILTIN:
            if mentions(joined, b):
                builtin_uses[n][b] = first_context(joined, b)

    # 3. Описание каждого скилла.
    for n in names:
        skill_md = read(SKILLS / n / "SKILL.md")
        desc = frontmatter_desc(skill_md)
        joined_all = "\n".join(texts[n].values()).lower()
        standards = [name for key, name in (("проектных заметок", "Стандарт проектных заметок"),
                                            ("названию проектов", "Стандарт по названию проектов"),
                                            ("названию устройств", "Стандарт по названию устройств"))
                     if key in joined_all]
        files = [str(p.relative_to(SKILLS / n)) for p in sorted((SKILLS / n).rglob("*")) if p.is_file()]
        lines = [f"# Скилл - {n}", "",
                 f"Копия файлов: `Копия/{n}/` · Источник: `~/Projects/claude/armarium-linux-cli-plugin/skills/{n}/` (копия не синхронизируется сама).", "",
                 "## Что делает", desc, "",
                 "## Кто пишет код", MODE.get(n, "—"), "",
                 "## Какие скиллы использует"]
        if uses[n] or builtin_uses[n]:
            for o, ctx in uses[n].items():
                lines.append(f"- [[Скилл - {o}]] — {ctx}")
            for b, ctx in builtin_uses[n].items():
                lines.append(f"- встроенный `{b}` — {ctx}")
        else:
            lines.append("- нет")
        lines += ["", "## Какие скиллы ссылаются на него"]
        lines += [f"- [[Скилл - {o}]]" for o in used_by[n]] or ["- нет"]
        lines += ["", "## Какие стандарты читает"]
        lines += [f"- {s}" for s in standards] or ["- нет"]
        lines += ["", "## Файлы"] + [f"- `{f}`" for f in files] + [""]
        (OUT / "Описания" / f"Скилл - {n}.md").write_text("\n".join(lines), encoding="utf-8")

    # 4. Карта скиллов.
    rows = ["| Скилл | Назначение | Использует | Кто пишет код |", "| --- | --- | --- | --- |"]
    for n in names:
        u = ", ".join(f"[[Скилл - {o}]]" for o in uses[n]) or "—"
        rows.append(f"| [[Скилл - {n}]] | {PURPOSE.get(n, '')} | {u} | {MODE.get(n, '—').split('.')[0]} |")
    index = ["# Карта скиллов Claude", "",
             "Резервная копия и описание скиллов плагина `armarium` (`~/Projects/claude/armarium-linux-cli-plugin/`, источник истины — он). "
             "Источник истины для правил — стандарты в `Проекты/`; скиллы читают их, а не копируют.", "",
             "## Структура",
             "- `Описания/` — по заметке на скилл: что делает, кто пишет код, какие скиллы использует и кто использует его.",
             "- `Копия/` — точная копия папок скиллов. Синхронизируется вручную (см. ниже).",
             "- `Проверки/` — сохранённый набор проверок скиллов (срабатывание, пробные данные, сценарии).", "",
             "## Скиллы", ""] + rows + ["",
             "## Как обновить копию",
             "После правки скилла в плагине (или в `~/.claude/skills`, пока плагин не включён) выполни "
             "`python3 -I ~/Projects/claude/armarium-linux-cli-plugin/tools/import_user_skills.py` (переносит правки из `~/.claude/skills` в плагин, "
             "нужно только пока плагин не включён) и затем `python3 -I ~/Projects/claude/armarium-linux-cli-plugin/tools/make_vault_copy.py`. "
             "Расхождение копии с оригиналом `standards-audit` по умолчанию не проверяет. "
             "Команда пересборки: `python3 -I ~/Projects/claude/armarium-linux-cli-plugin/tools/make_vault_copy.py`.", "",
             "## Хук-напоминание",
             "После правки стандарта (`Проекты/Стандарт*.md`) или файла в `~/.claude/skills/` (кроме `synced`) "
             "хук PostToolUse (в плагине `hooks/hooks.json`; пока плагин не включён — в `~/.claude/settings.json`) запускает `hooks/audit-reminder.sh` плагина. "
             "Он добавляет Claude напоминание: предложить `standards-audit` и обновить эту копию. Сам ничего не запускает. "
             "Копия скрипта: `Хук/audit-reminder.sh`. Просмотр и отключение: команда `/hooks`.", ""]
    (OUT / "Карта скиллов.md").write_text("\n".join(index), encoding="utf-8")
    # Хук и сохранённый набор проверок берём из плагина.
    (OUT / "Хук").mkdir(exist_ok=True)
    shutil.copy(PLUGIN / "hooks/audit-reminder.sh", OUT / "Хук/audit-reminder.sh")
    (OUT / "Проверки").mkdir(exist_ok=True)
    for f in (PLUGIN / "checks").iterdir():
        if f.is_file():
            shutil.copy(f, OUT / "Проверки" / f.name)
    print(f"Скиллов: {len(names)}; описаний: {len(list((OUT / 'Описания').glob('*.md')))}")


if __name__ == "__main__":
    main()
