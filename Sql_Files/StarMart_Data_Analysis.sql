-- Monthly Revenue 
SELECT 
  DATE_TRUNC('month', order_datetime) AS MONTH,
  SUM(final_price) AS Total_Sales
FROM starmart_orders
GROUP BY MONTH
ORDER BY MONTH;

-- Monthly Expenses
-- Employee 
SELECT 
  emp_id,
  hourly_rate,
  ROUND(hourly_rate * 8 * 365 / 12, 2) AS monthly_salary_estimate
FROM starmart_employees;

-- Restcok Expenses Per Month
SELECT 
    DATE_TRUNC('month', rsl.restock_date) AS MONTH,
    SUM(rsl.restock_quantity * v.per_item_cost) AS total_restock_cost
FROM starmart_restock_log rsl
INNER JOIN starmart_vendors v
    ON rsl.vendor_unique_id = v.vendor_unique_id
GROUP BY MONTH
ORDER BY MONTH;

