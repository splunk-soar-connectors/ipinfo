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
"""Checks the lookup ip action, with the ipinfo call replaced by a fake reply."""

import importlib
import re
from typing import Any

import pytest
from soar_sdk.exceptions import ActionFailure

from src.actions.lookup_ip import LookupIpOutput, LookupIpParams, lookup_ip
from src.consts import IPINFO_BAD_IP_ERROR

from .conftest import SAMPLE_IP_RESPONSE, SAMPLE_PAID_IP_RESPONSE

# src/actions/__init__.py imports the lookup_ip *function*, which hides the module
# of the same name, so load the module explicitly (as OneDrive's tests do)
lookup_ip_module = importlib.import_module("src.actions.lookup_ip")


def _fake_ipinfo(monkeypatch, reply: dict[str, Any]) -> list[str]:
    """Make lookup ip get `reply` instead of calling ipinfo.io. Returns the endpoints asked for."""
    endpoints: list[str] = []

    def fake_ipinfo_get(asset: Any, endpoint: str) -> dict[str, Any]:
        endpoints.append(endpoint)
        return dict(reply)

    monkeypatch.setattr(lookup_ip_module, "ipinfo_get", fake_ipinfo_get)
    return endpoints


def test_lookup_ip_returns_ipinfo_details(monkeypatch, soar, asset) -> None:
    endpoints = _fake_ipinfo(monkeypatch, SAMPLE_IP_RESPONSE)

    output = lookup_ip(LookupIpParams(ip="8.8.8.8"), soar, asset)

    assert endpoints == ["8.8.8.8/json"]
    assert output.ip == "8.8.8.8"
    assert output.city == "Mountain View"
    assert output.org == "AS15169 Google LLC"


def test_lookup_ip_splits_loc_into_latitude_and_longitude(
    monkeypatch, soar, asset
) -> None:
    _fake_ipinfo(monkeypatch, SAMPLE_IP_RESPONSE)

    output = lookup_ip(LookupIpParams(ip="8.8.8.8"), soar, asset)

    assert output.loc.latitude == "37.4056"
    assert output.loc.longitude == "-122.0775"


def test_lookup_ip_summary_matches_legacy(monkeypatch, soar, asset) -> None:
    # app-tests expects the message "City: Mountain View, Region: California, Country: US",
    # so empty company/carrier keys must not be in the summary
    _fake_ipinfo(monkeypatch, SAMPLE_IP_RESPONSE)

    lookup_ip(LookupIpParams(ip="8.8.8.8"), soar, asset)

    assert soar.summary.model_dump() == {
        "city": "Mountain View",
        "region": "California",
        "country": "US",
    }


def test_lookup_ip_summary_includes_company_when_returned(
    monkeypatch, soar, asset
) -> None:
    _fake_ipinfo(monkeypatch, SAMPLE_PAID_IP_RESPONSE)

    lookup_ip(LookupIpParams(ip="8.8.8.8"), soar, asset)

    summary = soar.summary.model_dump()
    assert summary["company_name"] == "Google LLC"
    assert summary["company_domain"] == "google.com"
    assert "carrier_name" not in summary


def test_lookup_ip_keeps_the_asn_data_path(monkeypatch, soar, asset) -> None:
    # app-tests feeds action_result.data.*.asn.asn from lookup ip into lookup asn
    _fake_ipinfo(monkeypatch, SAMPLE_PAID_IP_RESPONSE)

    output = lookup_ip(LookupIpParams(ip="8.8.8.8"), soar, asset)

    assert output.model_dump()["asn"]["asn"] == "AS15169"


def test_lookup_ip_accepts_ipv6(monkeypatch, soar, asset) -> None:
    endpoints = _fake_ipinfo(
        monkeypatch, {**SAMPLE_IP_RESPONSE, "ip": "2001:4860:4860::8888"}
    )

    output = lookup_ip(LookupIpParams(ip="2001:4860:4860::8888"), soar, asset)

    assert endpoints == ["2001:4860:4860::8888/json"]
    assert output.ip == "2001:4860:4860::8888"


def test_lookup_ip_fails_on_bogon(monkeypatch, soar, asset) -> None:
    _fake_ipinfo(monkeypatch, {"ip": "192.168.1.1", "bogon": True})

    with pytest.raises(ActionFailure, match=re.escape(IPINFO_BAD_IP_ERROR)):
        lookup_ip(LookupIpParams(ip="192.168.1.1"), soar, asset)


@pytest.mark.parametrize(
    "bad_ip",
    [
        "10.40.1",
        "10.40.1.777",
        "001:db8:3333:4444:5555:6666:",
        "2001:db8:3333:4444:5555:6666:7777:hhhh",
        "test_string",
        "",
        "漢字©¬ɸ",
    ],
)
def test_lookup_ip_rejects_invalid_ip_without_calling_ipinfo(
    monkeypatch, soar, asset, bad_ip: str
) -> None:
    endpoints = _fake_ipinfo(monkeypatch, SAMPLE_IP_RESPONSE)

    with pytest.raises(ActionFailure, match="Invalid IP address"):
        lookup_ip(LookupIpParams(ip=bad_ip), soar, asset)

    assert endpoints == []


def test_output_accepts_missing_fields_stored_as_none() -> None:
    # SOAR stores every output field, missing ones as None, and the view reads
    # them back into LookupIpOutput. This failed on the lab box before the
    # fields were made optional ("Data parsing failed ... phone").
    stored = LookupIpOutput(ip="8.8.8.8").model_dump()

    reparsed = LookupIpOutput(**stored)

    assert reparsed.phone is None
    assert reparsed.readme is None
    assert reparsed.loc is None


def test_lookup_ip_keeps_fields_that_are_not_declared(monkeypatch, soar, asset) -> None:
    # Paid plans return more than the declared outputs (ipinfo docs: privacy,
    # abuse, domains). Legacy stored the whole reply, so playbooks may use them.
    _fake_ipinfo(
        monkeypatch,
        {
            **SAMPLE_PAID_IP_RESPONSE,
            "privacy": {
                "vpn": True,
                "proxy": False,
                "tor": False,
                "service": "PrivateVPN",
            },
            "abuse": {"email": "abuse@example.com"},
            "asn": {**SAMPLE_PAID_IP_RESPONSE["asn"], "country": "US"},
        },
    )

    output = lookup_ip(LookupIpParams(ip="8.8.8.8"), soar, asset)
    stored = output.model_dump(by_alias=True)

    assert stored["privacy"]["vpn"] is True
    assert stored["abuse"]["email"] == "abuse@example.com"
    assert stored["asn"]["country"] == "US"
    # SOAR stores the dump and the widget reads it back into the model
    assert LookupIpOutput(**stored).model_dump()["privacy"]["service"] == "PrivateVPN"
