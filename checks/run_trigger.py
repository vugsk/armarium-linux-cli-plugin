#!/usr/bin/env python3
"""Проверка срабатывания пользовательских скиллов по их описанию.

Идея: для каждого запроса из файла запросов запускаем `claude -p` в ПУСТОЙ папке,
читаем потоковые события и смотрим, какие скиллы Claude вызвал в первых нескольких
вызовах инструментов. Сравниваем с ожиданием из файла запросов.

Использование (из этой папки):
    python3 -I run_trigger.py queries.json 4 results.json [--plugin-mode] [--skill ИМЯ] [дополнительные флаги claude]

    queries.json   — список запросов (формат ниже)
    4              — сколько запросов выполнять параллельно
    results.json   — куда записать подробный результат
    --plugin-mode  — запуск в режиме плагина: подключить этот плагин (--plugin-dir) и скрыть оригиналы
                     из ~/.claude/skills через skillOverrides, чтобы скиллы не задваивались
                     (способ проверен 2026-10-24, см. заметку вехи 2 проекта armarium)
    --skill ИМЯ    — взять из файла запросов только запросы этого скилла (так фильтр запросов делается внутри
                     скрипта, а не отдельной командой python3 -c: см. находку 2 заметки «Безопасность»)
    остальное      — всё, что идёт после, передаётся команде `claude` как есть
                     (например, --model sonnet)

Имена скиллов сравниваются без префикса плагина: в режиме плагина вызывается `armarium:code-coach`,
а в файле запросов ожидается `code-coach`, и это считается совпадением.

Формат queries.json — список объектов:
    {"skill": "имя скилла", "should_trigger": true/false, "query": "текст запроса"}

Важно:
  * Каждый запуск `claude -p` тратит токены вашего аккаунта; запросов много — запускай осознанно.
  * Срабатывание вероятностное: один запуск на запрос показывает явные ошибки, но не гарантию.
  * Нужна установленная командная строка `claude` (проверено на версии 2.1.x).
"""
import json
import os
import select
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Рабочая папка для claude создаётся при каждом запуске скрипта заново (см. main): пустая, чтобы в ней не было
# ни проектных скиллов, ни файлов, влияющих на выбор (установленные плагины и пользовательские скиллы при этом
# видны). Имя случайное и папка закрытая (права только у владельца): фиксированное общее имя в /tmp позволило бы
# другому пользователю машины заранее подготовить папку с чужим `.claude/` или `CLAUDE.md` (находка 3).

TIMEOUT = 150   # сколько секунд ждём один запрос, потом считаем, что скилл не вызван
MAX_TOOLS = 3   # смотрим только первые три вызова инструментов: скилл вызывают в начале


def plugin_args() -> list[str]:
    """Флаги claude для режима плагина: подключить плагин и скрыть оригиналы его скиллов.

    Плагин лежит на уровень выше этой папки (checks/ — внутри плагина). Без отключения оригиналов
    из ~/.claude/skills в списке скиллов оказались бы и они, и скиллы плагина с префиксом, и модель
    могла бы вызвать оригинал, тогда проверка ничего не доказывала бы.
    """
    root = HERE.parent
    # Имена скиллов — это имена папок плагина со SKILL.md; ровно такие имена и у оригиналов.
    names = sorted(p.name for p in (root / "skills").iterdir() if (p / "SKILL.md").exists())
    # skillOverrides со значением "off" скрывает скилл от Claude, но файлы на диске не трогает.
    settings = json.dumps({"skillOverrides": {name: "off" for name in names}})
    return ["--plugin-dir", str(root), "--settings", settings]


def same_skill(expected: str, called: str) -> bool:
    """Совпадает ли вызванный скилл с ожидаемым, не считая префикса плагина.

    `armarium:code-coach` и `code-coach` — один и тот же скилл. Префикс отделён двоеточием,
    поэтому берём часть после последнего двоеточия.
    """
    return called.split(":")[-1] == expected


def select_queries(items: list[dict], skill: str | None) -> list[dict]:
    """Оставляет запросы одного скилла; без имени (None) возвращает все запросы."""
    return [it for it in items if skill is None or it["skill"] == skill]


def run_query(query: str, extra: list[str], cwd: Path) -> dict:
    """Запускает один запрос и возвращает, какие скиллы и инструменты были вызваны.

    extra — дополнительные флаги для claude (например, из plugin_args()).
    cwd — пустая рабочая папка, в которой запускается claude.
    """
    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json",   # события построчно в формате JSON
        "--verbose",
        "--include-partial-messages",       # чтобы увидеть вызов инструмента как можно раньше
        *extra,
    ]
    # Переменную CLAUDECODE убираем, иначе вложенный запуск claude внутри сеанса claude отказывается работать.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, cwd=cwd, env=env)

    skills: list[str] = []   # имена вызванных скиллов
    tools: list[str] = []    # имена всех вызванных инструментов
    pending = None           # имя инструмента, чьи параметры сейчас приходят по частям
    acc = ""                 # накопленные части параметров (JSON)
    buf = ""                 # необработанный остаток вывода
    start = time.time()
    try:
        while time.time() - start < TIMEOUT:
            if proc.poll() is not None:
                # Процесс завершился: дочитываем остаток вывода и разбираем его целиком.
                buf += proc.stdout.read().decode("utf-8", errors="replace")
                lines, buf = buf.split("\n"), ""
            else:
                # Ждём новые данные не дольше секунды, чтобы вовремя проверять таймаут.
                ready, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not ready:
                    continue
                chunk = os.read(proc.stdout.fileno(), 8192)
                if not chunk:
                    break
                buf += chunk.decode("utf-8", errors="replace")
                *lines, buf = buf.split("\n")   # последняя (возможно неполная) строка остаётся в buf
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("type") == "stream_event":
                    se = ev.get("event", {})
                    t = se.get("type")
                    if t == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":      # начался вызов инструмента
                            pending = cb.get("name")
                            acc = ""
                            tools.append(pending)
                    elif t == "content_block_delta" and pending:
                        d = se.get("delta", {})
                        if d.get("type") == "input_json_delta":
                            acc += d.get("partial_json", "")  # копим параметры вызова
                    elif t == "content_block_stop" and pending:
                        if pending == "Skill":                # параметры вызова скилла: его имя
                            try:
                                skills.append(json.loads(acc).get("skill", "?"))
                            except json.JSONDecodeError:
                                skills.append("?")
                        pending = None
                        if len(tools) >= MAX_TOOLS or skills:
                            return {"query": query, "skills": skills, "tools": tools}
                    elif t == "message_stop" and not pending:
                        return {"query": query, "skills": skills, "tools": tools}
                elif ev.get("type") == "result":
                    return {"query": query, "skills": skills, "tools": tools}
            if proc.poll() is not None:
                break
        return {"query": query, "skills": skills, "tools": tools, "note": "timeout"}
    finally:
        # В любом случае не оставляем процесс работать.
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def main() -> None:
    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else HERE / "results.json"

    # Всё после третьего аргумента — флаги. Слово --plugin-mode раскрываем сами (подключение плагина и
    # скрытие оригиналов), --skill ИМЯ используем сами (фильтр запросов), остальные передаём claude без изменений.
    extra: list[str] = []
    only_skill = None
    rest = iter(sys.argv[4:])
    for arg in rest:
        if arg == "--plugin-mode":
            extra += plugin_args()
        elif arg == "--skill":
            only_skill = next(rest, None)            # значение идёт следующим аргументом
            if not only_skill:
                sys.exit("После --skill нужно имя скилла.")
        else:
            extra.append(arg)
    items = select_queries(items, only_skill)
    if not items:
        sys.exit(f"В файле запросов нет запросов для скилла {only_skill!r}.")
    print("Режим --plugin-mode:", "да (плагин из папки, оригиналы скрыты)" if "--plugin-dir" in extra else "нет (установленные плагины и скиллы пользователя как есть)")

    # Пустая рабочая папка со случайным именем и правами только у владельца; удаляется в конце в любом случае.
    cwd = Path(tempfile.mkdtemp(prefix="skills-check-"))
    try:
        # Выполняем запросы параллельно; результат объединяем с исходным описанием запроса.
        with ThreadPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(lambda it: {**run_query(it["query"], extra, cwd), **it}, items))
    finally:
        shutil.rmtree(cwd, ignore_errors=True)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    passed_total = 0
    for r in results:
        # Совпадение считаем без префикса плагина (armarium:code-coach == code-coach).
        triggered = any(same_skill(r["skill"], called) for called in r["skills"])
        # Ожидали срабатывание — должен был вызваться именно этот скилл;
        # не ожидали — этот скилл не должен был вызваться.
        passed = triggered if r["should_trigger"] else not triggered
        passed_total += passed
        print(f"[{'PASS' if passed else 'FAIL'}] {r['skill']:20} ждали={r['should_trigger']!s:5} "
              f"вызваны={r['skills']} :: {r['query'][:60]}")
    print(f"{passed_total}/{len(results)} прошло")


if __name__ == "__main__":
    main()
