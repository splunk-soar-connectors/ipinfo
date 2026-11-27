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
"""Checks the lookup asn action with a fake ipinfo reply.

The ASN details API needs a paid ipinfo plan, so these tests are how the
success path is verified without a paid token.
"""

import importlib
from typing import Any

import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.lookup_asn import LookupAsnOutput, LookupAsnParams, lookup_asn

from .conftest import SAMPLE_ASN_RESPONSE

# src/actions/__init__.py imports the lookup_asn *function*, which hides the module
# of the same name, so load the module explicitly (as OneDrive's tests do)
lookup_asn_module = importlib.import_module("src.actions.lookup_asn")


def _fake_ipinfo(monkeypatch, reply: dict[str, Any]) -> list[str]:
    """Make lookup asn get `reply` instead of calling ipinfo.io. Returns the endpoints asked for."""
    endpoints: list[str] = []

    def fake_ipinfo_get(asset: Any, endpoint: str) -> dict[str, Any]:
        endpoints.append(endpoint)
        return dict(reply)

    monkeypatch.setattr(lookup_asn_module, "ipinfo_get", fake_ipinfo_get)
    return endpoints


def test_lookup_asn_returns_asn_details(monkeypatch, soar, asset) -> None:
    endpoints = _fake_ipinfo(monkeypatch, SAMPLE_ASN_RESPONSE)

    output = lookup_asn(LookupAsnParams(asn="AS15169"), soar, asset)

    assert endpoints == ["AS15169/json"]
    assert output.asn == "AS15169"
    assert output.name == "Google LLC"
    assert output.domain == "google.com"
    assert output.registry == "arin"
    assert output.country == "US"
    assert output.prefixes[0].netblock == "8.8.8.0/24"
    assert output.prefixes6[0].netblock == "2001:4860::/32"


def test_lookup_asn_sets_summary(monkeypatch, soar, asset) -> None:
    _fake_ipinfo(monkeypatch, SAMPLE_ASN_RESPONSE)

    lookup_asn(LookupAsnParams(asn="AS15169"), soar, asset)

    assert soar.summary.name == "Google LLC"
    assert soar.summary.num_ips == 16000000


def test_lookup_asn_accepts_lowercase(monkeypatch, soar, asset) -> None:
    # app-tests: lookup_asn_case_sensitive_valid_001 expects "as15169" to succeed
    endpoints = _fake_ipinfo(monkeypatch, SAMPLE_ASN_RESPONSE)

    lookup_asn(LookupAsnParams(asn="as15169"), soar, asset)

    assert endpoints == ["AS15169/json"]


@pytest.mark.parametrize(
    "bad_asn", ["8.8.8.8", "ASP15169", "15169", "AS", "", "漢字©¬ɸ"]
)
def test_lookup_asn_rejects_invalid_asn_without_calling_ipinfo(
    monkeypatch, soar, asset, bad_asn: str
) -> None:
    endpoints = _fake_ipinfo(monkeypatch, SAMPLE_ASN_RESPONSE)

    with pytest.raises(ActionFailure, match="Invalid ASN"):
        lookup_asn(LookupAsnParams(asn=bad_asn), soar, asset)

    assert endpoints == []


def test_lookup_asn_passes_ipinfo_errors_through(monkeypatch, soar, asset) -> None:
    # e.g. a Lite token: ipinfo_get raises, and the action must fail with that error
    def fake_ipinfo_get(asset: Any, endpoint: str) -> dict[str, Any]:
        raise ActionFailure(
            "API returned an error. Status code: 401. Error: Token does not have access to this API"
        )

    monkeypatch.setattr(lookup_asn_module, "ipinfo_get", fake_ipinfo_get)

    with pytest.raises(ActionFailure, match="Status code: 401"):
        lookup_asn(LookupAsnParams(asn="AS15169"), soar, asset)


def test_output_accepts_missing_fields_stored_as_none() -> None:
    stored = LookupAsnOutput(asn="AS15169").model_dump()

    reparsed = LookupAsnOutput(**stored)

    assert reparsed.name is None
    assert reparsed.prefixes is None


def test_lookup_asn_keeps_fields_that_are_not_declared(
    monkeypatch, soar, asset
) -> None:
    _fake_ipinfo(
        monkeypatch,
        {**SAMPLE_ASN_RESPONSE, "peers": ["AS1"], "upstreams": ["AS2"]},
    )

    output = lookup_asn(LookupAsnParams(asn="AS15169"), soar, asset)

    assert output.model_dump()["peers"] == ["AS1"]
    assert output.model_dump()["upstreams"] == ["AS2"]
