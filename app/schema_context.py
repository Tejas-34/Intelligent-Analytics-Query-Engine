import json
from app.data_loader import get_db


def get_table_schemas():
    db = get_db()
    tables = [r[0] for r in db.execute("SHOW TABLES;").fetchall()]
    lines = []
    for table in tables:
        cols = db.execute(f"PRAGMA table_info('{table}');").fetchall()
        col_desc = [f"  - {c[1]} ({c[2]})" for c in cols]
        lines.append(f"Table: {table}\n" + "\n".join(col_desc))
    return "\n\n".join(lines)


def build_system_context():
    with open("dataset/data_dictionary.json") as f:
        data_dict = json.load(f)

    with open("dataset/nl_queries.json") as f:
        sample_queries = json.load(f)

    table_schemas = get_table_schemas()
    metrics_str = json.dumps(data_dict.get("metrics", {}), indent=2)
    dimensions_str = json.dumps(data_dict.get("dimensions", []), indent=2)
    synonyms_str = json.dumps(data_dict.get("synonyms", {}), indent=2)
    time_mappings_str = json.dumps(data_dict.get("time_mappings", {}), indent=2)

    examples = []
    for ex in sample_queries[:4]:
        examples.append(
            f'- Query: "{ex["query"]}"\n  Target Logic: {ex["expected_logic"]}'
        )
    examples_str = "\n".join(examples)

    return f"""You are an expert DuckDB SQL analytics generator and data analyst.
Convert natural language business questions into accurate, executable DuckDB SQL, return the result, an explanation, and a confidence score (0.0 to 1.0).

=== DUCKDB SCHEMA ===
{table_schemas}

=== BUSINESS METRICS & SYNONYMS ===
CRITICAL: 'revenue' is NOT a column in sales_data. Use the formula:
  quantity * unit_price * (1 - discount)

Metrics:
{metrics_str}

Dimensions:
{dimensions_str}

Synonyms:
{synonyms_str}

Time Mappings:
{time_mappings_str}

=== TEMPORAL ANCHOR ===
Dataset transactions span Jan 2024 - Mar 2024. Anchor date is 2024-03-31:
- 'this month' or 'March' -> '2024-03'
- 'last month' -> '2024-02'
DuckDB date extraction: strftime(CAST(order_date AS DATE), '%Y-%m')

=== TARGETS JOIN ===
Join targets with sales_data on:
  targets.region = sales_data.region AND targets.month = strftime(CAST(sales_data.order_date AS DATE), '%Y-%m')

=== SAMPLE EXAMPLES ===
{examples_str}

=== OUTPUT FORMAT ===
Return ONLY a valid JSON object matching:
{{
  "sql": "SELECT ...",
  "explanation": "Plain-English explanation of derivation...",
  "confidence_score": 0.95
}}
"""
