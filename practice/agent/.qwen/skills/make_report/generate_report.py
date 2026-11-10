#!/usr/bin/env python3
"""Создаёт Excel-отчёт по задачам TODO через локальный REST API."""
import argparse
import json
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font


def create_report(tasks, as_of, output):
    if len({task["id"] for task in tasks}) != len(tasks):
        raise ValueError("Обнаружены повторяющиеся ID задач")
    for task in tasks:
        if not all(key in task for key in ("id", "title", "priority", "due", "done")):
            raise ValueError("В задаче отсутствуют обязательные поля")
        if task["priority"] not in ("low", "normal", "high") or not isinstance(task["done"], bool):
            raise ValueError("Некорректный приоритет или статус")
        if task["due"] is not None:
            due = date.fromisoformat(task["due"])
            if due.isoformat() != task["due"]:
                raise ValueError("Срок должен быть в формате YYYY-MM-DD")

    tasks = sorted(tasks, key=lambda task: task["id"])
    total = len(tasks)
    done = sum(task["done"] for task in tasks)
    overdue = sum(not task["done"] and task["due"] is not None and task["due"] < as_of.isoformat()
                  for task in tasks)
    priorities = Counter(task["priority"] for task in tasks)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Задачи"
    sheet.append(["id", "название", "priority", "due", "done"])
    for task in tasks:
        title = task["title"]
        sheet.append([task["id"], title, task["priority"], task["due"], task["done"]])
        sheet.cell(sheet.max_row, 2).data_type = "s"
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in (("A", 10), ("B", 48), ("C", 14), ("D", 16), ("E", 12)):
        sheet.column_dimensions[column].width = width
    summary = workbook.create_sheet("Сводка")
    for row in (("Показатель", "Значение"), ("Дата отчёта", as_of.isoformat()),
                ("Всего", total), ("Выполнено", done), ("Не выполнено", total - done),
                ("Процент выполненных", round(done / total * 100, 2) if total else 0),
                ("Просрочено", overdue), ("low", priorities["low"]),
                ("normal", priorities["normal"]), ("high", priorities["high"])):
        summary.append(row)
    for s in (sheet, summary):
        for cell in s[1]:
            cell.font = Font(bold=True)
    summary.column_dimensions["A"].width = 25
    summary.column_dimensions["B"].width = 20
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as file:
        workbook.save(file)
    return {"total": total, "done": done, "overdue": overdue}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:5001")
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with urllib.request.urlopen(args.url.rstrip("/") + "/api/tasks", timeout=10) as response:
        tasks = json.load(response)
    if not isinstance(tasks, list):
        raise ValueError("API должен вернуть список задач")
    print(json.dumps(create_report(tasks, args.date, args.output), ensure_ascii=False))


if __name__ == "__main__":
    main()
