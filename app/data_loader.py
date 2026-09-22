import duckdb

con = None


def init_db():
    global con
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE sales_data AS SELECT * FROM read_csv_auto('dataset/sales_data.csv');")
    con.execute("CREATE TABLE targets AS SELECT * FROM read_csv_auto('dataset/targets.csv');")
    return con


def get_db():
    global con
    if con is None:
        init_db()
    return con


def execute_query(sql):
    db = get_db()
    cursor = db.execute(sql)
    if cursor.description is None:
        return []
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]
