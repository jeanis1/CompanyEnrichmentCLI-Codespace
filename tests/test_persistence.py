import csv 
import json

from services import persistence

def test_save_results_json(
        tmp_path,
        qualified_company,
        qualified_score
):

    persistence.save_results_json(
        qualified_company,
        qualified_score,
        filename="test.json",
        output_dir=tmp_path,
    )

    path = tmp_path / "test.json"

    assert path.exists()

    with path.open(encoding="utf-8") as file: 
        data = json.load(file)

    assert data["company"]["name"] == "OpenAI"
    assert data["company"]["domain"] == "openai.com"
    assert data["icp_score"]["score"] == 100
    assert data["icp_score"]["is_qualified"] is True

def test_save_results_csv(
        tmp_path,
        qualified_company,
        qualified_score,
):
    persistence.save_results_csv(
        qualified_company, 
        qualified_score,
        filename="test.csv",
        output_dir=tmp_path,
    )

    path = tmp_path / "test.csv"

    assert path.exists()

    with path.open(encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1

    row = rows[0]

    assert row["name"] == "OpenAI"
    assert row["domain"] == "openai.com"
    assert row["country"] == "United States"
    assert row["icp_score"] == "100"

