from . import queries
import pandas as pd


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
    result = str(company["is_qualified"]) in ("True", "False") 

    cursor = conn.execute(
        queries.INSERT_ENRICHMENT_RUN,
        (company_id,result),
    )
    return cursor.fetchone()[0]


def insert_qualification_result(conn, company_id, enrichment_run_id, icp_score,is_qualified) -> None : 
    conn.execute(
        queries.INSERT_QUALIFICATION_RESULT,
        (company_id, enrichment_run_id, icp_score, is_qualified)
    )


def get_highest_icp_score(conn) -> list[int] : 
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_HIGHEST_ICP_SCORE)
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

def get_total_qualfication(conn) -> float : 
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_TOTAL_QUALIFICATION_RATE)
        return float(cursor.fetchone()[0])
    
def get_batch_qualification(conn) -> float : 
    with conn.cursor() as cursor:
        df = pd.read_csv("data/output/batch_results_most_recent.csv") 
        domains = df["domain"].tolist()
        cursor.execute(queries.GET_BATCH_QUALIFICATION_RATE, (domains,))
        return sum(1 for row in cursor.fetchall() if row[0])
        
    
def get_processed_this_week(conn) -> float : 
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_PROCESSED_THIS_WEEK)
        return cursor.fetchall()
    
    