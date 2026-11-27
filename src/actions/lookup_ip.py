# Copyright (c) 2019-2026 Splunk Inc.
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
import ipaddress

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..consts import IPINFO_BAD_IP_ERROR
from ..ipinfo_client import ipinfo_get


class LookupIpParams(Params):
    ip: str = Param(
        description="IP to lookup", primary=True, cef_types=["ip"], column_name="IP"
    )


class AsnOutput(ActionOutput):
    asn: str | None = OutputField(cef_types=["asn"], example_values=["AS15169"])
    domain: str | None = OutputField(cef_types=["domain"], example_values=["google.com"])
    name: str | None = OutputField(example_values=["Google LLC"])
    route: str | None = OutputField(example_values=["8.8.8.0/24"])
    type: str | None = OutputField(example_values=["hosting"])


class CarrierOutput(ActionOutput):
    mcc: str | None = OutputField(example_values=["310"])
    mnc: str | None = OutputField(example_values=["150"])
    name: str | None = OutputField(example_values=["AT&T"])


class CompanyOutput(ActionOutput):
    domain: str | None = OutputField(cef_types=["domain"], example_values=["google.com"])
    name: str | None = OutputField(example_values=["Google LLC"])
    type: str | None = OutputField(example_values=["hosting"])


class LocOutput(ActionOutput):
    latitude: str | None = OutputField(example_values=["37.3860"])
    longitude: str | None = OutputField(example_values=["-122.0840"])


class LookupIpOutput(ActionOutput):
    # Field order sets the widget table column order: City, Region, Country, Organization
    ip: str | None = OutputField(cef_types=["ip"], example_values=["8.8.8.8"])
    hostname: str | None = OutputField(
        cef_types=["host name"], example_values=["google-public-dns-a.google.com"]
    )
    city: str | None = OutputField(example_values=["Mountain View"], column_name="City")
    region: str | None = OutputField(example_values=["California"], column_name="Region")
    country: str | None = OutputField(example_values=["US"], column_name="Country")
    org: str | None = OutputField(
        example_values=["AS15169 Google LLC"], column_name="Organization"
    )
    loc: LocOutput | None = None
    postal: str | None = OutputField(example_values=["94035"])
    timezone: str | None = OutputField(example_values=["America/Los_Angeles"])
    phone: str | None = OutputField(example_values=["650"])
    anycast: bool | None = None
    asn: AsnOutput | None = None
    company: CompanyOutput | None = None
    carrier: CarrierOutput | None = None
    readme: str | None = OutputField(example_values=["https://ipinfo.io/missingauth"])


class LookupIpSummary(ActionOutput):
    city: str | None = None
    region: str | None = None
    country: str | None = None
    company_domain: str | None = OutputField(cef_types=["domain"])
    company_name: str | None = None
    company_type: str | None = None
    carrier_name: str | None = None

    def model_dump(self, **kwargs: object) -> dict:
        # Like legacy, leave out company/carrier keys that ipinfo did not return
        # instead of showing "Company name: None" in the summary
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


def lookup_ip(params: LookupIpParams, soar: SOARClient, asset: Asset) -> LookupIpOutput:
    try:
        ipaddress.ip_address(params.ip)
    except ValueError as e:
        raise ActionFailure(f"Invalid IP address: {params.ip}") from e

    response = ipinfo_get(asset, f"{params.ip}/json")

    if response.get("bogon"):
        raise ActionFailure(IPINFO_BAD_IP_ERROR)

    # ipinfo returns "lat,long" as one string; split it so the output has separate fields
    if "loc" in response:
        lat, lng = response["loc"].split(",")
        response["loc"] = {"latitude": lat, "longitude": lng}

    company = response.get("company") or {}
    carrier = response.get("carrier") or {}
    soar.set_summary(
        LookupIpSummary(
            city=response.get("city"),
            region=response.get("region"),
            country=response.get("country"),
            company_domain=company.get("domain"),
            company_name=company.get("name"),
            company_type=company.get("type"),
            carrier_name=carrier.get("name"),
        )
    )

    return LookupIpOutput(**response)
