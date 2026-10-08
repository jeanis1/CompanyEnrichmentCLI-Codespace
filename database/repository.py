from . import queries

def insert_company(conn, company) -> int : 
    cursor = conn.execute(
        queries.INSERT_COMPANY,
        (company["name"],
         company["domain"],
         company["industry"],
        )
    )

    return cursor.fetchone()[0]


def insert_enrichment_run(conn, company) -> int : 
    if company["is_qualified"] is not None: 
        result = "success"
    else:
        result = "fail"

    cursor = conn.execute(
        queries.INSERT_ENRICHMENT_RUN,
        (result,)
    )
    return cursor.fetchone()[0]


def insert_qualification_result(conn, company_id, enrichment_run_id, icp_score) -> None : 
    conn.execute(
        queries.INSERT_QUALIFICATION_RESULT,
        (company_id, enrichment_run_id, icp_score)
    )


def get_highest_icp_score(conn) -> list[int] : 
    with conn.cursor() as cursor:
        cursor.execute(queries.HIGHEST_ICP_SCORE)
        return cursor.fetchall()


def get_table(conn, table) -> list[dict]:
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

def get_industry_count(conn) -> list[int] :
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_INDUSTRY_COUNT)
        return cursor.fetchall()
    

   