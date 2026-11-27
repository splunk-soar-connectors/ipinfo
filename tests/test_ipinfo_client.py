# Copyright (c) 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Checks the one place that talks to ipinfo.io, with httpx.request replaced by a fake."""

from typing import Any

import re

import httpx
import pytest
from soar_sdk.exceptions import ActionFailure

from src import ipinfo_client
from src.consts import IPINFO_DEFAULT_TIMEOUT

from .conftest import FAKE_TOKEN, SAMPLE_IP_RESPONSE


def _fake_httpx(monkeypatch, response: httpx.Response) -> list[dict[str, Any]]:
    """Replace httpx.request with a fake that records each call and returns response."""
    calls: list[dict[str, Any]] = []

    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        calls.append({"method": method, "url": url, **kwargs})
        return response

    monkeypatch.setattr(ipinfo_client.httpx, "request", fake_request)
    return calls


def test_request_adds_bearer_token_and_default_timeout(monkeypatch, asset) -> None:
    calls = _fake_httpx(monkeypatch, httpx.Response(200, json=SAMPLE_IP_RESPONSE))

    ipinfo_client.ipinfo_request(asset, "GET", "8.8.8.8/json")

    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://ipinfo.io/8.8.8.8/json"
    assert calls[0]["headers"]["Authorization"] == f"Bearer {FAKE_TOKEN}"
    assert calls[0]["timeout"] == IPINFO_DEFAULT_TIMEOUT


def test_request_without_token_sends_no_authorization_header(
    monkeypatch, asset_without_token
) -> None:
    calls = _fake_httpx(monkeypatch, httpx.Response(200, json=SAMPLE_IP_RESPONSE))

    ipinfo_client.ipinfo_request(asset_without_token, "GET", "8.8.8.8/json")

    assert "Authorization" not in calls[0]["headers"]


def test_request_does_not_double_the_slash(monkeypatch, asset) -> None:
    calls = _fake_httpx(monkeypatch, httpx.Response(200, json=SAMPLE_IP_RESPONSE))

    ipinfo_client.ipinfo_request(asset, "GET", "/8.8.8.8/json")

    assert calls[0]["url"] == "https://ipinfo.io/8.8.8.8/json"


def test_connection_error_becomes_action_failure(monkeypatch, asset) -> None:
    def fake_request(method: str, url: str, **kwargs: Any) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(ipinfo_client.httpx, "request", fake_request)

    with pytest.raises(ActionFailure, match=re.escape("Error connecting to ipinfo.io")):
        ipinfo_client.ipinfo_request(asset, "GET", "8.8.8.8/json")


def test_get_returns_the_json_body(monkeypatch, asset) -> None:
    _fake_httpx(monkeypatch, httpx.Response(200, json=SAMPLE_IP_RESPONSE))

    assert ipinfo_client.ipinfo_get(asset, "8.8.8.8/json") == SAMPLE_IP_RESPONSE


def test_get_raises_on_api_error_without_leaking_the_token(monkeypatch, asset) -> None:
    # ipinfo echoes the token back in some error replies; legacy put it in the error message
    _fake_httpx(
        monkeypatch,
        httpx.Response(
            401,
            json={
                "error": "Token does not have access to this API",
                "token": FAKE_TOKEN,
            },
        ),
    )

    with pytest.raises(ActionFailure) as excinfo:
        ipinfo_client.ipinfo_get(asset, "AS15169/json")

    assert "Status code: 401" in str(excinfo.value)
    assert "Token does not have access to this API" in str(excinfo.value)
    assert FAKE_TOKEN not in str(excinfo.value)


def test_get_raises_when_error_key_comes_with_200(monkeypatch, asset) -> None:
    _fake_httpx(monkeypatch, httpx.Response(200, json={"error": "Wrong ip"}))

    with pytest.raises(ActionFailure, match="Wrong ip"):
        ipinfo_client.ipinfo_get(asset, "nope/json")


def test_get_raises_on_non_json_reply(monkeypatch, asset) -> None:
    _fake_httpx(monkeypatch, httpx.Response(502, text="<html>Bad Gateway</html>"))

    with pytest.raises(
        ActionFailure,
        match=re.escape("Unable to parse JSON response. Status code: 502"),
    ):
        ipinfo_client.ipinfo_get(asset, "8.8.8.8/json")
