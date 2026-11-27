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
"""Shared helpers for the IPinfo unit tests.

None of these tests call ipinfo.io. Each test replaces the function that would
make the HTTP call with a fake that returns a prepared reply.
"""

from types import SimpleNamespace
from typing import Any

import pytest

# Not a real token. Tests use it to check where the token is (and is not) sent.
FAKE_TOKEN = "fake-test-token"

# Sample replies in the shape ipinfo.io documents for each endpoint.
SAMPLE_IP_RESPONSE: dict[str, Any] = {
    "ip": "8.8.8.8",
    "hostname": "dns.google",
    "city": "Mountain View",
    "region": "California",
    "country": "US",
    "loc": "37.4056,-122.0775",
    "org": "AS15169 Google LLC",
    "postal": "94043",
    "timezone": "America/Los_Angeles",
    "anycast": True,
}

SAMPLE_PAID_IP_RESPONSE: dict[str, Any] = {
    **SAMPLE_IP_RESPONSE,
    "asn": {
        "asn": "AS15169",
        "name": "Google LLC",
        "domain": "google.com",
        "route": "8.8.8.0/24",
        "type": "hosting",
    },
    "company": {"name": "Google LLC", "domain": "google.com", "type": "hosting"},
}

SAMPLE_ASN_RESPONSE: dict[str, Any] = {
    "asn": "AS15169",
    "name": "Google LLC",
    "country": "US",
    "allocated": "2000-03-30",
    "registry": "arin",
    "domain": "google.com",
    "num_ips": 16000000,
    "type": "hosting",
    "prefixes": [
        {
            "netblock": "8.8.8.0/24",
            "id": "LVLT-GOGL-8-8-8",
            "name": "Google LLC",
            "country": "US",
            "size": "256",
            "status": "ASSIGNMENT",
            "domain": "google.com",
        }
    ],
    "prefixes6": [
        {
            "netblock": "2001:4860::/32",
            "id": "GOOGLE-IPV6",
            "name": "Google LLC",
            "country": "US",
            "size": "79228162514264337593543950336",
            "status": "ALLOCATION",
            "domain": "google.com",
        }
    ],
}


class FakeSoar:
    """Stands in for the SOAR client. Only records the summary an action sets."""

    def __init__(self) -> None:
        self.summary = None

    def set_summary(self, summary: Any) -> None:
        self.summary = summary


@pytest.fixture
def soar() -> FakeSoar:
    return FakeSoar()


@pytest.fixture
def asset() -> SimpleNamespace:
    """An asset with a token. Actions only read asset.token."""
    return SimpleNamespace(token=FAKE_TOKEN)


@pytest.fixture
def asset_without_token() -> SimpleNamespace:
    return SimpleNamespace(token=None)
