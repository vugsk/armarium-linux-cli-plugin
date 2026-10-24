"""Тест 1: плагин проходит официальную проверку `claude plugin validate`.

Зачем: требование Т-12 (плагин проходит `claude plugin validate` без ошибок). Проверка ловит ошибки
в манифесте, хуках, скиллах и командах раньше, чем плагин сломается у пользователя.
Вход: папка плагина (на уровень выше этой папки tests). Ожидаем: код возврата 0 и строка
«Validation passed» в выводе. Если команды `claude` нет в системе, тест пропускается (не падает).
Токены не тратятся: проверка локальная.
"""
import shutil
import subprocess
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]   # корень плагина


@unittest.skipUnless(shutil.which("claude"), "команда claude не найдена в PATH")
class TestValidate(unittest.TestCase):
    def test_plugin_validates(self):
        # Запускаем проверку и собираем вывод (stdout и stderr вместе: в какой из них пишет команда, неважно).
        result = subprocess.run(["claude", "plugin", "validate", str(PLUGIN)],
                                capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        # Код возврата 0 — признак успеха; текст нужен, чтобы тест не прошёл по ошибке на пустом выводе.
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("Validation passed", output)


if __name__ == "__main__":
    unittest.main()
