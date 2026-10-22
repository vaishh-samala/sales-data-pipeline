-- 1. View all loaded transactions
SELECT * FROM sales ORDER BY sale_date, transaction_id;

-- 2. Total revenue
SELECT ROUND(SUM(total_amount), 2) AS total_revenue FROM sales;

-- 3. Revenue and units sold per product
SELECT product, SUM(quantity) AS units_sold,
       ROUND(SUM(total_amount), 2) AS revenue
FROM sales GROUP BY product ORDER BY revenue DESC;

-- 4. Sales by day
SELECT sale_date, COUNT(*) AS transaction_count,
       ROUND(SUM(total_amount), 2) AS daily_revenue
FROM sales GROUP BY sale_date ORDER BY sale_date;

-- 5. Transactions above 100
SELECT transaction_id, product, total_amount
FROM sales WHERE total_amount > 100 ORDER BY total_amount DESC;

-- 6. Rejection reasons
SELECT reason, COUNT(*) AS rejected_count
FROM rejected_records GROUP BY reason ORDER BY rejected_count DESC;

-- 7. Monthly sales summary
SELECT substr(sale_date, 1, 7) AS sales_month,
       COUNT(*) AS transaction_count,
       ROUND(SUM(total_amount), 2) AS revenue
FROM sales GROUP BY substr(sale_date, 1, 7) ORDER BY sales_month;
