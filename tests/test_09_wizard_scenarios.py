"""Тест 9: сценарии мастера настройки `armarium:setup` (многоходовая часть проверена вручную, здесь ответы даны заранее).

Зачем: требования Т-6 и Т-7 (мастер создаёт и исправляет файл настроек, не трогает готовые стандарты, пишет только
с согласия человека). Мастер всегда работает с файлом `~/.claude/armarium.json` по настоящему пути (подменить домашнюю
папку для инструментов Claude через HOME нельзя, это проверено). Как тест изолирует настоящий файл:
  * Основной способ (если установлен `bwrap`, bubblewrap, и разрешены пользовательские пространства имён): `claude`
    запускается в песочнице, где поверх `~/.claude` смонтирована временная папка, а все остальные записи из
    настоящей `~/.claude` (вход в аккаунт, плагины, сессии) смонтированы в неё по одной, кроме `armarium.json` и его
    копий. Мастер видит ТОЛЬКО временный файл настроек; ваш настоящий файл вообще не затрагивается, подмены и возврата нет.
  * Запасной способ (нет `bwrap`): на время сценария настоящий файл убирается, потом возвращается, контрольная сумма
    сверяется. Тогда не пользуйтесь Claude в других окнах на время прогона.
ТРАТИТ ТОКЕНЫ (три запроса `claude -p`), поэтому по умолчанию ПРОПУСКАЕТСЯ:
чтобы запустить, задайте переменную окружения ARMARIUM_WIZARD_TEST=1.
Проверка самого теста (мутации): задайте ещё ARMARIUM_PLUGIN_DIR=<папка копии плагина со сломанным скиллом setup>; тест должен упасть.
Сценарии (в каждом хранилище и ответы выдуманные, во временной папке):
  A. Файла настроек нет, человек отказывается его записывать: файл не создан.
  B. Файл повреждён (`не json`), человек разрешает исправить: файл стал корректным JSON с нужным vault,
     рядом создана копия `armarium.json.bak-<дата>` с повреждённым текстом.
  C. Два стандарта уже лежат в хранилище, человек просит только настройки (запрета «не трогай» в запросе нет):
     стандарты не изменены (контрольные суммы), файл настроек создан.
  Ограничения (мутационная проверка 2026-10-25, сломанные копии скилла `setup`): B порчу заметил (убрано правило про
  копию .bak). A и C порчу НЕ заметили: в A просьба человека («НЕТ») совпадает с правилом скилла, в C автоматический
  запуск не доходит до диалога о содержании стандартов (ответов нет), и путь перезаписи готовых стандартов не
  выполняется. Эти два сценария ловят только грубое нарушение; чувствительный тест C потребовал бы заранее дать ответы
  на все вопросы шага 4 (дороже по токенам).
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


def sandbox_available() -> bool:
    """Есть ли рабочий `bwrap`: пробный запуск пустой команды в песочнице (нужны пользовательские пространства имён)."""
    bwrap = shutil.which("bwrap")
    if not bwrap:
        return False
    try:
        return subprocess.run([bwrap, "--dev-bind", "/", "/", "true"], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@unittest.skipUnless(RUN, "пропущен: тратит токены; задайте ARMARIUM_WIZARD_TEST=1")
class TestWizard(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        # Выдуманное хранилище с папкой Проекты.
        self.vault = self.tmp / "vault"
        (self.vault / "Проекты").mkdir(parents=True)
        self.workdir = self.tmp / "work"
        self.workdir.mkdir()
        self.sandbox = sandbox_available()
        if self.sandbox:
            self.setup_sandbox()
        else:
            self.setup_swap()

    def setup_sandbox(self):
        """Временная папка вместо ~/.claude внутри песочницы; настоящий файл настроек туда не попадает."""
        real_dir = SETTINGS.parent
        self.fake_dir = self.tmp / "claude-dir"
        self.fake_dir.mkdir()
        self.settings = self.fake_dir / "armarium.json"     # то, что мастер увидит как ~/.claude/armarium.json
        self.old_baks = set()
        args = [shutil.which("bwrap"), "--dev-bind", "/", "/", "--bind", str(self.fake_dir), str(real_dir)]
        # Остальные записи настоящей ~/.claude монтируем по одной: вход в аккаунт, плагины, сессии должны работать.
        # Источник указывает на настоящую папку (bwrap берёт источник из исходной файловой системы), назначение — внутрь
        # временной папки. Файл настроек и его копии не монтируем: мастер должен видеть только временный.
        for entry in sorted(real_dir.iterdir()):
            if entry.name == SETTINGS.name or entry.name.startswith(SETTINGS.name + "."):
                continue
            if entry.exists():
                args += ["--bind", str(entry), str(real_dir / entry.name)]
        self.bwrap_args = args
        self.before_real = sha(SETTINGS) if SETTINGS.exists() else None
        self.addCleanup(self.check_real_untouched)

    def check_real_untouched(self):
        """Настоящий файл настроек не должен измениться (в песочнице до него мастер не достаёт)."""
        after = sha(SETTINGS) if SETTINGS.exists() else None
        self.assertEqual(after, self.before_real, "настоящий файл настроек изменился во время теста")

    def setup_swap(self):
        """Запасной способ: убрать настоящий файл на время сценария и вернуть."""
        self.settings = SETTINGS
        self.bwrap_args = []
        # Копия настоящего файла (если он есть) и его контрольная сумма: по ним проверяем возврат.
        # Копия лежит рядом с настоящим файлом, а не во временной папке: если процесс убьют, она не пропадёт при очистке
        # временных файлов (находка 7).
        self.backup = SETTINGS.with_name("armarium.json.test-backup")
        if self.backup.exists():
            # Остался файл от прерванного прогона: настройки могли остаться убранными. Возвращаем их, если файла нет,
            # но дальше не идём: человек должен сам проверить состояние.
            if not SETTINGS.exists():
                shutil.copy2(self.backup, SETTINGS)
            self.fail(f"Найден файл {self.backup} от прерванного прогона. Проверьте {SETTINGS} и удалите эту копию.")
        self.had = SETTINGS.exists()
        self.before = sha(SETTINGS) if self.had else None
        if self.had:
            shutil.copy2(SETTINGS, self.backup)
            SETTINGS.unlink()
        self.old_baks = set(SETTINGS.parent.glob("armarium.json.bak-*"))
        self.had_plain_bak = SETTINGS.with_name("armarium.json.bak").exists()
        self.addCleanup(self.restore)

    def restore(self):
        """Запасной способ: возвращает настоящий файл настроек и убирает копии .bak, созданные мастером в этом прогоне."""
        if SETTINGS.exists():
            SETTINGS.unlink()
        for bak in set(SETTINGS.parent.glob("armarium.json.bak-*")) - self.old_baks:
            bak.unlink()
        plain_bak = SETTINGS.with_name("armarium.json.bak")   # копия без даты (так делает испорченный скилл); была ли до прогона
        if plain_bak.exists() and not self.had_plain_bak:
            plain_bak.unlink()
        if self.had:
            shutil.copy2(self.backup, SETTINGS)
            self.assertEqual(sha(SETTINGS), self.before, f"файл настроек не восстановлен, копия: {self.backup}")
            self.backup.unlink()   # возврат подтверждён контрольной суммой: копия больше не нужна

    def wizard(self, answers: str) -> str:
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        # Необязательно: ARMARIUM_PLUGIN_DIR — папка плагина для пробы (например, копия со сломанным скиллом, чтобы
        # проверить, что тест это заметит). Без переменной работает установленный плагин.
        plugin_dir = os.environ.get("ARMARIUM_PLUGIN_DIR")
        extra = ["--plugin-dir", plugin_dir] if plugin_dir else []
        result = subprocess.run([*self.bwrap_args, "claude", "-p", INTRO + answers, "--max-turns", "25", *extra, *TOOLS],
                                capture_output=True, text=True, cwd=self.workdir, env=env, timeout=900)
        return result.stdout

    def test_a_refuse_settings(self):
        self.wizard(f"Файла настроек нет. Соглашения прочитал. Хранилище: {self.vault} (папка Проекты есть). "
                    "Новые стандарты не нужны. Настройки (шаг 6): НЕТ, ничего не записывай в ~/.claude/armarium.json.")
        self.assertFalse(self.settings.exists(), "мастер создал файл настроек вопреки отказу")

    def test_b_fix_corrupted(self):
        self.settings.write_text("не json", encoding="utf-8")
        self.wizard(f"Файл настроек повреждён (так и есть). Соглашения прочитал. Хранилище: {self.vault}. "
                    "Новые стандарты не нужны. Исправь файл настроек: да, сначала сделай копию повреждённого файла.")
        data = json.loads(self.settings.read_text(encoding="utf-8"))          # должен быть корректным JSON
        self.assertEqual(data.get("version"), 1)
        self.assertEqual(Path(data["vault"]).expanduser(), self.vault)
        baks = set(self.settings.parent.glob("armarium.json.bak-*")) - self.old_baks
        self.assertEqual(len(baks), 1, "ожидалась одна копия повреждённого файла")
        self.assertEqual(next(iter(baks)).read_text(encoding="utf-8").strip(), "не json")

    def test_c_existing_standards_untouched(self):
        standards = [self.vault / "Проекты" / "Стандарт по названию проектов.md",
                     self.vault / "Проекты" / "Стандарт проектных заметок.md"]
        for std in standards:
            std.write_text("# готовый стандарт\n", encoding="utf-8")
        before = [sha(s) for s in standards]
        # Запрет «не трогай» здесь намеренно не произносится: тест должен проверять правило скилла, а не послушание
        # явной просьбе (мутационная проверка 2026-10-25: с запретом в запросе тест не замечал порченый скилл).
        self.wizard(f"Файла настроек нет. Соглашения прочитал. Хранилище: {self.vault}, два стандарта там уже "
                    "лежат. Из недостающих нужен только стандарт названий устройств, но содержание его не обсуждай: "
                    "его не создавай. Настройки (шаг 6): да, запиши.")
        self.assertEqual([sha(s) for s in standards], before, "мастер изменил готовые стандарты")
        self.assertTrue(self.settings.exists(), "мастер не создал файл настроек")


if __name__ == "__main__":
    unittest.main()
