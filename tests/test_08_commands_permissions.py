"""Тест 8: у скиллов плагина нет слишком широких разрешений на запуск программ.

Зачем: находки 1 и 2 проверки безопасности (заметка «Безопасность», 2026-10-25). В поле `allowed-tools` скилла
перечислены инструменты, которые разрешены без вопроса. Голый `Bash` и шаблон `Bash(python3 -I:*)` разрешают любую
команду оболочки или любой код на Python; через инструкции в содержимом хранилища это превращается в выполнение
произвольных команд с правами пользователя. Тест следит, чтобы такие разрешения не вернулись:
  1. в `allowed-tools` нет голого `Bash` (без шаблона в скобках);
  2. нет шаблонов, разрешающих любой `python3`, любую оболочку или любую программу: `Bash(*)`, `Bash(python3:*)`,
     `Bash(python3 -I:*)`, `Bash(python3 *)`, `Bash(bash:*)`, `Bash(sh:*)`.
Ожидаем: ни одного нарушения. Токены не тратятся.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
TOO_BROAD = {"Bash(*)", "Bash(python3:*)", "Bash(python3 *)", "Bash(python3 -I:*)", "Bash(python3 -I *)",
             "Bash(bash:*)", "Bash(sh:*)", "Bash(env:*)"}


def allowed_tools(text: str) -> list[str]:
    """Читает значение `allowed-tools` из шапки скилла: строка через запятую, шаблоны Bash(...) не разбиваются."""
    match = re.search(r"^allowed-tools:\s*(.+)$", text, re.M)
    if not match:
        return []
    value, items, depth, current = match.group(1), [], 0, ""
    for char in value:
        depth += char == "("
        depth -= char == ")"
        if char == "," and depth == 0:          # запятая внутри скобок принадлежит шаблону, а не разделяет инструменты
            items.append(current.strip())
            current = ""
        else:
            current += char
    items.append(current.strip())
    return [x for x in items if x]


class TestCommandsPermissions(unittest.TestCase):
    def test_no_broad_bash(self):
        problems = []
        self.assertFalse((PLUGIN / "commands").exists(), "папка commands/ вернулась: ручные запуски теперь скиллы")
        commands = sorted((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertGreater(len(commands), 0, "в skills/ нет ни одного скилла")
        for command in commands:
            for tool in allowed_tools(command.read_text(encoding="utf-8")):
                if tool == "Bash":
                    problems.append(f"{command.parent.name}: голый Bash без ограничений")
                if tool in TOO_BROAD:
                    problems.append(f"{command.parent.name}: слишком широкое разрешение {tool}")
        self.assertEqual(problems, [], "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
