#!/usr/bin/env python3
"""Создаёт пробные данные для проверки скиллов (учебные проекты с намеренными изъянами).

Использование:
    python3 -I make_fixtures.py /путь/к/пустой/папке

Что создаётся (всё учебное, ничего настоящего, секреты поддельные):
    adhide-stage1/   заметки проекта на этапе 1 с неполной «Идеей» (проверка перехода между этапами)
    wc/              маленький проект на Python и заметки на этапе 4 (проверка test-plan)
    keybrd-stm-dev/  репозиторий устройства с намеренными ошибками (проверка hw-board-check)
    vulnapp/         код бота с уязвимостями и git-историей с «секретом» (проверка project-security)
    device.bin       маленький бинарный файл с известной структурой (проверка reverse-engineering)
    guiview/         requirements.txt с зависимостью под GPL (проверка выбора лицензии)
Файлы не используют сеть. Git нужен только для двух репозиториев.
"""
import struct
import subprocess
import sys
import zlib
from pathlib import Path


def write(path: Path, text: str) -> None:
    """Создаёт файл (и недостающие папки) с текстом в UTF-8."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def git(repo: Path, *args: str) -> None:
    """Запускает git в репозитории с фиксированным автором, чтобы не зависеть от ваших настроек."""
    subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", *args],
                   cwd=repo, check=True, stdout=subprocess.DEVNULL)


def status_note(code: str, stage_no: int, stage_name: str) -> str:
    """Заметка «Статус» по шаблону стандарта проектных заметок для нужного этапа."""
    names = ["Инициация", "Планирование", "Реализация", "Проверка", "Релиз", "Сопровождение"]
    rows = []
    for i, n in enumerate(names, 1):
        state = "выполнен" if i < stage_no else ("идёт" if i == stage_no else "не начат")
        rows.append(f"| {i} | {n} | {state} | |")
    return (f"# {code} - Статус\n\nТип: tool · Группа: ПО\nСостояние проекта: активен\nПричина состояния: —\n"
            f"Текущий этап: {stage_no} {stage_name}\nВерсия или ревизия: нет\nСледующий шаг: —\nБлокеры: нет\n"
            f"Обновлено: 2026-10-24\n\n## Этапы\n\n| № | Этап | Состояние | Заметки |\n| --- | --- | --- | --- |\n"
            + "\n".join(rows) + f"\n\n## Чек-лист текущего этапа\n\n- [ ] критерий выхода\n\nОткрытые вопросы: [[{code} - Вопросы]]\n")


def questions_note(code: str) -> str:
    return (f"# {code} - Вопросы\n\n| № | Вопрос | Варианты | Статус | Решение |\n| --- | --- | --- | --- | --- |\n")


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)

    # 1. Этап 1 с неполной «Идеей»: скилл не должен переводить проект на этап 2.
    base = out / "adhide-stage1/Проекты/adhide"
    write(base / "adhide - Статус.md", status_note("adhide", 1, "Инициация"))
    write(base / "adhide - Идея.md", "# adhide - Идея\n\n## Проблема\nРеклама на YouTube мешает смотреть видео.\n\n"
                                     "## Цель\n<что должно получиться, 1–2 фразы>\n\n## Для Кого\n\n## Критерии Успеха\n\n## Что Не Входит\n")
    write(base / "adhide - Вопросы.md", questions_note("adhide"))

    # 2. Проект wc: функция подсчёта слов и заметки на этапе 4.
    write(out / "wc/code/wc/wordcount.py",
          'def count_words(text):\n    """Возвращает число слов в строке (слова разделены пробельными символами)."""\n    return len(text.split())\n')
    nb = out / "wc/Проекты/wc"
    write(nb / "wc - Статус.md", status_note("wc", 4, "Проверка"))
    write(nb / "wc - Идея.md", "# wc - Идея\n\n## Цель\nФункция count_words считает число слов в строке.\n\n## Критерии Успеха\n"
                               "- На обычной строке возвращает число слов.\n- На пустой строке возвращает 0.\n- Несколько пробелов подряд не создают лишних слов.\n")
    write(nb / "wc - Вопросы.md", questions_note("wc"))

    # 3. Репозиторий устройства с изъянами: шёлк с rA вместо rB, дубль R1, LED1, нет тега по стандарту.
    dev = out / "keybrd-stm-dev"
    write(dev / "pcb/keybrd.kicad_pro", '{"meta":{"filename":"keybrd.kicad_pro","version":1}}\n')
    write(dev / "pcb/keybrd.kicad_pcb", '(kicad_pcb (version 20240108)\n (gr_text "KEYBRD rA 2026-10" (at 10 10) (layer "F.SilkS"))\n)\n')
    write(dev / "pcb/keybrd.kicad_sch",
          '(kicad_sch (version 20231120)\n (symbol (lib_id "Device:R") (property "Reference" "R1") (property "Value" "10k"))\n'
          ' (symbol (lib_id "Device:R") (property "Reference" "R1") (property "Value" "4k7"))\n'
          ' (symbol (lib_id "Device:LED") (property "Reference" "LED1"))\n)\n')
    write(dev / "case/case.scad", "solid placeholder v1\n")
    write(dev / "docs/passport.md", "| Поколение | Плата | Корпус | Прошивка | Статус | Дата | Примечание |\n| --- | --- | --- | --- | --- | --- | --- |\n"
                                    "| g1 | rA | v1 | keybrd-embed-headless-fw v0.3 | проверено | 2026-09-02 | |\n")
    subprocess.run(["git", "init", "-q", "."], cwd=dev, check=True)
    git(dev, "add", "-A")
    git(dev, "commit", "-qm", "init")
    git(dev, "tag", "v1.0")

    # 4. Бот с уязвимостями; «секрет» (поддельный) лежит в истории git.
    app = out / "vulnapp/code/vulnapp"
    write(app / "app.py",
          'import logging\nimport os\nimport pickle\nimport sqlite3\nimport subprocess\n\n'
          'TOKEN = "123456:FAKE-TEST-TOKEN-not-real"\nlogging.basicConfig(level=logging.INFO)\n\n\n'
          'def handle_message(user_text, raw_state):\n    logging.info("token=%s text=%s", TOKEN, user_text)\n'
          '    state = pickle.loads(raw_state)\n    out = subprocess.run("ping -c 1 " + user_text, shell=True, capture_output=True)\n'
          '    con = sqlite3.connect("bot.db")\n    rows = con.execute("SELECT * FROM users WHERE name = \'" + user_text + "\'").fetchall()\n'
          '    return out.stdout, rows, state\n\n\n'
          'def read_file(name):\n    with open(os.path.join("/srv/files", name), "rb") as f:\n        return f.read()\n')
    write(app / ".env", "BOT_TOKEN=123456:FAKE-TEST-TOKEN-not-real\n")
    subprocess.run(["git", "init", "-q", "-b", "gen-1", "."], cwd=app, check=True)
    git(app, "add", "-A")
    git(app, "commit", "-qm", "init")
    git(app, "rm", "-q", "--cached", ".env")     # убираем из индекса, но в первой версии истории файл остался
    (app / ".env").unlink()
    git(app, "commit", "-qm", "remove env")
    vn = out / "vulnapp/Проекты/vulnapp"
    write(vn / "vulnapp - Статус.md", status_note("vulnapp", 4, "Проверка").replace("Тип: tool", "Тип: bot"))
    write(vn / "vulnapp - Вопросы.md", questions_note("vulnapp"))

    # 5. Бинарный файл с известной структурой: заголовок DEVX, версия, число записей, записи тип-длина-данные, CRC32.
    records = [(1, b"ssid=home"), (2, b"\x01\x00\xc0\xa8\x00\x0a"), (3, b"name=sensor-7")]
    body = b"".join(struct.pack("<BH", t, len(p)) + p for t, p in records)
    data = b"DEVX" + struct.pack("<HH", 1, len(records)) + body
    data += struct.pack("<I", zlib.crc32(data))
    (out / "device.bin").write_bytes(data)

    # 6. Проект с зависимостью под GPL: выбор лицензии MIT должен показать конфликт.
    gv = out / "guiview/guiview-linux-gui-app"
    write(gv / "requirements.txt", "requests==2.32.3\nnumpy==2.1.0\nPyQt5==5.15.11\n")
    write(gv / "main.py", "import requests\nimport numpy\nfrom PyQt5 import QtWidgets\n")
    print(f"Готово: {out}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Использование: python3 -I make_fixtures.py /путь/к/пустой/папке")
    main(Path(sys.argv[1]))
