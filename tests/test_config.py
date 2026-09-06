import pytest

import config 
from config import Settings

def test_missing_api_key_raises_error(
        monkeypatch, 
):
    monkeypatch.setattr(
        config, 
        "load_dotenv",
        lambda: None,
    )

    monkeypatch.delenv(
        "ABSTRACT_API_KEY",
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="ABSTRACT_API_KEY is not configured.",
    ):
        Settings.from_env()