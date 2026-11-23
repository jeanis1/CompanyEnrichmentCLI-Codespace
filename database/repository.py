from . import queries
import pandas as pd


def insert_company(conn, row) -> int:
    domain = row["domain"]
    cursor = conn.execute(
        queries.INSERT_COMPANY,
        (
            row["name"],
            domain,
            row["industry"],
        ),
    )

    return cursor.fetchone()[0]


def insert_qualification_result(
    conn, company_id, enrichment_run_id, icp_score, is_qualified
) -> None:
    conn.execute(
        queries.INSERT_QUALIFICATION_RESULT,
        (company_id, enrichment_run_id, icp_score, is_qualified),
    )


def get_highest_icp_score(conn) -> list[int]:
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_HIGHEST_ICP_SCORE)
        return cursor.fetchall()


def get_total_industry_count(conn) -> list[int]:
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_ALL_INDUSTRY_COUNT)
        return cursor.fetchall()


def get_industry_count(conn, industry) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_THIS_INDUSTRY, (industry,))
        return cursor.fetchall()


def get_duplicate(conn) -> list[str]:
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_DUPLICATE)
        return cursor.fetchall()


def get_total_qualfication(conn) -> float:
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_TOTAL_QUALIFICATION_RATE)
        return float(cursor.fetchone()[0])


def get_batch_qualification(conn) -> float:
    with conn.cursor() as cursor:
        df = pd.read_csv("data/output/batch_results_most_recent.csv")
        domains = df["domain"].tolist()
        cursor.execute(queries.GET_BATCH_QUALIFICATION_RATE, (domains,))
        return sum(1 for row in cursor.fetchall() if row[0])


def get_processed_this_week(conn) -> float:
    with conn.cursor() as cursor:
        cursor.execute(queries.GET_PROCESSED_THIS_WEEK)
        return cursor.fetchall()


def start_enrichment_run(conn, domain: str) -> int:
    cursor = conn.execute(
        """
        INSERT INTO enrichment_runs(
            requested_domain,
            status
        )
        VALUES (%s, 'running')
        RETURNING id
        """,
        (domain,),
    )
    return cursor.fetchone()[0]


def complete_enrichment_run(
    conn,
    run_id: int,
    company_id: int,
    is_qualified: bool,
) -> None:
    cursor = conn.execute(
        """
        UPDATE enrichment_runs
        SET company_id = %s,
            status = 'succeeded',
            result = %s,
            finished_at = NOW(),
            error_code = NULL
        WHERE id = %s
            AND status = 'running'
        RETURNING id
        """,
        (company_id, is_qualified, run_id),
    )

    if cursor.fetchone() is None:
        raise ValueError("Run does not exist or is no longer running.")


def fail_enrichment_run(
    conn,
    run_id: int,
    error_code: str,
) -> None:
    cursor = conn.execute(
        """
        UPDATE enrichment_runs
        SET status = 'failed',
            result = NULL,
            error_code = %s,
            finished_at = NOW()
        WHERE id = %s 
            AND status = 'running'
        RETURNING id
        """,
        (error_code, run_id),
    )

    if cursor.fetchone() is None:
        raise ValueError("Run does not exist or is no longer running")


def get_failed_runs(conn):
    return conn.execute(queries.GET_FAILED_RUNS).fetchall()


def get_potentially_interrupted_runs(conn, minutes=15):
    return conn.execute(
        queries.GET_POTENTIALLY_INTERRUPTED_RUNS,
        (minutes,),
    ).fetchall()


def fail_stale_runs(conn, minutes: int = 15) -> int:
    # Mark runs left in 'running' by a crash or lost connection as failed
    cursor = conn.execute(
        """
        UPDATE enrichment_runs
        SET status = 'failed', error_code = 'interrupted', finished_at = NOW()
        WHERE status = 'running'
            AND started_at < NOW() - make_interval(mins => %s)
        """,
        (minutes,),
    )
    return cursor.rowcount


def get_recently_enriched(conn, domains: list[str], days: int = 30) -> set[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT requested_domain FROM enrichment_runs
        WHERE status = 'succeeded'
            AND requested_domain = ANY(%s)
            AND finished_at > NOW() - make_interval(days => %s)
        """,
        (domains, days),
    ).fetchall()
    return {row[0] for row in rows}


def get_company_icp_score(conn, domain: str) -> int | None:
    row = conn.execute(queries.GET_COMPANY_ICP_SCORE, (domain,)).fetchone()
    return row[0] if row else None


def get_company_qualification_result(conn, domain: str) -> bool | None:
    row = conn.execute(queries.GET_COMPANY_QUALIFICATION_RESULT, (domain,)).fetchone()
    return row[0] if row else None
