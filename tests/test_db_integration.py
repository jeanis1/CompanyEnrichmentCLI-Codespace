import psycopg
import pytest

from clients.apollo_api import ApolloAPIError
from database import repository
from services.company_processing import process_company

def count(conn, table):
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_success_writes_company_run_and_score(conn, apollo_payload):
    process_company(conn, "http://www.OpenAI.com", lambda d: apollo_payload)
    assert conn.execute(
        "SELECT status, requested_domain FROM enrichment_runs"
    ).fetchone() == ("succeeded", "openai.com")
    assert count(conn, "companies") == 1
    assert count(conn, "qualification_results") == 1


def test_rerun_does_not_duplicate_company(conn, apollo_payload):
    process_company(conn, "openai.com", lambda d: apollo_payload)
    process_company(conn, "openai.com", lambda d: apollo_payload)
    assert count(conn, "companies") == 1
    assert count(conn, "enrichment_runs") == 2


def test_provider_failure_is_recorded(conn):
    def fail(_):
        raise ApolloAPIError("down", code="server_error")

    with pytest.raises(ApolloAPIError):
        process_company(conn, "openai.com", fail)

    assert conn.execute(
        "SELECT status, error_code FROM enrichment_runs"
    ).fetchone() == (
        "failed", "provider_server_error")
    assert count(conn, "companies") == 0


def test_db_failure_rolls_back_company_and_marks_run_failed(
    conn, apollo_payload, monkeypatch
):
    def boom(*args, **kwargs):
        raise psycopg.errors.CheckViolation("forced")

    monkeypatch.setattr(repository, "insert_qualification_result", boom)

    with pytest.raises(psycopg.IntegrityError):
        process_company(conn, "openai.com", lambda d: apollo_payload)

    assert count(conn, "companies") == 0  # real rollback
    assert conn.execute(
        "SELECT status, error_code FROM enrichment_runs"
    ).fetchone() == ("failed", "database_constraint")


def test_stale_runs_are_failed(conn):
    conn.execute(
        "INSERT INTO enrichment_runs(requested_domain,status, started_at)"
        "VALUES ('openai.com', 'running', NOW() - INTERVAL '1 hour')"
    )
    repository.start_enrichment_run(conn, "stripe.com")  # recent : must stay running

    assert repository.fail_stale_runs(conn) == 1
    rows = conn.execute(
        "SELECT requested_domain, status, error_code FROM enrichment_runs ORDER BY id"
    ).fetchall()
    assert rows == [
        ("openai.com", "failed", "interrupted"),
        ("stripe.com", "running", None),
    ]

def test_invalid_domain_creates_no_run(conn):
    with pytest.raises(ValueError):
        process_company(conn, "not a domain", lambda d: {})
    assert count(conn, "enrichment_runs") == 0