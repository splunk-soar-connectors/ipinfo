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
import re

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import ActionOutput, OutputField
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import Param, Params

from ..asset import Asset
from ..ipinfo_client import ipinfo_get
from ..outputs import IpinfoOutput


class LookupAsnParams(Params):
    asn: str = Param(
        description="ASN to lookup", primary=True, cef_types=["asn"], column_name="ASN"
    )


class PrefixesOutput(IpinfoOutput):
    country: str | None = OutputField(example_values=["US"])
    domain: str | None = OutputField(example_values=["ccselink.com"])
    id: str | None = OutputField(example_values=["AKAMAI"])
    name: str | None = OutputField(example_values=["Akamai Technologies, Inc."])
    netblock: str | None = OutputField(example_values=["104.109.53.0/24"])
    size: str | None = OutputField(example_values=["256"])
    status: str | None = OutputField(example_values=["REASSIGNMENT"])


class Prefixes6Output(IpinfoOutput):
    country: str | None = OutputField(example_values=["US"])
    domain: str | None = OutputField(example_values=["comcast.com"])
    id: str | None = OutputField(example_values=["COMCAST6NET"])
    name: str | None = OutputField(example_values=["Comcast Cable Communications, LLC"])
    netblock: str | None = OutputField(example_values=["2001:558::/29"])
    size: str | None = OutputField(example_values=["633825300114114700748351602688"])
    status: str | None = OutputField(example_values=["ALLOCATION"])


class LookupAsnOutput(IpinfoOutput):
    # Field order sets the widget table column order, matching legacy:
    # ASN, Name, Domain, Registry, Country
    asn: str | None = OutputField(cef_types=["asn"], example_values=["AS7922"])
    name: str | None = OutputField(
        example_values=["Comcast Cable Communications, LLC"], column_name="Name"
    )
    domain: str | None = OutputField(
        cef_types=["domain"], example_values=["comcast.net"], column_name="Domain"
    )
    registry: str | None = OutputField(example_values=["arin"], column_name="Registry")
    country: str | None = OutputField(example_values=["US"], column_name="Country")
    allocated: str | None = OutputField(example_values=["1997-02-14"])
    num_ips: float | None = OutputField(example_values=[71211264])
    type: str | None = OutputField(example_values=["isp"])
    prefixes: list[PrefixesOutput] | None = None
    prefixes6: list[Prefixes6Output] | None = None


class LookupAsnSummary(ActionOutput):
    name: str | None = None
    num_ips: int | None = None


def lookup_asn(
    params: LookupAsnParams, soar: SOARClient, asset: Asset
) -> LookupAsnOutput:
    asn = params.asn.upper()
    if not re.fullmatch(r"AS\d+", asn):
        raise ActionFailure(f"Invalid ASN: {params.asn}. Expected a value like AS15169")

    response = ipinfo_get(asset, f"{asn}/json")

    soar.set_summary(
        LookupAsnSummary(name=response.get("name"), num_ips=response.get("num_ips"))
    )

    return LookupAsnOutput(**response)
