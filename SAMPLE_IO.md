# Sample Inputs and Outputs: Intelligent Analytics Query Engine

This document provides representative sample queries along with the exact JSON request payloads and API responses produced by the engine across various analytical and security scenarios.

---

## 1. Aggregation with Metric Formula Derivation

**Natural Language Query**: `"Total sales in India for March"`

The engine detects that `revenue` is a derived business metric (`quantity * unit_price * (1 - discount)`), filters by country and order date, and returns the net sales amount.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Total sales in India for March"
}
```

### Response
```json
{
  "query": "Total sales in India for March",
  "generated_logic": "SELECT SUM(quantity * unit_price * (1 - discount)) AS total_sales FROM sales_data WHERE country = 'India' AND strftime('%Y-%m', CAST(order_date AS DATE)) = '2024-03';",
  "result": [
    {
      "total_sales": 108.0
    }
  ],
  "confidence_score": 1,
  "explanation": "Calculated total net revenue for orders placed in India during March 2024 using the formula: quantity * unit_price * (1 - discount)."
}
```

---

## 2. Grouping, Ordering & Limit

**Natural Language Query**: `"Top 2 cities by profit"`

The engine groups transactions by city, aggregates total profit, sorts in descending order, and limits to the top 2 cities.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Top 2 cities by profit"
}
```

### Response
```json
{
  "query": "Top 2 cities by profit",
  "generated_logic": "SELECT city, SUM(profit) AS total_profit FROM sales_data GROUP BY city ORDER BY total_profit DESC LIMIT 2;",
  "result": [
    {
      "city": "New York",
      "total_profit": 200
    },
    {
      "city": "San Francisco",
      "total_profit": 180
    }
  ],
  "confidence_score": 1,
  "explanation": "Calculates the total profit for each city by aggregating the 'profit' column, sorts the results in descending order to identify the highest earning cities, and returns the top 2."
}
```

---

## 3. Multi-Table Join against Targets

**Natural Language Query**: `"Which region missed its target in Feb?"`

The engine calculates actual revenue by region for February 2024, joins against the `targets` table on `region` and `month`, and filters for regions where actual revenue fell short of `target_revenue`.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Which region missed its target in Feb?"
}
```

### Response
```json
{
  "query": "Which region missed its target in Feb?",
  "generated_logic": "WITH monthly_sales AS (\n    SELECT region, SUM(quantity * unit_price * (1 - discount)) AS actual_revenue\n    FROM sales_data\n    WHERE strftime('%Y-%m', CAST(order_date AS DATE)) = '2024-02'\n    GROUP BY region\n)\nSELECT t.region, t.target_revenue, COALESCE(s.actual_revenue, 0) AS actual_revenue\nFROM targets t\nLEFT JOIN monthly_sales s ON t.region = s.region\nWHERE t.month = '2024-02' AND COALESCE(s.actual_revenue, 0) < t.target_revenue;",
  "result": [
    {
      "region": "APAC",
      "target_revenue": 6000,
      "actual_revenue": 0.0
    },
    {
      "region": "EMEA",
      "target_revenue": 7500,
      "actual_revenue": 0.0
    },
    {
      "region": "NA",
      "target_revenue": 9500,
      "actual_revenue": 2125.8
    }
  ],
  "confidence_score": 1,
  "explanation": "Joined regional sales revenue for February 2024 against monthly revenue targets to identify all regions where actual revenue was less than the target."
}
```

---

## 4. Complex Window Function & Partitioning

**Natural Language Query**: `"Top product in each region"`

The engine aggregates total revenue by region and product, uses the DuckDB window ranking function `RANK() OVER (PARTITION BY region ORDER BY SUM(revenue) DESC)`, and filters for rank 1.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Top product in each region"
}
```

### Response
```json
{
  "query": "Top product in each region",
  "generated_logic": "WITH ranked_products AS (\n    SELECT region, product_name, SUM(quantity * unit_price * (1 - discount)) AS revenue,\n           RANK() OVER (PARTITION BY region ORDER BY SUM(quantity * unit_price * (1 - discount)) DESC) AS rnk\n    FROM sales_data\n    GROUP BY region, product_name\n)\nSELECT region, product_name, revenue\nFROM ranked_products\nWHERE rnk = 1;",
  "result": [
    {
      "region": "APAC",
      "product_name": "Ergo Chair",
      "revenue": 216.0
    },
    {
      "region": "EMEA",
      "product_name": "iPhone 14",
      "revenue": 855.0
    },
    {
      "region": "NA",
      "product_name": "MacBook Air",
      "revenue": 1116.0
    }
  ],
  "confidence_score": 1,
  "explanation": "Partitioned transactions by region to identify the top revenue-generating product in each geographic territory using window ranking functions."
}
```

---

## 5. Read-Only Safety Guard: Data Modification Blocked

**Natural Language Query**: `"Delete all orders from Mumbai"`

The engine detects a data modification query (`DELETE`). It **blocks execution entirely**, ensures DuckDB tables are **never touched**, preserves the generated logic for inspection, and assigns `confidence_score = 0`.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Delete all orders from Mumbai"
}
```

### Response
```json
{
  "query": "Delete all orders from Mumbai",
  "generated_logic": "DELETE FROM sales_data WHERE city = 'Mumbai';",
  "result": null,
  "confidence_score": 0,
  "explanation": "Query execution blocked: only read-only SELECT queries are permitted."
}
```

---

## 6. Read-Only Safety Guard: DDL Operation Blocked

**Natural Language Query**: `"Drop the sales_data table"`

The engine intercepts the DDL keyword (`DROP`), halts execution immediately, keeps tables intact, and returns a binary 0 confidence score.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Drop the sales_data table"
}
```

### Response
```json
{
  "query": "Drop the sales_data table",
  "generated_logic": "DROP TABLE sales_data;",
  "result": null,
  "confidence_score": 0,
  "explanation": "Query execution blocked: only read-only SELECT queries are permitted."
}
```

---

## 7. Zero Matching Records (Empty Result Set)

**Natural Language Query**: `"Total sales in Antarctica for March"`

The query is a valid read-only `SELECT` query that executes without errors, but matches no rows. Because the operation is safe and successful, `confidence_score = 1`.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Total sales in Antarctica for March"
}
```

### Response
```json
{
  "query": "Total sales in Antarctica for March",
  "generated_logic": "SELECT SUM(quantity * unit_price * (1 - discount)) AS total_sales FROM sales_data WHERE country = 'Antarctica' AND strftime('%Y-%m', CAST(order_date AS DATE)) = '2024-03';",
  "result": [
    {
      "total_sales": null
    }
  ],
  "confidence_score": 1,
  "explanation": "Calculated total sales in Antarctica for March 2024. Query executed successfully, returning null as no orders matched the specified country filter."
}
```

---

## 8. Automatic 1-Shot Retry Recovery

**Scenario**: Initial SQL generation produced a column syntax error; the engine automatically re-prompted Gemini with the exact database error diagnostic to produce corrected SQL.

### Request
```http
POST /query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "Show average customer spend"
}
```

### Response
```json
{
  "query": "Show average customer spend",
  "generated_logic": "SELECT customer_id, AVG(quantity * unit_price * (1 - discount)) AS avg_spend FROM sales_data GROUP BY customer_id;",
  "result": [
    {
      "customer_id": "C001",
      "avg_spend": 216.0
    },
    {
      "customer_id": "C002",
      "avg_spend": 855.0
    },
    {
      "customer_id": "C003",
      "avg_spend": 75.0
    }
  ],
  "confidence_score": 1,
  "explanation": "Calculated average net spend per customer across all orders (automatically corrected after initial syntax retry)."
}
```
