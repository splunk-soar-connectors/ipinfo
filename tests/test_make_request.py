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
"""Checks the make request action, with the ipinfo call replaced by a fake."""

import importlib
import json
from typing import Any

import httpx2
import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.make_request import IpinfoMakeRequestParams, make_request
from src.consts import IPINFO_DEFAULT_TIMEOUT

from .conftest import FAKE_TOKEN

# src/actions/__init__.py imports the make_request *function*, which hides the module
# of the same name, so load the module explicitly (as OneDrive's tests do)
make_request_module = importlib.import_module("src.actions.make_request")


def _fake_ipinfo(monkeypatch, response: httpx2.Response) -> list[dict[str, Any]]:
    """Make make request get `response` instead of calling ipinfo.io. Returns each call's arguments."""
    calls: list[dict[str, Any]] = []

    def fake_ipinfo_request(
        asset: Any, method: str, endpoint: str, **kwargs: Any
    ) -> httpx2.Response:
        calls.append({"method": method, "endpoint": endpoint, **kwargs})
        return response

    monkeypatch.setattr(make_request_module, "ipinfo_request", fake_ipinfo_request)
    return calls


def _params(**overrides: Any) -> IpinfoMakeRequestParams:
    return IpinfoMakeRequestParams(
        **{"http_method": "GET", "endpoint": "/8.8.8.8/city", **overrides}
    )


def test_get_with_only_required_fields(monkeypatch, soar, asset) -> None:
    # SOAR sends empty optional fields as None (confirmed on the lab box)
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200, text="Mountain View\n"))

    output = make_request(_params(), soar, asset)

    assert output.status_code == 200
    assert output.response_body == "Mountain View\n"
    assert calls[0]["method"] == "GET"
    assert calls[0]["endpoint"] == "/8.8.8.8/city"
    assert calls[0]["headers"] == {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    assert calls[0]["params"] is None
    assert calls[0]["json_body"] is None
    assert calls[0]["content"] is None
    assert calls[0]["timeout"] == IPINFO_DEFAULT_TIMEOUT
    assert calls[0]["verify"] is True


def test_endpoint_without_leading_slash_is_fixed(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200, text="Mountain View\n"))

    make_request(_params(endpoint="8.8.8.8/city"), soar, asset)

    assert calls[0]["endpoint"] == "/8.8.8.8/city"


@pytest.mark.parametrize(
    "endpoint", ["https://example.com/x", "http://example.com/x", "", "   "]
)
def test_full_urls_and_empty_endpoints_are_rejected(
    monkeypatch, soar, asset, endpoint: str
) -> None:
    # Only ipinfo.io paths are allowed, so the asset token never goes to another host
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    with pytest.raises(ActionFailure, match="Invalid endpoint"):
        make_request(_params(endpoint=endpoint), soar, asset)

    assert calls == []


def test_error_status_is_returned_not_raised(monkeypatch, soar, asset) -> None:
    _fake_ipinfo(
        monkeypatch,
        httpx2.Response(401, json={"error": "Token does not have access to this API"}),
    )

    output = make_request(_params(endpoint="/AS15169/json"), soar, asset)

    assert output.status_code == 401
    assert "Token does not have access to this API" in output.response_body


def test_custom_headers_are_merged_with_defaults(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(
        _params(headers='{"Accept": "text/plain", "X-Test": "1"}'), soar, asset
    )

    assert calls[0]["headers"] == {
        "Accept": "text/plain",
        "Content-Type": "application/json",
        "X-Test": "1",
    }


@pytest.mark.parametrize("headers", ["not-json", '["a", "b"]'])
def test_invalid_headers_are_rejected(monkeypatch, soar, asset, headers: str) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    with pytest.raises(ActionFailure, match="Invalid JSON headers"):
        make_request(_params(headers=headers), soar, asset)

    assert calls == []


def test_json_query_parameters_are_passed_as_params(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(
        _params(endpoint="/8.8.8.8", query_parameters='{"fields": "city"}'), soar, asset
    )

    assert calls[0]["endpoint"] == "/8.8.8.8"
    assert calls[0]["params"] == {"fields": "city"}


def test_query_string_is_appended_to_the_endpoint(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(
        _params(endpoint="/8.8.8.8", query_parameters="?fields=city"), soar, asset
    )

    assert calls[0]["endpoint"] == "/8.8.8.8?fields=city"
    assert calls[0]["params"] is None


def test_non_object_json_query_parameters_are_rejected(
    monkeypatch, soar, asset
) -> None:
    _fake_ipinfo(monkeypatch, httpx2.Response(200))

    with pytest.raises(ActionFailure, match="Invalid query parameters"):
        make_request(_params(query_parameters='["fields"]'), soar, asset)


def test_post_batch_sends_the_json_body(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(
        monkeypatch,
        httpx2.Response(
            200, json={"8.8.8.8/city": "Mountain View", "1.1.1.1/country": "AU"}
        ),
    )

    output = make_request(
        _params(
            http_method="POST",
            endpoint="/batch",
            body='["8.8.8.8/city", "1.1.1.1/country"]',
        ),
        soar,
        asset,
    )

    assert calls[0]["method"] == "POST"
    assert calls[0]["json_body"] == ["8.8.8.8/city", "1.1.1.1/country"]
    assert calls[0]["content"] is None
    assert "Mountain View" in output.response_body


def test_plain_text_body_is_sent_as_is(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(
        _params(
            http_method="POST",
            endpoint="/batch",
            headers='{"Content-Type": "text/plain"}',
            body="8.8.8.8/city 1.1.1.1/country",
        ),
        soar,
        asset,
    )

    assert calls[0]["json_body"] is None
    assert calls[0]["content"] == "8.8.8.8/city 1.1.1.1/country"


def test_invalid_json_body_is_rejected(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    with pytest.raises(ActionFailure, match="Invalid JSON body"):
        make_request(
            _params(http_method="POST", endpoint="/batch", body="[not json"),
            soar,
            asset,
        )

    assert calls == []


def test_timeout_and_verify_ssl_are_passed_through(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(_params(timeout=10, verify_ssl=False), soar, asset)

    assert calls[0]["timeout"] == 10
    assert calls[0]["verify"] is False


@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def test_other_methods_are_sent_unchanged(
    monkeypatch, soar, asset, method: str
) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(_params(http_method=method), soar, asset)

    assert calls[0]["method"] == method


def test_token_in_the_reply_is_redacted(monkeypatch, soar, asset) -> None:
    # ipinfo echoes the token in 401 replies and in /me
    _fake_ipinfo(
        monkeypatch,
        httpx2.Response(
            401,
            json={
                "error": "Token does not have access to this API",
                "token": FAKE_TOKEN,
            },
        ),
    )

    output = make_request(_params(endpoint="/AS15169/json"), soar, asset)

    assert output.status_code == 401
    assert FAKE_TOKEN not in output.response_body
    body = json.loads(output.response_body)
    assert body["token"] == "***"
    assert body["error"] == "Token does not have access to this API"


def test_reply_is_unchanged_without_a_token(
    monkeypatch, soar, asset_without_token
) -> None:
    _fake_ipinfo(monkeypatch, httpx2.Response(200, text="Mountain View\n"))

    output = make_request(_params(), soar, asset_without_token)

    assert output.response_body == "Mountain View\n"


def test_lowercase_content_type_replaces_the_default(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(
        _params(
            http_method="POST",
            endpoint="/batch",
            headers='{"content-type": "text/plain"}',
            body="8.8.8.8/city",
        ),
        soar,
        asset,
    )

    assert calls[0]["headers"] == {
        "Accept": "application/json",
        "content-type": "text/plain",
    }
    assert calls[0]["json_body"] is None
    assert calls[0]["content"] == "8.8.8.8/city"


def test_json_scalar_body_is_sent(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(
        _params(http_method="POST", endpoint="/batch", body="123"), soar, asset
    )

    assert calls[0]["json_body"] == 123
    assert calls[0]["content"] is None


def test_non_string_header_values_are_converted(monkeypatch, soar, asset) -> None:
    calls = _fake_ipinfo(monkeypatch, httpx2.Response(200))

    make_request(_params(headers='{"X-Retry": 1, "X-Debug": true}'), soar, asset)

    assert calls[0]["headers"]["X-Retry"] == "1"
    assert calls[0]["headers"]["X-Debug"] == "True"
