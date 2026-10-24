"""Тест 7: проверка срабатывания (`checks/run_trigger.py`) сравнивает имена скиллов с учётом префикса плагина.

Зачем: требование Т-3 («скиллы срабатывают как раньше»). В режиме плагина вызывается `armarium:code-coach`,
а в наборе запросов ожидается `code-coach`; если сравнение ошибётся, проверка выдаст ложные провалы или
ложные успехи. Проверяем функцию `same_skill` и сборку флагов `plugin_args` (в нём должны быть все
скиллы плагина с отключением `off` и флаг `--plugin-dir`).
Вход: модуль `checks/run_trigger.py`, загруженный из файла. Ожидаем: ожидаемые значения в таблице ниже.
Токены не тратятся (запросы к claude не выполняются).
"""
import importlib.util
import json
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]


def load_run_trigger():
    """Загружает run_trigger.py как модуль (его имя не подходит для обычного import)."""
    spec = importlib.util.spec_from_file_location("run_trigger", PLUGIN / "checks/run_trigger.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSameSkill(unittest.TestCase):
    def test_same_skill_table(self):
        rt = load_run_trigger()
        cases = [
            ("code-coach", "armarium:code-coach", True),    # имя с префиксом плагина
            ("code-coach", "code-coach", True),             # имя без префикса
            ("code-coach", "armarium:test-plan", False),    # другой скилл
            ("docx", "anthropic-skills:docx", True),        # префикс другого набора тоже отбрасывается
            ("test-plan", "armarium:test-plan-extra", False),  # похожее имя не считается совпадением
        ]
        for expected, called, answer in cases:
            with self.subTest(expected=expected, called=called):
                self.assertEqual(rt.same_skill(expected, called), answer)

    def test_select_queries(self):
        # Фильтр запросов по скиллу (`--skill`) вместо отдельной команды `python3 -c` (находка 2).
        rt = load_run_trigger()
        items = [{"skill": "a", "query": "1"}, {"skill": "b", "query": "2"}, {"skill": "a", "query": "3"}]
        self.assertEqual([x["query"] for x in rt.select_queries(items, "a")], ["1", "3"])
        self.assertEqual(rt.select_queries(items, None), items)       # без имени возвращаются все запросы
        self.assertEqual(rt.select_queries(items, "нет"), [])

    def test_plugin_args_cover_all_skills(self):
        rt = load_run_trigger()
        args = rt.plugin_args()
        self.assertEqual(args[0], "--plugin-dir")
        overrides = json.loads(args[args.index("--settings") + 1])["skillOverrides"]
        folders = {p.name for p in (PLUGIN / "skills").iterdir() if (p / "SKILL.md").exists()}
        self.assertEqual(set(overrides), folders)                      # отключены все скиллы плагина
        self.assertEqual(set(overrides.values()), {"off"})             # и только отключением


if __name__ == "__main__":
    unittest.main()
