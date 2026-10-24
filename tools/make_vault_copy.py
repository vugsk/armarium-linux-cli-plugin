#!/usr/bin/env python3
"""Строит резервную копию, описания и карту скиллов в хранилище Obsidian ИЗ ПЛАГИНА armarium.

Источник истины — папка плагина (skills/, checks/, hooks/). Скрипт ничего не меняет в плагине:
он только перезаписывает в хранилище папки `Копия/`, `Описания/`, `Проверки/`, `Хук/` и файл `Карта скиллов.md`
в `<корень хранилища>/Документация/Скиллы Claude/`.

Корень хранилища берётся из файла настроек `~/.claude/armarium.json` (поле `vault`, схема описана
в `docs/settings.md` плагина). Если файла нет или он неверный, скрипт печатает понятное сообщение
и ничего не записывает.

Использование:
    python3 -I make_vault_copy.py
"""
import json
import re
import shutil
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent   # корень плагина (рядом с папкой tools)
SKILLS = PLUGIN / "skills"                        # источник скиллов — плагин
SETTINGS = Path.home() / ".claude" / "armarium.json"   # файл настроек пользователя


def pretty(path: Path) -> str:
    """Путь для текста заметок: начало с домашней папки заменяем на `~`, чтобы в тексте не было имени пользователя."""
    try:
        return "~/" + str(path.relative_to(Path.home()))
    except ValueError:
        return str(path)   # путь вне домашней папки показываем как есть


def load_vault() -> Path:
    """Читает из настроек корень хранилища и проверяет, что такая папка существует.

    При любой проблеме печатает причину и завершает скрипт, ничего не записывая:
    молча подставлять другой путь нельзя (можно записать копию не туда).
    """
    if not SETTINGS.exists():
        sys.exit(f"Файл настроек {pretty(SETTINGS)} не найден: создай его по docs/settings.md плагина "
                 '(например, {"version": 1, "vault": "~/Documents/Book"}).')
    try:
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        sys.exit(f"Файл настроек {pretty(SETTINGS)} не является корректным JSON: {err}")
    if data.get("version") != 1:
        sys.exit(f"В {pretty(SETTINGS)} неизвестная версия схемы: {data.get('version')!r} (ожидалась 1).")
    vault = data.get("vault")
    if not isinstance(vault, str) or not vault:
        sys.exit(f"В {pretty(SETTINGS)} нет поля vault (корень хранилища Obsidian).")
    path = Path(vault).expanduser()   # ~ в начале значения раскрывается как домашняя папка
    if not path.is_dir():
        sys.exit(f"Папка хранилища из настроек не найдена: {path}")
    return path


VAULT = load_vault()                                        # корень хранилища из настроек
OUT = VAULT / "Документация" / "Скиллы Claude"              # фиксированная раскладка хранилища (docs/settings.md)
PLUGIN_TXT = pretty(PLUGIN)                                 # путь плагина для текстов заметок

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
    "setup": "Мастер настройки: пишет файл настроек, память и черновики недостающих стандартов только с согласия человека; существующее не перезаписывает без копии, ничего не удаляет. Код не пишет.",
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
    "setup": "Первичная настройка armarium: хранилище, файл настроек, черновики стандартов.",
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
                 f"Копия файлов: `Копия/{n}/` · Источник: `{PLUGIN_TXT}/skills/{n}/` (копия не синхронизируется сама).", "",
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
             f"Резервная копия и описание скиллов плагина `armarium` (`{PLUGIN_TXT}/`, источник истины — он). "
             "Источник истины для правил — стандарты в `Проекты/`; скиллы читают их, а не копируют.", "",
             "## Структура",
             "- `Описания/` — по заметке на скилл: что делает, кто пишет код, какие скиллы использует и кто использует его.",
             "- `Копия/` — точная копия папок скиллов. Синхронизируется вручную (см. ниже).",
             "- `Проверки/` — сохранённый набор проверок скиллов (срабатывание, пробные данные, сценарии).", "",
             "## Скиллы", ""] + rows + ["",
             "## Как обновить копию",
             f"После правки скилла или стандарта выполни `python3 -I {PLUGIN_TXT}/tools/make_vault_copy.py`. "
             "Расхождение копии с плагином `standards-audit` по умолчанию не проверяет.", "",
             "## Хук-напоминание",
             "После правки стандарта (`Проекты/Стандарт*.md`) или файла в папке `skills/` плагина "
             "хук PostToolUse (в плагине `hooks/hooks.json`) запускает `hooks/audit-reminder.sh` плагина. "
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
