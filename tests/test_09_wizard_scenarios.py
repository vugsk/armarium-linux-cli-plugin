"""Тест 9: сценарии мастера настройки `armarium:setup` (многоходовая часть проверена вручную, здесь ответы даны заранее).

Зачем: требования Т-6 и Т-7 (мастер создаёт и исправляет файл настроек, не трогает готовые стандарты, пишет только
с согласия человека). Мастер всегда работает с НАСТОЯЩИМ файлом `~/.claude/armarium.json` (подменить домашнюю папку
для инструментов Claude нельзя, это проверено), поэтому тест на время подменяет этот файл: сохраняет копию, убирает
файл, после каждого сценария возвращает копию и сверяет контрольную сумму. Если вернуть файл не удалось, тест
падает с понятной ошибкой (копия остаётся во временной папке, путь в сообщении).
ТРАТИТ ТОКЕНЫ (три запроса `claude -p`) и меняет ваш файл настроек на время прогона, поэтому по умолчанию ПРОПУСКАЕТСЯ:
чтобы запустить, задайте переменную окружения ARMARIUM_WIZARD_TEST=1 (и не пользуйтесь Claude в других окнах на это время).
Сценарии (в каждом хранилище и ответы выдуманные, во временной папке):
  A. Файла настроек нет, человек отказывается его записывать: файл не создан.
  B. Файл повреждён (`не json`), человек разрешает исправить: файл стал корректным JSON с нужным vault,
     рядом создана копия `armarium.json.bak-<дата>` с повреждённым текстом.
  C. Два стандарта уже лежат в хранилище, человек просит только настройки: стандарты не изменены (контрольные суммы),
     файл настроек создан.
"""
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SETTINGS = Path.home() / ".claude" / "armarium.json"
RUN = os.environ.get("ARMARIUM_WIZARD_TEST") == "1" and shutil.which("claude")
TOOLS = ["--allowedTools", "Read", "Write", "Edit", "Bash(mkdir:*)", "Bash(ls:*)", "Bash(cat:*)", "Bash(cp:*)"]
INTRO = ("Настрой armarium. Это автоматическая проверка мастера: я отвечаю на все вопросы заранее, "
         "спрашивать меня не нужно, действуй по шагам мастера. Память не записывай (шаг 7: нет). ")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(RUN, "пропущен: тратит токены и меняет ваш файл настроек; задайте ARMARIUM_WIZARD_TEST=1")
class TestWizard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # Копия настоящего файла (если он есть) и его контрольная сумма: по ним проверяем возврат.
        self.backup = self.tmp / "armarium.json.real"
        self.had = SETTINGS.exists()
        self.before = sha(SETTINGS) if self.had else None
        if self.had:
            shutil.copy2(SETTINGS, self.backup)
            SETTINGS.unlink()
        self.old_baks = set(SETTINGS.parent.glob("armarium.json.bak-*"))
        self.addCleanup(self.restore)
        # Выдуманное хранилище с папкой Проекты.
        self.vault = self.tmp / "vault"
        (self.vault / "Проекты").mkdir(parents=True)
        self.workdir = self.tmp / "work"
        self.workdir.mkdir()

    def restore(self):
        """Возвращает настоящий файл настроек и убирает копии .bak, созданные мастером в этом прогоне."""
        if SETTINGS.exists():
            SETTINGS.unlink()
        for bak in set(SETTINGS.parent.glob("armarium.json.bak-*")) - self.old_baks:
            bak.unlink()
        if self.had:
            shutil.copy2(self.backup, SETTINGS)
            self.assertEqual(sha(SETTINGS), self.before, f"файл настроек не восстановлен, копия: {self.backup}")

    def wizard(self, answers: str) -> str:
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        result = subprocess.run(["claude", "-p", INTRO + answers, "--max-turns", "25", *TOOLS],
                                capture_output=True, text=True, cwd=self.workdir, env=env, timeout=900)
        return result.stdout

    def test_a_refuse_settings(self):
        self.wizard(f"Файла настроек нет. Соглашения прочитал. Хранилище: {self.vault} (папка Проекты есть). "
                    "Новые стандарты не нужны. Настройки (шаг 6): НЕТ, ничего не записывай в ~/.claude/armarium.json.")
        self.assertFalse(SETTINGS.exists(), "мастер создал файл настроек вопреки отказу")

    def test_b_fix_corrupted(self):
        SETTINGS.write_text("не json", encoding="utf-8")
        self.wizard(f"Файл настроек повреждён (так и есть). Соглашения прочитал. Хранилище: {self.vault}. "
                    "Новые стандарты не нужны. Исправь файл настроек: да, сначала сделай копию повреждённого файла.")
        data = json.loads(SETTINGS.read_text(encoding="utf-8"))          # должен быть корректным JSON
        self.assertEqual(data.get("version"), 1)
        self.assertEqual(Path(data["vault"]).expanduser(), self.vault)
        baks = set(SETTINGS.parent.glob("armarium.json.bak-*")) - self.old_baks
        self.assertEqual(len(baks), 1, "ожидалась одна копия повреждённого файла")
        self.assertEqual(next(iter(baks)).read_text(encoding="utf-8").strip(), "не json")

    def test_c_existing_standards_untouched(self):
        standards = [self.vault / "Проекты" / "Стандарт по названию проектов.md",
                     self.vault / "Проекты" / "Стандарт проектных заметок.md"]
        for std in standards:
            std.write_text("# готовый стандарт\n", encoding="utf-8")
        before = [sha(s) for s in standards]
        self.wizard(f"Файла настроек нет. Соглашения прочитал. Хранилище: {self.vault}, два готовых стандарта там "
                    "лежат, не трогай их, новые не нужны. Настройки (шаг 6): да, запиши.")
        self.assertEqual([sha(s) for s in standards], before, "мастер изменил готовые стандарты")
        self.assertTrue(SETTINGS.exists(), "мастер не создал файл настроек")


if __name__ == "__main__":
    unittest.main()
