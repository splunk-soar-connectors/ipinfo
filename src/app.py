# Copyright (c) 2019-2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions
# and limitations under the License.
import ipaddress
import re

from pydantic import ConfigDict
from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.app import App
from soar_sdk.asset import AssetField, BaseAsset, FieldCategory
from soar_sdk.exceptions import ActionFailure
from soar_sdk.logging import getLogger
from soar_sdk.params import Param, Params

from .consts import (
    IPINFO_BAD_IP_ERROR,
    IPINFO_INVALID_ASN_ERROR,
    IPINFO_INVALID_IP_ERROR,
    IPINFO_TEST_CONNECTIVITY_IP,
)
from .helper import make_rest_call, summary_message
from .make_request import make_request


logger = getLogger()

ASN_REGEX = re.compile(r"AS\d+", re.IGNORECASE)


class Asset(BaseAsset):
    token: str | None = AssetField(
        required=False,
        description="IPinfo API token",
        sensitive=True,
        category=FieldCategory.CONNECTIVITY,
    )


app = App(
    name="IPinfo",
    app_type="information",
    logo="logo_ipinfo.svg",
    logo_dark="logo_ipinfo_dark.svg",
    product_vendor="ipinfo.io",
    product_name="ipinfo.io",
    publisher="Splunk",
    appid="4da0b970-9440-418a-b5b1-f6d2def0ade2",
    fips_compliant=True,
    asset_cls=Asset,
)


def _lookup_ip(token: str | None, ip: str) -> dict:
    try:
        ipaddress.ip_address(ip)
    except ValueError:
        raise ActionFailure(IPINFO_INVALID_IP_ERROR) from None

    response = make_rest_call(token, f"{ip}/json")
    if response.get("bogon"):
        raise ActionFailure(IPINFO_BAD_IP_ERROR)
    return response


@app.test_connectivity()
def test_connectivity(soar: SOARClient, asset: Asset) -> None:
    """Validate the asset configuration for connectivity using supplied configuration."""
    logger.info("Connecting to endpoint")
    try:
        _lookup_ip(asset.token, IPINFO_TEST_CONNECTIVITY_IP)
    except ActionFailure:
        logger.info("Test Connectivity Failed.")
        raise
    logger.info("Test Connectivity Passed")


# IPinfo returns more fields with paid plans (abuse, privacy, domains, ...), and may return
# numbers for string fields. Keep undeclared keys so action_result.data matches the API
# response, as the legacy app's raw add_data() did.
_LENIENT = ConfigDict(coerce_numbers_to_str=True, extra="allow")


class LookupIpParams(Params):
    ip: str = Param(
        description="IP to lookup",
        required=True,
        primary=True,
        cef_types=["ip"],
        column_name="IP",
    )


class AsnOutput(ActionOutput):
    model_config = _LENIENT

    asn: str | None = OutputField(cef_types=["asn"], example_values=["AS15169"])
    domain: str | None = OutputField(
        cef_types=["domain"], example_values=["google.com"]
    )
    name: str | None = OutputField(example_values=["Google LLC"])
    route: str | None = OutputField(example_values=["8.8.8.0/24"])
    type: str | None = OutputField(example_values=["hosting"])


class CarrierOutput(ActionOutput):
    model_config = _LENIENT

    mcc: str | None = OutputField(example_values=["310"])
    mnc: str | None = OutputField(example_values=["150"])
    name: str | None = OutputField(example_values=["AT&T"])


class CompanyOutput(ActionOutput):
    model_config = _LENIENT

    domain: str | None = OutputField(
        cef_types=["domain"], example_values=["google.com"]
    )
    name: str | None = OutputField(example_values=["Google LLC"])
    type: str | None = OutputField(example_values=["hosting"])


class LocOutput(ActionOutput):
    model_config = _LENIENT

    latitude: str | None = OutputField(example_values=["37.3860"])
    longitude: str | None = OutputField(example_values=["-122.0840"])


class LookupIpOutput(ActionOutput):
    model_config = _LENIENT

    # The legacy action_result.status table column; the SDK has no implicit status column.
    status: str = OutputField(
        column_name="Status", example_values=["success", "failed"]
    )
    anycast: bool | None
    asn: AsnOutput | None
    carrier: CarrierOutput | None
    city: str | None = OutputField(example_values=["Mountain View"])
    company: CompanyOutput | None
    country: str | None = OutputField(example_values=["US"])
    hostname: str | None = OutputField(
        cef_types=["host name"], example_values=["google-public-dns-a.google.com"]
    )
    ip: str | None = OutputField(cef_types=["ip"], example_values=["8.8.8.8"])
    loc: LocOutput | None
    org: str | None = OutputField(example_values=["AS15169 Google LLC"])
    phone: str | None = OutputField(example_values=["650"])
    postal: str | None = OutputField(example_values=["94035"])
    readme: str | None = OutputField(example_values=["https://ipinfo.io/missingauth"])
    region: str | None = OutputField(example_values=["California"])
    timezone: str | None = OutputField(example_values=["America/Los_Angeles"])


class LookupIpSummary(ActionOutput):
    city: str | None = OutputField(example_values=["Mountain View"])
    region: str | None = OutputField(example_values=["California"])
    country: str | None = OutputField(example_values=["US"])
    company_domain: str | None = OutputField(
        cef_types=["domain"], example_values=["google.com"]
    )
    company_name: str | None = OutputField(example_values=["Google LLC"])
    company_type: str | None = OutputField(example_values=["hosting"])
    carrier_name: str | None = OutputField(example_values=["AT&T"])


def _split_loc(loc: object) -> object:
    # IPinfo returns "lat,lng"; the legacy app exposed it as loc.latitude / loc.longitude.
    if isinstance(loc, str) and "," in loc:
        latitude, longitude = loc.split(",", 1)
        return {"latitude": latitude.strip(), "longitude": longitude.strip()}
    return loc


@app.action(
    description="Lookup the details of an IP address",
    action_type="investigate",
    read_only=True,
    render_as="table",
    summary_type=LookupIpSummary,
)
def lookup_ip(params: LookupIpParams, soar: SOARClient, asset: Asset) -> LookupIpOutput:
    """Lookup the details of an IP address."""
    logger.debug("Making rest call for lookup_ip")
    response = _lookup_ip(asset.token, params.ip)

    if "loc" in response:
        response["loc"] = _split_loc(response["loc"])

    company = (
        response.get("company") if isinstance(response.get("company"), dict) else {}
    )
    carrier = (
        response.get("carrier") if isinstance(response.get("carrier"), dict) else {}
    )
    summary = {
        "city": response.get("city"),
        "region": response.get("region"),
        "country": response.get("country"),
    }
    if company:
        summary.update(
            company_domain=company.get("domain"),
            company_name=company.get("name"),
            company_type=company.get("type"),
        )
    if carrier:
        summary["carrier_name"] = carrier.get("name")

    soar.set_summary(LookupIpSummary(**summary))
    soar.set_message(summary_message(summary))

    response.pop("status", None)
    return LookupIpOutput(status="success", **response)


class LookupAsnParams(Params):
    asn: str = Param(
        description="ASN to lookup",
        required=True,
        primary=True,
        cef_types=["asn"],
        column_name="ASN",
    )


class PrefixOutput(ActionOutput):
    model_config = _LENIENT

    country: str | None = OutputField(example_values=["US"])
    domain: str | None = OutputField(example_values=["ccselink.com"])
    id: str | None = OutputField(example_values=["AKAMAI"])
    name: str | None = OutputField(example_values=["Akamai Technologies, Inc."])
    netblock: str | None = OutputField(example_values=["104.109.53.0/24"])
    size: str | None = OutputField(example_values=["256"])
    status: str | None = OutputField(example_values=["REASSIGNMENT"])


class Prefix6Output(ActionOutput):
    model_config = _LENIENT

    country: str | None = OutputField(example_values=["US"])
    domain: str | None = OutputField(example_values=["comcast.com"])
    id: str | None = OutputField(example_values=["COMCAST6NET"])
    name: str | None = OutputField(example_values=["Comcast Cable Communications, LLC"])
    netblock: str | None = OutputField(example_values=["2001:558::/29"])
    size: str | None = OutputField(example_values=["633825300114114700748351602688"])
    status: str | None = OutputField(example_values=["ALLOCATION"])


class LookupAsnOutput(ActionOutput):
    model_config = _LENIENT

    # Table columns, declared in the original manifest's column order (ASN param is first).
    status: str = OutputField(
        column_name="Status", example_values=["success", "failed"]
    )
    name: str | None = OutputField(
        column_name="Name", example_values=["Comcast Cable Communications, LLC"]
    )
    domain: str | None = OutputField(
        column_name="Domain", cef_types=["domain"], example_values=["comcast.net"]
    )
    registry: str | None = OutputField(column_name="Registry", example_values=["arin"])
    country: str | None = OutputField(column_name="Country", example_values=["US"])

    allocated: str | None = OutputField(example_values=["1997-02-14"])
    asn: str | None = OutputField(cef_types=["asn"], example_values=["AS7922"])
    num_ips: int | None = OutputField(example_values=[71211264])
    prefixes: list[PrefixOutput] | None
    prefixes6: list[Prefix6Output] | None
    type: str | None = OutputField(example_values=["isp"])


class LookupAsnSummary(ActionOutput):
    name: str | None = OutputField(example_values=["Comcast Cable Communications, LLC"])
    num_ips: int | None = OutputField(example_values=[71211264])


@app.action(
    description="Lookup the details of an Autonomous System Number",
    action_type="investigate",
    read_only=True,
    render_as="table",
    summary_type=LookupAsnSummary,
)
def lookup_asn(
    params: LookupAsnParams, soar: SOARClient, asset: Asset
) -> LookupAsnOutput:
    """Lookup the details of an Autonomous System Number."""
    if not ASN_REGEX.fullmatch(params.asn):
        raise ActionFailure(IPINFO_INVALID_ASN_ERROR)

    logger.debug("Making rest call for lookup_asn")
    response = make_rest_call(asset.token, f"{params.asn.upper()}/json")

    summary = {"name": response.get("name"), "num_ips": response.get("num_ips")}
    soar.set_summary(LookupAsnSummary(**summary))
    soar.set_message(summary_message(summary))

    response.pop("status", None)
    return LookupAsnOutput(status="success", **response)


app.make_request()(make_request)


if __name__ == "__main__":
    app.cli()
