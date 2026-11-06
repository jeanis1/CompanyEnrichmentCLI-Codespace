# Batch-loop control flow with process company faked (no DB or network)
import psycopg
import pytest
import main

from clients.apollo_api import ApolloAPIError
from services import persistence

def make_batch(n):
    return [
        {
            "domain": f"site{i}.com",
            "status": None,
            "icp_score": None,
            "qualification": None,
            "error_type": None,
        }
        for i in range(n)
    ]


@pytest.fixture
def no_files(monkeypatch):
    monkeypatch.setattr(main, "save_output_files", lambda *args: None)


def run(monkeypatch, batch, fake, max_calls=100):
    monkeypatch.setattr(main, "process_company", fake)
    return main.enrich_batch(None, batch, None, None, max_calls)


def raises(exc):
    def fake(conn, domain, fetch):
        raise exc

    return fake


def statuses(batch): # Reduce batch to list tuple for easy comparison
    return [(e["status"], e["error_type"]) for e in batch]


def test_circuit_breaker_stops_after_consecutive_transient_failures(
    monkeypatch, no_files
):
    batch = run(
        monkeypatch, make_batch(7), raises(ApolloAPIError("x", code="server_error"))
    )
    assert (
        statuses(batch)
        == [("FAIL", "server_error")] * 5 + [("SKIPPED", "batch_stopped_transient_provider_error")] * 2
    )


def test_auth_error_stops_immediately(monkeypatch, no_files):
    batch = run(monkeypatch, make_batch(3), raises(ApolloAPIError("x", code="auth")))
    assert statuses(batch) == [("FAIL", "auth")] + [("SKIPPED", "batch_stopped_auth_error")] * 2


def test_database_unavailable_stops_batch(monkeypatch, no_files):
    batch = run(monkeypatch, make_batch(2), raises(psycopg.OperationalError()))
    assert statuses(batch) == [
        ("FAIL", "database_unavailable"),
        ("SKIPPED", "batch_stopped_db_unavailable"),
    ]


def test_not_found_does_not_trip_breaker(monkeypatch, no_files):
    batch = run(
        monkeypatch, make_batch(7), raises(ApolloAPIError("x", code="not_found"))
    )
    assert statuses(batch) == [("FAIL", "not_found")] * 7


def test_max_calls_skips_the_rest(
    monkeypatch, no_files, qualified_company, qualified_score
):
    calls = []

    def ok(conn, domain, fetch):
        calls.append(domain)
        return qualified_company, qualified_score

    batch = make_batch(4)
    batch[0].update(
        status="FAIL", error_type="Invalid Domain"
    )  # pre-failed rows don't count
    batch = run(monkeypatch, batch, ok, max_calls=2)

    assert len(calls) == 2
    assert statuses(batch) == [
        ("FAIL", "Invalid Domain"),
        ("SUCCESS", None),
        ("SUCCESS", None),
        ("SKIPPED", "max_calls_reached"),
    ]


def test_file_write_failure_keeps_success(
    monkeypatch, qualified_company, qualified_score
):
    def broken_write(*args, **kwargs):
        raise PermissionError("read-only")

    monkeypatch.setattr(persistence, "save_results_json", broken_write)
    batch = run(
        monkeypatch, make_batch(1), lambda c, d, f: (qualified_company, qualified_score)
    )
    assert statuses(batch) == [("SUCCESS", None)]

