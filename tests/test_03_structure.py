"""Тест 3: структура скиллов корректна, ссылки внутри плагина не ведут в пустоту.

Зачем: требования Т-1 (плагин содержит скиллы) и Т-8 (скиллы читают настройки через справку `docs/settings.md`).
Проверяем для каждой папки в `skills/`:
  1. есть `SKILL.md` с шапкой, в которой `name` равен имени папки, а `description` не пустое;
  2. все упомянутые в тексте пути вида `assets/<файл>.md` и `references/<файл>.md` существуют внутри этого скилла;
  3. если скилл ссылается на `../../docs/settings.md`, этот файл существует относительно папки скилла.
Ожидаем: ни одной проблемы. Токены не тратятся.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SKILLS = PLUGIN / "skills"


def frontmatter(text: str) -> dict:
    """Читает простую шапку --- ... --- из начала SKILL.md: строки вида `ключ: значение`."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    data = {}
    if match:
        for line in match.group(1).splitlines():
            key, _, value = line.partition(":")
            if value:
                data[key.strip()] = value.strip()
    return data


class TestStructure(unittest.TestCase):
    def test_skills_are_well_formed(self):
        problems = []
        folders = sorted(p for p in SKILLS.iterdir() if p.is_dir())
        self.assertGreater(len(folders), 0, "в skills/ нет ни одного скилла")
        for folder in folders:
            skill_md = folder / "SKILL.md"
            if not skill_md.exists():
                problems.append(f"{folder.name}: нет SKILL.md")
                continue
            text = skill_md.read_text(encoding="utf-8")
            head = frontmatter(text)
            if head.get("name") != folder.name:
                problems.append(f"{folder.name}: name в шапке {head.get('name')!r}, ожидалось {folder.name!r}")
            if not head.get("description"):
                problems.append(f"{folder.name}: пустое description")
            # Пути assets/... и references/... из текста скилла и его вспомогательных файлов.
            # Путь может начинаться с имени другого скилла (`project-stages/assets/status.md`): тогда файл
            # ищем в той папке, иначе в папке самого скилла.
            for source in sorted(set([skill_md, *folder.rglob("*.md")])):
                body = source.read_text(encoding="utf-8")
                pattern = r"\b(?:([a-z][a-z0-9-]*)/)?((?:assets|references)/[A-Za-z0-9_.-]+\.md)\b"
                for owner, rel in sorted(set(re.findall(pattern, body))):
                    base = SKILLS / owner if owner and (SKILLS / owner).is_dir() else folder
                    if not (base / rel).exists():
                        problems.append(f"{folder.name}: {source.name} ссылается на {owner + '/' if owner else ''}{rel}, файла нет")
            # Справка по настройкам: путь считается от папки скилла.
            if "../../docs/settings.md" in text and not (folder / "../../docs/settings.md").resolve().exists():
                problems.append(f"{folder.name}: ../../docs/settings.md не существует")
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
