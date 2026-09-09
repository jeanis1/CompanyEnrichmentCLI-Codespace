from unittest.mock import Mock

import pytest
import requests

from clients import abstract_api
from clients.abstract_api import AbstractAPIError

def test_successful_request(monkeypatch):
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "name": "OpenAI",
        "domain": "openai.com",
    }

    monkeypatch.setattr(
        abstract_api.requests,
        "get",
        Mock(return_value=fake_response),
    )

    result = abstract_api.get_company_by_domain(
        "openai.com",
        api_key="test-key",
    )

    assert result["name"] == "OpenAI"
    assert result["domain"] == "openai.com"

def test_404_raises_company_not_found(monkeypatch):
    fake_response = Mock()
    fake_response.status_code = 404 

    monkeypatch.setattr(
        abstract_api.requests,
        "get",
        Mock(return_value=fake_response),
    )

    with pytest.raises(
        AbstractAPIError,
        match="Company not found",
    ): 
        abstract_api.get_company_by_domain(
            "doesnotexist.com",
            api_key="test-key",
        )



def test_timeout_retries_then_succeeds(monkeypatch):
    successful_response=Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = { 
        "name": "OpenAI",
        "domain": "openai.com",
    }

    mock_get = Mock(
        side_effect=[
            requests.Timeout(),
            successful_response,
        ]
    )

    monkeypatch.setattr(
        abstract_api.requests,
        "get",
        mock_get,
    )

    # Do not actually sleep during test
    monkeypatch.setattr(
        abstract_api,
        "_wait_before_retry",
        Mock(),
    )

    result = abstract_api.get_company_by_domain(
        "openai.com",
        api_key="test-key"
    )

    assert result["name"] == "OpenAI"
    assert mock_get.call_count == 2

def test_timeout_after_all_retries_raises_error(monkeypatch):
    mock_get = Mock(
        side_effect=requests.Timeout()
    )

    monkeypatch.setattr(
        abstract_api.requests,
        "get",
        mock_get,
    )

    monkeypatch.setattr(
        abstract_api,
        "_wait_before_retry",
        Mock(),
    )

    with pytest.raises(
        AbstractAPIError,
        match="timed out after retries",
    ):

        abstract_api.get_company_by_domain(
            "openai.com",
            api_key="test-key"
        )

    assert mock_get.call_count == abstract_api.MAX_RETRIES + 1


def test_server_error_retries_then_succceds(monkeypatch):
    server_error = Mock()
    server_error.status_code = 503
    server_error.headers = {}

    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "name": "OpenAI",
        "domain": "openai.com",
    }

    mock_get = Mock(
        side_effect=[
            server_error,
            successful_response,
        ]
    )

    monkeypatch.setattr(
        abstract_api.requests, 
        "get", 
        mock_get,
    )

    monkeypatch.setattr(
        abstract_api,
        "_wait_before_retry",
        Mock(),
    )

    result = abstract_api.get_company_by_domain(
        "openai.com",
        api_key="test-key"
    )

    assert result["name"] == "OpenAI"
    assert mock_get.call_count == 2 

def test_invalid_json_raises_error(monkeypatch):
    fake_response = Mock()
    fake_response.status_code = 200

    fake_response.json.side_effect = requests.JSONDecodeError(
        "Invalid JSON",
        "",
        0,
    )

    monkeypatch.setattr(
        abstract_api.requests,
        "get",
        Mock(return_value=fake_response),
    )

    with pytest.raises(
        AbstractAPIError,
        match="Abstract API returned invalid JSON",
    ):
        abstract_api.get_company_by_domain(
            "openai.com",
            api_key="test-key",
        )
