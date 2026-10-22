import csv
import json
import math
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = ROOT / "data" / "sales.csv"
DEFAULT_DB = ROOT / "data" / "sales.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales (
    transaction_id TEXT PRIMARY KEY,
    sale_date TEXT NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total_amount REAL NOT NULL CHECK (total_amount >= 0)
);

CREATE TABLE IF NOT EXISTS rejected_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    source_row INTEGER NOT NULL,
    transaction_id TEXT,
    reason TEXT NOT NULL,
    raw_record TEXT NOT NULL
);
"""


def validate_record(row):
    """Return (clean_record, error). Invalid records are not loaded."""
    transaction_id = (row.get("transaction_id") or "").strip()
    sale_date = (row.get("sale_date") or "").strip()
    product = (row.get("product") or "").strip()
    quantity_text = (row.get("quantity") or "").strip()
    price_text = (row.get("unit_price") or "").strip()
    errors = []

    if not transaction_id:
        errors.append("Missing transaction_id")

    if not sale_date:
        errors.append("Missing sale_date")
    else:
        try:
            date.fromisoformat(sale_date)
        except ValueError:
            errors.append("Invalid sale_date; expected YYYY-MM-DD")

    if not product:
        errors.append("Missing product")

    try:
        quantity = int(quantity_text)
        if quantity <= 0:
            errors.append("Quantity must be positive")
    except ValueError:
        quantity = None
        errors.append("Quantity must be a whole number")

    try:
        unit_price = float(price_text)
        if not math.isfinite(unit_price) or unit_price < 0:
            errors.append("Unit price must be finite and non-negative")
    except ValueError:
        unit_price = None
        errors.append("Unit price must be numeric")

    if errors:
        return None, "; ".join(errors)

    clean = {
        "transaction_id": transaction_id,
        "sale_date": sale_date,
        "product": product,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": round(quantity * unit_price, 2),
    }
    return clean, None


def run_pipeline(csv_path=DEFAULT_CSV, db_path=DEFAULT_DB):
    """Read, validate, load and report on a CSV file."""
    csv_path = Path(csv_path)
    db_path = Path(db_path)

    if not csv_path.is_file():
        raise FileNotFoundError(f"Input CSV not found: {csv_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).isoformat()

    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        required = {
            "transaction_id", "sale_date", "product",
            "quantity", "unit_price"
        }
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV must contain these columns: {sorted(required)}"
            )
        input_rows = list(reader)

    accepted = []
    rejected = []
    for source_row, row in enumerate(input_rows, start=2):
        clean, error = validate_record(row)
        if error:
            rejected.append({
                "source_row": source_row,
                "transaction_id": row.get("transaction_id"),
                "reason": error,
                "raw_record": json.dumps(row),
            })
        else:
            accepted.append(clean)

    inserted = 0
    duplicates = 0
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)
        for record in accepted:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO sales
                (transaction_id, sale_date, product, quantity,
                 unit_price, total_amount)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record["transaction_id"], record["sale_date"],
                    record["product"], record["quantity"],
                    record["unit_price"], record["total_amount"],
                ),
            )
            if cursor.rowcount == 1:
                inserted += 1
            else:
                duplicates += 1

        conn.executemany(
            """
            INSERT INTO rejected_records
            (run_id, source_row, transaction_id, reason, raw_record)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (run_id, item["source_row"], item["transaction_id"],
                 item["reason"], item["raw_record"])
                for item in rejected
            ],
        )
        total_loaded = conn.execute(
            "SELECT COUNT(*) FROM sales"
        ).fetchone()[0]

    report = {
        "run_id": run_id,
        "input_rows": len(input_rows),
        "validated_rows": len(accepted),
        "inserted_rows": inserted,
        "duplicates_skipped": duplicates,
        "rejected_rows": len(rejected),
        "total_transactions_in_database": total_loaded,
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run_pipeline()
