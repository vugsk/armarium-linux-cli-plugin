#!/usr/bin/env python3
"""Переходный помощник: переносит в плагин armarium правки, сделанные в ~/.claude/skills.

Зачем: пока плагин не включён, Claude Code читает скиллы из ~/.claude/skills, и правки идут туда.
Источник истины — плагин, поэтому после правки в ~/.claude/skills запусти этот скрипт: он
перезаписывает папки скиллов плагина содержимым ~/.claude/skills (без служебной папки synced).
Когда плагин включён, а ~/.claude/skills очищена от этих скиллов, скрипт больше не нужен.

Использование:
    python3 -I import_user_skills.py
"""
import shutil
from pathlib import Path

SRC = Path.home() / ".claude" / "skills"                # прежнее место скиллов
DST = Path(__file__).resolve().parent.parent / "skills"  # папка skills плагина

copied = 0
for d in sorted(SRC.iterdir()):
    # берём только папки со SKILL.md; synced (скиллы claude.ai) пропускаем
    if not d.is_dir() or d.name == "synced" or not (d / "SKILL.md").exists():
        continue
    target = DST / d.name
    if target.exists():
        shutil.rmtree(target)      # заменяем целиком, чтобы удалённые файлы не оставались
    shutil.copytree(d, target)
    copied += 1
print(f"Скиллов перенесено в плагин: {copied}")
