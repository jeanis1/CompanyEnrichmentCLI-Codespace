from unittest.mock import Mock

import pytest
import requests

from clients.abstract_api import AbstractAPIClient, AbstractAPIError


BASE_URL = "https://example.test/company"


def make_client(session: Mock, max_retries: int = 3) -> AbstractAPIClient:
    return AbstractAPIClient(
        api_key="test-key",
        base_url=BASE_URL,
        max_retries=max_retries,
        session=session,
        sleep=lambda _: None,
    )


def test_successful_request():
    fake_response = Mock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "name": "OpenAI",
        "domain": "openai.com",
    }

    session = Mock()
    session.get.return_value = fake_response

    result = make_client(session).get_company_by_domain("openai.com")

    assert result["name"] == "OpenAI"
    assert result["domain"] == "openai.com"
    session.get.assert_called_once_with(
        BASE_URL,
        params={"api_key": "test-key", "domain": "openai.com"},
        timeout=10.0,
    )


def test_missing_api_key_raises_error():
    with pytest.raises(
        AbstractAPIError,
        match="ABSTRACT_API_KEY is not configured",
    ):
        AbstractAPIClient(api_key="", base_url=BASE_URL)


def test_404_raises_company_not_found():
    fake_response = Mock()
    fake_response.status_code = 404

    session = Mock()
    session.get.return_value = fake_response

    with pytest.raises(AbstractAPIError, match="Company not found"):
        make_client(session).get_company_by_domain("doesnotexist.com")


def test_timeout_retries_then_succeeds():
    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "name": "OpenAI",
        "domain": "openai.com",
    }

    session = Mock()
    session.get.side_effect = [requests.Timeout(), successful_response]

    result = make_client(session).get_company_by_domain("openai.com")

    assert result["name"] == "OpenAI"
    assert session.get.call_count == 2


def test_timeout_after_all_retries_raises_error():
    session = Mock()
    session.get.side_effect = requests.Timeout()

    client = make_client(session, max_retries=3)

    with pytest.raises(AbstractAPIError, match="timed out after retries"):
        client.get_company_by_domain("openai.com")

    assert session.get.call_count == 4


def test_server_error_retries_then_succeeds():
    server_error = Mock()
    server_error.status_code = 503
    server_error.headers = {}

    successful_response = Mock()
    successful_response.status_code = 200
    successful_response.json.return_value = {
        "name": "OpenAI",
        "domain": "openai.com",
    }

    session = Mock()
    session.get.side_effect = [server_error, successful_response]

    result = make_client(session).get_company_by_domain("openai.com")

    assert result["name"] == "OpenAI"
    assert session.get.call_count == 2
