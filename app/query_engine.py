from app.data_loader import execute_query
from app.llm_client import build_prompt, call_gemini
from app.models import QueryResponse
from app.schema_context import build_system_context


def is_select_only(sql: str) -> bool:
    cleaned = (sql or "").strip()
    while cleaned.startswith("--") or cleaned.startswith("/*"):
        if cleaned.startswith("--"):
            cleaned = cleaned.split("\n", 1)[-1].strip()
        elif cleaned.startswith("/*") and "*/" in cleaned:
            cleaned = cleaned.split("*/", 1)[-1].strip()
        else:
            break

    tokens = cleaned.split()
    if not tokens:
        return False

    first_word = tokens[0].upper()
    if first_word == "SELECT":
        return True
    if first_word == "WITH":
        upper = cleaned.upper()
        disallowed = ("DELETE ", "UPDATE ", "INSERT ", "DROP ", "ALTER ", "TRUNCATE ", "CREATE ", "ATTACH ", "COPY ")
        return "SELECT" in upper and not any(verb in upper for verb in disallowed)
    return False


def process_query(query: str):
    system_context = build_system_context()
    prompt = build_prompt(query)
    try:
        data = call_gemini(prompt, system_context)
    except Exception as api_err:
        return QueryResponse(
            query=query,
            generated_logic="",
            result=None,
            confidence_score=0,
            explanation=f"LLM API Error: {api_err}",
        )

    sql = data.get("sql", "").strip()
    explanation = data.get("explanation", "")

    if not is_select_only(sql):
        return QueryResponse(
            query=query,
            generated_logic=sql,
            result=None,
            confidence_score=0,
            explanation="Query execution blocked: only read-only SELECT queries are permitted.",
        )

    try:
        result = execute_query(sql)
    except Exception as err:
        try:
            fix_prompt = build_prompt(query, failed_sql=sql, error_msg=str(err))
            fix_data = call_gemini(fix_prompt, system_context)
            sql = fix_data.get("sql", "").strip()
            explanation = fix_data.get("explanation", "")
            if not is_select_only(sql):
                return QueryResponse(
                    query=query,
                    generated_logic=sql,
                    result=None,
                    confidence_score=0,
                    explanation="Query execution blocked: only read-only SELECT queries are permitted.",
                )
            result = execute_query(sql)
        except Exception as retry_err:
            return QueryResponse(
                query=query,
                generated_logic=sql,
                result=None,
                confidence_score=0,
                explanation=f"Query execution failed: {retry_err}",
            )

    return QueryResponse(
        query=query,
        generated_logic=sql,
        result=result,
        confidence_score=1,
        explanation=explanation,
    )
