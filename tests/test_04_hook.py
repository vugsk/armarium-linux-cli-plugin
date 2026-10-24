"""Тест 4: хук-напоминание `hooks/audit-reminder.sh` срабатывает ровно там, где нужно.

Зачем: требования Т-4 (напоминание после правки стандартов и скиллов), Т-5 и Т-8 (папка хранилища берётся
из настроек `~/.claude/armarium.json`, а не прописана в скрипте). Хук получает JSON на стандартный ввод и
либо молчит, либо печатает JSON с напоминанием для Claude. Настройки скрипт ищет в `$HOME/.claude`, поэтому
тест подставляет временную домашнюю папку и временное «хранилище»: ваши настоящие файлы не затрагиваются.
Сценарии: ожидание «напоминание» (REMIND) или «тишина» (SILENT):
  1. стандарт в хранилище из настроек, 2. файл скилла плагина, 3. заметка проекта, 4. посторонний файл,
  5. без настроек, стандарт, 6. без настроек, скилл плагина, 7. настройки на другое хранилище, стандарт старого,
  8. то же, стандарт нового, 9. файл настроек повреждён, скилл плагина.
Нужны bash и jq; если jq нет, тест пропускается. Токены не тратятся.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
HOOK = PLUGIN / "hooks/audit-reminder.sh"
STANDARD = "Стандарт проектных заметок.md"


def run_hook(home: Path, file_path: str) -> str:
    """Запускает хук с подменённой домашней папкой и возвращает его вывод (пустая строка — тишина)."""
    event = json.dumps({"tool_input": {"file_path": file_path}})
    env = {**os.environ, "HOME": str(home)}
    result = subprocess.run(["bash", str(HOOK)], input=event, capture_output=True, text=True, env=env, timeout=30)
    assert result.returncode == 0, result.stderr   # хук не должен падать ни в одном сценарии
    return result.stdout.strip()


def is_reminder(output: str) -> bool:
    """Напоминание — это JSON со строкой про standards-audit в additionalContext."""
    if not output:
        return False
    data = json.loads(output)
    return "standards-audit" in data["hookSpecificOutput"]["additionalContext"]


@unittest.skipUnless(shutil.which("jq"), "утилита jq не найдена")
class TestHook(unittest.TestCase):
    def setUp(self):
        # Временная «машина»: домашняя папка с .claude и два хранилища (рабочее и «другое»).
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.vault = self.tmp / "vault"
        self.other = self.tmp / "other"
        for vault in (self.vault, self.other):
            (vault / "Проекты").mkdir(parents=True)
            (vault / "Проекты" / STANDARD).write_text("стандарт", encoding="utf-8")
        self.skill = str(PLUGIN / "skills/code-coach/SKILL.md")   # файл скилла плагина (путь нужен, содержимое нет)

    def settings(self, content: str):
        (self.home / ".claude" / "armarium.json").write_text(content, encoding="utf-8")

    def good(self, vault: Path):
        self.settings(json.dumps({"version": 1, "vault": str(vault)}))

    def test_scenarios(self):
        std = lambda vault: str(vault / "Проекты" / STANDARD)
        self.good(self.vault)
        self.assertTrue(is_reminder(run_hook(self.home, std(self.vault))), "1: стандарт при настройках")
        self.assertTrue(is_reminder(run_hook(self.home, self.skill)), "2: скилл плагина")
        note = self.vault / "Проекты" / "armarium - Статус.md"
        self.assertFalse(is_reminder(run_hook(self.home, str(note))), "3: заметка проекта не повод")
        self.assertFalse(is_reminder(run_hook(self.home, "/tmp/посторонний.md")), "4: посторонний файл")
        # Без настроек: стандарты неизвестны, скиллы плагина по-прежнему отслеживаются.
        (self.home / ".claude" / "armarium.json").unlink()
        self.assertFalse(is_reminder(run_hook(self.home, std(self.vault))), "5: без настроек, стандарт")
        self.assertTrue(is_reminder(run_hook(self.home, self.skill)), "6: без настроек, скилл")
        # Настройки указывают на другое хранилище.
        self.good(self.other)
        self.assertFalse(is_reminder(run_hook(self.home, std(self.vault))), "7: стандарт старого хранилища")
        self.assertTrue(is_reminder(run_hook(self.home, std(self.other))), "8: стандарт нового хранилища")
        # Повреждённый файл настроек.
        self.settings("не json")
        self.assertTrue(is_reminder(run_hook(self.home, self.skill)), "9: файл повреждён, скилл")


if __name__ == "__main__":
    unittest.main()
