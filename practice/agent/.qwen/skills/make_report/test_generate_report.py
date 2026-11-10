import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("report", HERE / "generate_report.py")
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTest(unittest.TestCase):
    def test_metrics_boundaries_and_formulas(self):
        tasks = [
            {"id": 2, "title": "=1+1", "priority": "high", "due": "2026-11-09", "done": False},
            {"id": 1, "title": "готово", "priority": "low", "due": "2026-11-01", "done": True},
            {"id": 3, "title": "сегодня", "priority": "normal", "due": "2026-11-10", "done": False},
            {"id": 4, "title": "без срока", "priority": "low", "due": None, "done": False},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.xlsx"
            self.assertEqual(report.create_report(tasks, date(2026, 11, 10), path),
                             {"total": 4, "done": 1, "overdue": 1})
            workbook = load_workbook(path, data_only=False)
            self.assertEqual(workbook.sheetnames, ["Задачи", "Сводка"])
            self.assertEqual([row[0] for row in list(workbook["Задачи"].values)[1:]], [1, 2, 3, 4])
            self.assertEqual(workbook["Задачи"]["B3"].data_type, "s")
            summary = dict(list(workbook["Сводка"].values)[1:])
            self.assertEqual(summary["Процент выполненных"], 25)
            self.assertEqual((summary["low"], summary["normal"], summary["high"]), (2, 1, 1))
            with self.assertRaises(FileExistsError):
                report.create_report(tasks, date.today(), path)

    def test_empty_and_invalid(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.xlsx"
            report.create_report([], date.today(), path)
            self.assertEqual(dict(list(load_workbook(path)["Сводка"].values)[1:])["Процент выполненных"], 0)
            invalid = {"id": 1, "title": "x", "priority": "bad", "due": None, "done": False}
            with self.assertRaises(ValueError):
                report.create_report([invalid], date.today(), Path(directory) / "invalid.xlsx")
            valid = {**invalid, "priority": "low"}
            with self.assertRaises(ValueError):
                report.create_report([valid, valid], date.today(), Path(directory) / "duplicate.xlsx")


if __name__ == "__main__":
    unittest.main()
