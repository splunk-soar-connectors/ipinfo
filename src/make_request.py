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
import json
from typing import Any
from urllib.parse import urlsplit

import requests
from soar_sdk.action_results import MakeRequestOutput
from soar_sdk.asset import BaseAsset
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams

from .consts import IPINFO_ALLOWED_HOSTS, IPINFO_BASE_URL, IPINFO_DEFAULT_TIMEOUT
from .helper import auth_headers, redact


ENDPOINT_ERROR = (
    "The endpoint must be a path relative to https://ipinfo.io (for example '/batch' or "
    "'/8.8.8.8/city'), or an https URL on ipinfo.io or api.ipinfo.io"
)
# Headers the app controls: credentials always come from the asset.
PROTECTED_HEADERS = {"authorization"}


def _build_url(endpoint: str) -> str:
    endpoint = endpoint.strip()
    if not endpoint or endpoint.startswith("//") or "\\" in endpoint:
        raise ActionFailure(ENDPOINT_ERROR)

    parsed = urlsplit(endpoint)
    url = endpoint if parsed.scheme else f"{IPINFO_BASE_URL}/{endpoint.lstrip('/')}"

    # Never send the asset token anywhere but the IPinfo API hosts.
    target = urlsplit(url)
    try:
        port = target.port
    except ValueError:
        raise ActionFailure(ENDPOINT_ERROR) from None
    if (
        target.scheme != "https"
        or target.hostname not in IPINFO_ALLOWED_HOSTS
        or target.username is not None
        or target.password is not None
        or port not in (None, 443)
    ):
        raise ActionFailure(ENDPOINT_ERROR)
    return url


def _parse_headers(raw: str | None) -> dict[str, str]:
    if not raw:
        return {}
    try:
        headers = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ActionFailure("The headers parameter must be a JSON object") from e
    if not isinstance(headers, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in headers.items()
    ):
        raise ActionFailure(
            "The headers parameter must be a JSON object with string keys and values"
        )
    return {k: v for k, v in headers.items() if k.lower() not in PROTECTED_HEADERS}


def _parse_query(raw: str | None) -> dict[str, Any] | str | None:
    if not raw:
        return None
    try:
        query = json.loads(raw)
    except json.JSONDecodeError:
        query = raw.lstrip("?")
    if isinstance(query, dict):
        if any(str(key).lower() == "token" for key in query):
            raise ActionFailure(
                "Do not pass 'token' in query_parameters; the asset token is sent in the Authorization header"
            )
        return query
    if isinstance(query, str):
        if any(
            part.split("=", 1)[0].strip().lower() == "token"
            for part in query.split("&")
        ):
            raise ActionFailure(
                "Do not pass 'token' in query_parameters; the asset token is sent in the Authorization header"
            )
        return query
    raise ActionFailure(
        "The query_parameters parameter must be a JSON object or a query string"
    )


def make_request(params: MakeRequestParams, asset: BaseAsset) -> MakeRequestOutput:
    """Make an HTTP request to any IPinfo API endpoint using the asset token."""
    url = _build_url(params.endpoint)
    headers = _parse_headers(params.headers)
    query = _parse_query(params.query_parameters)

    timeout = params.timeout if params.timeout is not None else IPINFO_DEFAULT_TIMEOUT
    if timeout <= 0:
        raise ActionFailure("The timeout parameter must be greater than zero")

    request_kwargs: dict[str, Any] = {}
    if params.body:
        try:
            request_kwargs["json"] = json.loads(params.body)
        except json.JSONDecodeError:
            request_kwargs["data"] = params.body

    token = asset.token
    headers.update(auth_headers(token))
    try:
        response = requests.request(
            params.http_method,
            url,
            headers=headers,
            params=query,
            timeout=timeout,
            verify=params.verify_ssl,
            **request_kwargs,
        )
    except Exception as e:
        raise ActionFailure(
            f"Error Connecting to server. Details: {redact(str(e), token)}"
        ) from e

    response_body = redact(response.text, token)
    if response.status_code >= 400:
        raise ActionFailure(
            f"Error from server. Status Code: {response.status_code} Data from server: {response_body}"
        )

    return MakeRequestOutput(
        status_code=response.status_code, response_body=response_body
    )
