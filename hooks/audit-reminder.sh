#!/usr/bin/env bash
# Хук PostToolUse (Edit|Write) плагина armarium: напоминание после правки стандартов и скиллов.
# Читает JSON со стандартного ввода и берёт путь изменённого файла.
# Если файл — один из трёх стандартов или файл внутри папки скиллов плагина, выводит JSON,
# по которому Claude получает напоминание.
# Во всех остальных случаях молчит и ничего не делает.

FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[ -z "$FILE" ] && exit 0

STANDARDS="$HOME/Documents/disk_docs/Book/Проекты"       # три стандарта в хранилище Obsidian
PLUGIN_SKILLS="$HOME/Projects/claude/armarium-linux-cli-plugin/skills"  # источник скиллов (плагин)

case "$FILE" in
  "$STANDARDS"/Стандарт*.md | "$PLUGIN_SKILLS"/*) ;;      # стандарты и скиллы плагина — идём дальше
  *) exit 0 ;;                                           # любой другой файл — молчим
esac

MSG="Изменён стандарт или скилл ($FILE). Напомни пользователю: 1) предложить прогнать скилл standards-audit (команда /armarium:audit); 2) обновить резервную копию в Book/Документация/Скиллы Claude (python3 -I ~/Projects/claude/armarium-linux-cli-plugin/tools/make_vault_copy.py). Не запускай сам без согласия пользователя."
jq -n --arg m "$MSG" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
