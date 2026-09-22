from app.data_loader import execute_query
from app.llm_client import build_prompt, call_gemini
from app.models import QueryResponse
from app.schema_context import build_system_context


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
            confidence_score=0.0,
            explanation=f"LLM API Error: {api_err}",
        )

    sql = data.get("sql", "")
    explanation = data.get("explanation", "")
    score = float(data.get("confidence_score", 0.8))
    retried = False

    try:
        result = execute_query(sql)
    except Exception as err:
        retried = True
        try:
            fix_prompt = build_prompt(query, failed_sql=sql, error_msg=str(err))
            fix_data = call_gemini(fix_prompt, system_context)
            sql = fix_data.get("sql", "")
            explanation = fix_data.get("explanation", "")
            score = float(fix_data.get("confidence_score", 0.8))
            result = execute_query(sql)
        except Exception as retry_err:
            return QueryResponse(
                query=query,
                generated_logic=sql,
                result=None,
                confidence_score=0.0,
                explanation=f"Query execution failed: {retry_err}",
            )

    if retried:
        score = round(score * 0.8, 2)
        explanation += " (Automatically corrected after syntax retry)."
    elif isinstance(result, list) and len(result) == 0:
        score = min(score, 0.3)
        explanation += " (Executed successfully, but matched zero records)."

    return QueryResponse(
        query=query,
        generated_logic=sql,
        result=result,
        confidence_score=round(score, 2),
        explanation=explanation,
    )
