"""Тест 5: `tools/make_vault_copy.py` правильно читает настройки и строит копию в хранилище.

Зачем: требования Т-5 (копия и описания в хранилище строятся из плагина) и Т-8 (корень хранилища берётся из
`~/.claude/armarium.json`). Скрипт определяет домашнюю папку по переменной HOME, поэтому тест подставляет временную
домашнюю папку и временное хранилище: ваши настоящие файлы не затрагиваются.
Сценарии ошибок (ожидаем код возврата 1 и понятное сообщение, ничего не записано): нет файла настроек, неизвестная
версия схемы, папки хранилища нет, файл не JSON. Сценарий успеха: код возврата 0, в хранилище создана папка
`Документация/Скиллы Claude/Копия`, и её содержимое совпадает с папкой `skills/` плагина файл в файл.
Токены не тратятся.
"""
import filecmp
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "tools/make_vault_copy.py"


def run_script(home: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "HOME": str(home)}
    return subprocess.run([sys.executable, "-I", str(SCRIPT)], capture_output=True, text=True, env=env, timeout=120)


def same_tree(left: Path, right: Path) -> bool:
    """Папки совпадают: одинаковые имена и одинаковое содержимое файлов на всех уровнях."""
    cmp = filecmp.dircmp(left, right)
    if cmp.left_only or cmp.right_only or cmp.funny_files:
        return False
    _, mismatch, errors = filecmp.cmpfiles(left, right, cmp.common_files, shallow=False)
    return not mismatch and not errors and all(same_tree(left / d, right / d) for d in cmp.common_dirs)


class TestMakeVaultCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.vault = self.tmp / "vault"
        self.vault.mkdir()

    def settings(self, content: str):
        (self.home / ".claude" / "armarium.json").write_text(content, encoding="utf-8")

    def assert_fails(self, text: str):
        result = run_script(self.home)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(text, result.stderr)
        self.assertEqual(list(self.vault.iterdir()), [], "при ошибке в хранилище ничего не должно появиться")

    def test_errors(self):
        self.assert_fails("не найден")                                                          # нет файла настроек
        self.settings(json.dumps({"version": 2, "vault": str(self.vault)}))
        self.assert_fails("неизвестная версия")
        self.settings(json.dumps({"version": 1, "vault": str(self.tmp / "нет-такой-папки")}))
        self.assert_fails("не найдена")                                                         # папки хранилища нет
        self.settings("не json")
        self.assert_fails("не является корректным JSON")

    def test_copy_equals_plugin(self):
        self.settings(json.dumps({"version": 1, "vault": str(self.vault)}))
        result = run_script(self.home)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        copy = self.vault / "Документация" / "Скиллы Claude" / "Копия"
        self.assertTrue(copy.is_dir())
        self.assertTrue(same_tree(PLUGIN / "skills", copy), "копия не совпадает с папкой skills/ плагина")


if __name__ == "__main__":
    unittest.main()
