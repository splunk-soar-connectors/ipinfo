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
import json
from typing import Any

from soar_sdk.abstract import SOARClient
from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams, Param

from ..asset import Asset
from ..consts import IPINFO_DEFAULT_TIMEOUT, MAKE_REQUEST_INVALID_ENDPOINT
from ..ipinfo_client import ipinfo_request


class IpinfoMakeRequestParams(MakeRequestParams):
    endpoint: str = Param(
        description=(
            "ipinfo.io endpoint to call, appended to https://ipinfo.io. "
            "Examples: '/8.8.8.8/json', '/AS15169/json', '/me'. "
            "Use POST with '/batch' for batch lookups."
        ),
        required=True,
    )
    verify_ssl: bool = Param(
        description="Whether to verify the SSL certificate.",
        required=False,
        default=True,
    )


def _get_endpoint(endpoint: str) -> str:
    # Only paths are allowed so the asset token is never sent to another host
    endpoint = endpoint.strip()
    if not endpoint or endpoint.startswith(("http://", "https://")):
        raise ActionFailure(MAKE_REQUEST_INVALID_ENDPOINT.format(endpoint=endpoint))
    return endpoint if endpoint.startswith("/") else f"/{endpoint}"


def _get_headers(params: IpinfoMakeRequestParams) -> dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    if not params.headers:
        return headers

    try:
        parsed_headers = json.loads(params.headers)
    except (json.JSONDecodeError, TypeError) as e:
        raise ActionFailure(f"Invalid JSON headers: {params.headers}") from e

    if not isinstance(parsed_headers, dict):
        raise ActionFailure(f"Invalid JSON headers: {params.headers}")

    headers.update(parsed_headers)
    return headers


def _get_query_params(
    params: IpinfoMakeRequestParams,
    endpoint: str,
) -> tuple[str, dict[str, Any] | None]:
    if not params.query_parameters:
        return endpoint, None

    # Accept a JSON object, or a plain query string such as ?a=1&b=2
    try:
        parsed_params = json.loads(params.query_parameters)
    except (json.JSONDecodeError, TypeError):
        query_string = params.query_parameters.lstrip("?")
        separator = "&" if "?" in endpoint else "?"
        return f"{endpoint}{separator}{query_string}", None

    if not isinstance(parsed_params, dict):
        raise ActionFailure(f"Invalid query parameters: {params.query_parameters}")

    return endpoint, parsed_params


def _get_body(params: IpinfoMakeRequestParams, headers: dict[str, str]) -> Any:  # noqa: ANN401
    if not params.body:
        return None

    content_type = headers.get("Content-Type", "").lower()
    if "json" not in content_type:
        return params.body

    try:
        return json.loads(params.body)
    except (json.JSONDecodeError, TypeError) as e:
        raise ActionFailure(f"Invalid JSON body: {params.body}") from e


def make_request(
    params: IpinfoMakeRequestParams, soar: SOARClient, asset: Asset
) -> MakeRequestOutput:
    """
    Make an arbitrary ipinfo.io API request using this asset's token.
    """
    endpoint = _get_endpoint(params.endpoint)
    headers = _get_headers(params)
    endpoint, query_params = _get_query_params(params, endpoint)
    body = _get_body(params, headers)
    timeout = params.timeout or IPINFO_DEFAULT_TIMEOUT

    # HTTP error statuses are returned, not raised, so the caller can inspect them
    response = ipinfo_request(
        asset,
        params.http_method,
        endpoint,
        headers=headers,
        params=query_params,
        json_body=body if isinstance(body, dict | list) else None,
        content=body if isinstance(body, str) else None,
        timeout=timeout,
        verify=params.verify_ssl,
    )

    return MakeRequestOutput(
        status_code=response.status_code,
        response_body=response.text,
    )
