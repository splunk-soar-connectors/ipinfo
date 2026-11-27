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
from typing import Any

import httpx
from soar_sdk.exceptions import ActionFailure

from .asset import Asset
from .consts import IPINFO_BASE_URL, IPINFO_DEFAULT_TIMEOUT


def ipinfo_request(
    asset: Asset,
    method: str,
    endpoint: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: Any = None,
    content: str | None = None,
    timeout: float = IPINFO_DEFAULT_TIMEOUT,
    verify: bool = True,
) -> httpx.Response:
    """Send one request to https://ipinfo.io/<endpoint> with the asset's token.

    This is the only place that adds the Authorization header, so every action
    authenticates the same way. Connection errors become ActionFailure; HTTP
    error statuses are returned to the caller to handle.
    """
    request_headers = dict(headers or {})
    if asset.token:
        request_headers["Authorization"] = f"Bearer {asset.token}"

    try:
        return httpx.request(
            method,
            IPINFO_BASE_URL + endpoint.lstrip("/"),
            headers=request_headers,
            params=params,
            json=json_body,
            content=content,
            timeout=timeout,
            verify=verify,
        )
    except httpx.HTTPError as e:
        raise ActionFailure(f"Error connecting to ipinfo.io: {e}") from e


def ipinfo_get(asset: Asset, endpoint: str) -> dict:
    """GET https://ipinfo.io/<endpoint> and return the JSON body, or raise ActionFailure."""
    response = ipinfo_request(asset, "GET", endpoint)

    try:
        body = response.json()
    except ValueError as e:
        raise ActionFailure(
            f"Unable to parse JSON response. Status code: {response.status_code}. Response: {response.text[:500]}"
        ) from e

    if response.is_error or "error" in body:
        raise ActionFailure(
            f"API returned an error. Status code: {response.status_code}. Error: {body.get('error', body)}"
        )

    return body
