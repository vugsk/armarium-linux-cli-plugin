"""Тест 2: в плагине нет жёстко прописанных путей чьей-то машины.

Зачем: требование Т-8 (пути берутся из настроек, а не из текста скиллов, хука и скриптов), иначе плагин
не работает на другой машине. Ищем в тексте всех файлов плагина (кроме `.git` и папки tests, где такие строки
встречаются в самих шаблонах поиска): `/home/` и `disk_docs` (имя вашей папки хранилища).
Вход: файлы плагина. Ожидаем: ни одного совпадения. Бинарные файлы пропускаем.
"""
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
FORBIDDEN = ["/home/", "disk_docs"]            # признаки пути конкретной машины и вашего хранилища
SKIP_DIRS = {".git", "tests", "__pycache__"}   # служебные папки: в tests эти строки лежат намеренно


class TestNoHardcodedPaths(unittest.TestCase):
    def test_no_machine_paths(self):
        found = []
        for path in PLUGIN.rglob("*"):
            # Пропускаем папки из списка и всё, что в них лежит.
            if not path.is_file() or any(part in SKIP_DIRS for part in path.relative_to(PLUGIN).parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue   # бинарный файл, искать в нём нечего
            for line_no, line in enumerate(text.splitlines(), 1):
                for bad in FORBIDDEN:
                    if bad in line:
                        found.append(f"{path.relative_to(PLUGIN)}:{line_no}: {bad}")
        self.assertEqual(found, [], "жёсткие пути:\n" + "\n".join(found))


if __name__ == "__main__":
    unittest.main()
