import json
import os
from google import genai
from google.genai import types


def build_prompt(query, failed_sql=None, error_msg=None):
    if failed_sql and error_msg:
        return f"""USER QUERY: "{query}"

PREVIOUS SQL THAT FAILED:
{failed_sql}

DUCKDB ERROR:
{error_msg}

Fix the SQL query to resolve the DuckDB error, provide an updated explanation, and return the JSON response."""
    return f'USER QUERY: "{query}"\nGenerate the structured JSON response containing "sql", "explanation", and "confidence_score".'


def call_gemini(prompt, system_context):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not found in environment.")

    client = genai.Client(api_key=api_key)
    model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    full_content = f"{system_context}\n\n=== REQUEST ===\n{prompt}"
    response = client.models.generate_content(
        model=model,
        contents=full_content,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
        ),
    )

    text = (response.text or "{}").strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())
