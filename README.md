# Sales Data Pipeline

A beginner-friendly end-to-end data engineering project using Python, CSV, SQLite, and SQL.

## Overview

This project processes raw sales transactions from a CSV file, validates data quality, rejects invalid records, loads valid transactions into SQLite, and runs SQL queries for sales analysis.

## Architecture

CSV source -> Python ingestion -> Data validation and transformation -> SQLite database -> SQL analytics and quality reporting

## Tech Stack

- Python 3.10+
- SQLite
- SQL
- Python standard library (`csv`, `sqlite3`, `json`, `datetime`, `unittest`)
- Git and GitHub

## Features

- Validates transaction IDs, dates, products, quantities and prices.
- Calculates each transaction's total amount.
- Rejects invalid records with reasons.
- Prevents duplicate transaction IDs using a primary key.
- Supports reruns without duplicating existing sales.
- Produces a run summary with input, accepted, inserted, duplicate and rejected record counts.
- Includes automated tests.
- Provides SQL queries for revenue, product performance and daily/monthly sales.

## Project Structure

```text
sales-data-pipeline/
├── data/
│   └── sales.csv
├── src/
│   ├── __init__.py
│   ├── pipeline.py
│   └── queries.sql
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py
├── .gitignore
└── README.md
```

The SQLite database is generated locally when the pipeline runs.

## Requirements

- Python 3.10 or newer
- No external Python packages required

## Run the Pipeline

```bash
python3 -m src.pipeline
```

## Run Tests

```bash
python3 -m unittest discover -s tests -v
```

## Explore the Database

The database is created at `data/sales.db`. Example query:

```sql
SELECT product,
       SUM(quantity) AS units_sold,
       ROUND(SUM(total_amount), 2) AS revenue
FROM sales
GROUP BY product
ORDER BY revenue DESC;
```

## Sample Data Quality Results

For the supplied sample CSV:

- Input rows: 10
- Rows passing validation: 6
- New transactions inserted: 5
- Duplicate rows skipped: 1
- Invalid rows rejected: 4
- Total unique transactions loaded: 5
- Total sales amount: 2345.00

These figures describe the supplied sample dataset, not external business data.

## Design Decisions

- SQLite provides a lightweight relational database without requiring a separate database server.
- Python validation identifies data-quality problems before loading.
- A primary key prevents duplicate transaction IDs.
- Parameterized SQL separates values from SQL commands.
- Automated tests verify counts, revenue, invalid input and reruns.

## Limitations and Future Improvements

- Use structured logging and persistent per-run audit records.
- Add explicit conflict handling for duplicate transaction IDs.
- Make rejected-record audit writes and data loading atomic.
- Use decimal-safe monetary calculations and an explicit currency.
- Add batch processing for large files.
- Add configurable schemas and stronger data-quality rules.
- Add scheduling, monitoring and alerting.
- Deploy to cloud storage and a managed database if required.

## Learning Outcomes

This project demonstrates the fundamentals of data ingestion, transformation, validation, relational storage, SQL analytics, idempotency and automated testing.
