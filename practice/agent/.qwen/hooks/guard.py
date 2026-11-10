#!/usr/bin/env python3
"""PreToolUse-hook: запрещает сеть из shell, а изменения задач всегда требуют подтверждения."""
import json
import re
import sys

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
args = data.get("tool_input", {})


def decide(decision: str, reason: str) -> None:
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,          # allow / deny / ask
        "permissionDecisionReason": reason,
    }}, ensure_ascii=False))
    sys.exit(0)


if tool == "run_shell_command":
    cmd = args.get("command", "")
    if re.search(r"\b(curl|wget|nc|ncat)\b|todo_db\.json", cmd):
        decide("deny", "Сетевые команды и прямой доступ к БД запрещены.")

if re.fullmatch(r"mcp__todo__(complete_task|delete_task)", tool):
    decide("ask", f"Изменение задач: {tool} {json.dumps(args, ensure_ascii=False)}")

decide("allow", "ok")  # обычные проверки и подтверждения Qwen остаются в силе