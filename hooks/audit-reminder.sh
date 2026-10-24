#!/usr/bin/env bash
# Хук PostToolUse (Edit|Write) плагина armarium: напоминание после правки стандартов и скиллов.
# Читает JSON со стандартного ввода и берёт путь изменённого файла.
# Если файл — один из стандартов, файл внутри папки скиллов плагина или внутри ~/.claude/skills
# (кроме synced — это скиллы с claude.ai), выводит JSON, по которому Claude получает напоминание.
# Во всех остальных случаях молчит и ничего не делает.

FILE=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty')
[ -z "$FILE" ] && exit 0

STANDARDS="$HOME/Documents/disk_docs/Book/Проекты"       # три стандарта в хранилище Obsidian
PLUGIN_SKILLS="$HOME/Projects/claude/armarium-linux-cli-plugin/skills"  # источник скиллов (плагин)
USER_SKILLS="$HOME/.claude/skills"                       # прежнее место скиллов (пока плагин не включён)

case "$FILE" in
  "$USER_SKILLS/synced/"*) exit 0 ;;                     # скиллы claude.ai не трогаем
  "$STANDARDS"/Стандарт*.md | "$PLUGIN_SKILLS"/* | "$USER_SKILLS"/*) ;;  # нужные файлы — идём дальше
  *) exit 0 ;;                                           # любой другой файл — молчим
esac

MSG="Изменён стандарт или скилл ($FILE). Напомни пользователю: 1) предложить прогнать скилл standards-audit (команда /armarium:audit); 2) обновить резервную копию в Book/Документация/Скиллы Claude (python3 -I ~/Projects/claude/armarium-linux-cli-plugin/tools/make_vault_copy.py). Если правка была в ~/.claude/skills, а не в плагине, сначала python3 -I ~/Projects/claude/armarium-linux-cli-plugin/tools/import_user_skills.py. Не запускай сам без согласия пользователя."
jq -n --arg m "$MSG" '{hookSpecificOutput:{hookEventName:"PostToolUse",additionalContext:$m}}'
