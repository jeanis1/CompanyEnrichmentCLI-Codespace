from services.company_processing import process_company


def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

def test_success_writes_company_run_and_score(conn, apollo_payload):
    process_company(conn, "openai.com", lambda d:apollo_payload)
    assert conn.execute("SELECT status, requested_domain FROM enrichment_runs").fetchone() \
        == ("succeeded", "openai.com")
    assert count(conn, "companies") == 1
    assert count(conn, "qualification_results") == 1

def test_rerun_does_not_duplicate_company(conn, apollo_payload): 
    process_company(conn, "openai.com", lambda d: apollo_payload)
    process_company(conn, "openai.com", lambda d: apollo_payload)
    assert count(conn, "companies") == 1 
    assert count(conn, "enrichment_runs") == 2