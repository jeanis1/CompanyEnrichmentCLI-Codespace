from . import queries
import math 

def insert_company(conn, row) -> int : 
    domain = row["domain"].strip().lower()
    cursor = conn.execute(
        queries.INSERT_COMPANY,
        (row["name"],
         domain,
         row["industry"],
        )
    )

    return cursor.fetchone()[0]


def insert_enrichment_run(conn, company_id:int, company: str) -> int :
    #Verifies enrichment (not icp score) 
    if company["is_qualified"] == "True" or company["is_qualified"] == "False": 
        result = "success"
    else:
        result = "fail"


    cursor = conn.execute(
        queries.INSERT_ENRICHMENT_RUN,
        (company_id,result,)
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

def get_total_industry_count(conn) -> list[int] :
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_ALL_INDUSTRY_COUNT)
        return cursor.fetchall()
    
def get_industry_count(conn, industry) -> list[str] :
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_THIS_INDUSTRY, (industry,))
        return cursor.fetchall()

def get_failed(conn) -> list[str] : 
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_FAILED)
        return cursor.fetchall()

def get_duplicate(conn) -> list[str] : 
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_DUPLICATE)
        return cursor.fetchall()
