"""Тест 6: обязательные заголовки контракта стандартов есть в скелетах мастера.

Зачем: требования Т-6 и Т-9. Мастер `setup` пишет черновики стандартов по скелетам
(`skills/setup/references/skeletons.md`), а скиллы потом ищут в стандартах разделы по дословным заголовкам
из контракта (`docs/standards-contract.md`). Если заголовок из контракта пропал из скелета, черновик сломает скиллы.
Берём из контракта все заголовки в обратных кавычках (`## ...`, `### ...`), кроме тех, что в нём же помечены
как необязательные или не относящиеся к стандартам, и проверяем, что каждый есть в скелетах.
Ожидаем: ни одного недостающего заголовка. Токены не тратятся.
"""
import re
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
# Заголовки, которых в скелетах быть не обязано: необязательные разделы стандарта автора,
# журнал решений автора и подзаголовок внутри формата заметки `Статус`.
OPTIONAL = {
    "## Примеры",
    "## Стадии Зрелости — Не В Имени, а В Версиях",
    "## Открытые Пункты Стандарта",
    "## Чек-лист текущего этапа",
    "### Файлы Проекта EDA",
}


class TestContract(unittest.TestCase):
    def test_required_headings_in_skeletons(self):
        contract = (PLUGIN / "docs/standards-contract.md").read_text(encoding="utf-8")
        skeletons = (PLUGIN / "skills/setup/references/skeletons.md").read_text(encoding="utf-8")
        required = set(re.findall(r"`(#{2,3} [^`]+)`", contract)) - OPTIONAL
        self.assertGreater(len(required), 20, "из контракта разобрано слишком мало заголовков")
        missing = sorted(h for h in required if h not in skeletons)
        self.assertEqual(missing, [], "нет в скелетах: " + ", ".join(missing))


if __name__ == "__main__":
    unittest.main()
