import csv
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.pipeline import run_pipeline, validate_record

SAMPLE_ROWS = [
    {"transaction_id": "TXN1001", "sale_date": "2026-10-01", "product": "Laptop", "quantity": "2", "unit_price": "750.00"},
    {"transaction_id": "TXN1002", "sale_date": "2026-10-02", "product": "Mouse", "quantity": "5", "unit_price": "20.00"},
    {"transaction_id": "TXN1003", "sale_date": "2026-10-02", "product": "Keyboard", "quantity": "3", "unit_price": "45.00"},
    {"transaction_id": "TXN1004", "sale_date": "2026-10-03", "product": "Monitor", "quantity": "2", "unit_price": "180.00"},
    {"transaction_id": "TXN1002", "sale_date": "2026-10-02", "product": "Mouse", "quantity": "5", "unit_price": "20.00"},
    {"transaction_id": "TXN1005", "sale_date": "2026-10-04", "product": "", "quantity": "2", "unit_price": "30.00"},
    {"transaction_id": "TXN1006", "sale_date": "2026-10-04", "product": "Headphones", "quantity": "0", "unit_price": "60.00"},
    {"transaction_id": "TXN1007", "sale_date": "2026-13-04", "product": "Webcam", "quantity": "1", "unit_price": "40.00"},
    {"transaction_id": "TXN1008", "sale_date": "2026-10-05", "product": "USB Hub", "quantity": "2", "unit_price": "-5.00"},
    {"transaction_id": "TXN1009", "sale_date": "2026-10-06", "product": "Desk", "quantity": "1", "unit_price": "250.00"},
]


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.csv_path = self.root / "sales.csv"
        self.db_path = self.root / "sales.db"
        with self.csv_path.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=list(SAMPLE_ROWS[0].keys()))
            writer.writeheader()
            writer.writerows(SAMPLE_ROWS)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_validation_calculates_total(self):
        clean, error = validate_record(SAMPLE_ROWS[0])
        self.assertIsNone(error)
        self.assertEqual(clean["total_amount"], 1500.00)

    def test_missing_product_is_rejected(self):
        clean, error = validate_record(SAMPLE_ROWS[5])
        self.assertIsNone(clean)
        self.assertIn("Missing product", error)

    def test_pipeline_counts_and_revenue(self):
        report = run_pipeline(self.csv_path, self.db_path)
        self.assertEqual(report["input_rows"], 10)
        self.assertEqual(report["validated_rows"], 6)
        self.assertEqual(report["inserted_rows"], 5)
        self.assertEqual(report["duplicates_skipped"], 1)
        self.assertEqual(report["rejected_rows"], 4)
        self.assertEqual(report["total_transactions_in_database"], 5)
        with sqlite3.connect(self.db_path) as conn:
            revenue = conn.execute("SELECT SUM(total_amount) FROM sales").fetchone()[0]
        self.assertAlmostEqual(revenue, 2345.00)

    def test_rerun_does_not_duplicate_sales(self):
        run_pipeline(self.csv_path, self.db_path)
        report = run_pipeline(self.csv_path, self.db_path)
        self.assertEqual(report["inserted_rows"], 0)
        self.assertEqual(report["duplicates_skipped"], 6)
        self.assertEqual(report["total_transactions_in_database"], 5)

    def test_missing_file_fails_clearly(self):
        with self.assertRaises(FileNotFoundError):
            run_pipeline(self.root / "does_not_exist.csv", self.db_path)

    def test_missing_required_column_fails(self):
        bad_csv = self.root / "bad.csv"
        bad_csv.write_text("transaction_id,product\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            run_pipeline(bad_csv, self.root / "bad.db")


if __name__ == "__main__":
    unittest.main()
