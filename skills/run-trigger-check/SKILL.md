---
name: run-trigger-check
description: Ручной запуск проверки срабатывания скиллов по набору запросов (тратит токены аккаунта). Вызывается только пользователем командой /armarium:run-trigger-check.
disable-model-invocation: true
argument-hint: [имя скилла для фильтра]
allowed-tools: Read, Bash(python3 -I ${CLAUDE_PLUGIN_ROOT}/checks/run_trigger.py *), AskUserQuestion
---

Проверь, срабатывают ли скиллы на запросах из `${CLAUDE_PLUGIN_ROOT}/checks/queries.json` с помощью `${CLAUDE_PLUGIN_ROOT}/checks/run_trigger.py`. Подробности и ограничения — в `${CLAUDE_PLUGIN_ROOT}/checks/Проверки скиллов - как запускать.md`.

1. Узнай, сколько запросов будет выполнено: прочитай `queries.json` (`Read`) и посчитай все запросы или, если указан аргумент ($ARGUMENTS), только запросы этого скилла (поле `skill`). Отдельных команд для фильтра не запускай: фильтр делает сам скрипт параметром `--skill`.
2. Скажи пользователю, сколько запросов будет выполнено. **Каждый запрос — отдельный запуск `claude -p`, он тратит токены аккаунта.** Спроси подтверждение (`AskUserQuestion`); без «да» не запускай.
3. После подтверждения: `python3 -I ${CLAUDE_PLUGIN_ROOT}/checks/run_trigger.py ${CLAUDE_PLUGIN_ROOT}/checks/queries.json 4 <файл результата во временной папке>`, а для одного скилла добавь в конец `--skill <имя>`.
4. Покажи итог (сколько прошло) и список непрошедших. Напомни, что один запуск на запрос только сигнал, спорные запросы стоит повторить.
