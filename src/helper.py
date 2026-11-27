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
from typing import Any

import requests
from bs4 import BeautifulSoup
from soar_sdk.exceptions import ActionFailure

from .consts import IPINFO_BASE_URL, IPINFO_DEFAULT_TIMEOUT


def redact(text: str, secret: str | None) -> str:
    """Remove the asset token from text that may be shown to the user."""
    return text.replace(secret, "[REDACTED]") if secret else text


def auth_headers(token: str | None) -> dict[str, str]:
    """Send the token as a bearer header so it never appears in a request URL."""
    return {"Authorization": f"Bearer {token}"} if token else {}


def summary_message(summary: dict[str, Any]) -> str:
    """Build the result message the way the legacy platform derived it from the summary."""
    return ", ".join(
        f"{key.replace('_', ' ').capitalize()}: {value}"
        for key, value in summary.items()
        if value is not None
    )


def _process_empty_response(response: requests.Response) -> dict[str, Any]:
    if response.status_code == 200:
        return {}
    raise ActionFailure("Empty response and no information in the header")


def _process_html_response(response: requests.Response) -> dict[str, Any]:
    # An HTML response is treated as an error (often a proxy in between SOAR and IPinfo)
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        for element in soup(["script", "style", "footer", "nav"]):
            element.extract()
        split_lines = [line.strip() for line in soup.text.split("\n") if line.strip()]
        error_text = "\n".join(split_lines)
    except Exception:
        error_text = "Cannot parse error details"

    raise ActionFailure(
        f"Status Code: {response.status_code}. Data from server:\n{error_text}\n"
    )


def _process_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        resp_json = response.json()
    except Exception as e:
        raise ActionFailure(f"Unable to parse JSON response. Error: {e!s}") from e

    if 200 <= response.status_code < 399:
        if not isinstance(resp_json, dict):
            raise ActionFailure(
                f"Unexpected JSON response from server: expected an object, got {type(resp_json).__name__}"
            )
        if "error" in resp_json:
            raise ActionFailure(f"API returned an error. Error: {resp_json['error']}")
        return resp_json

    raise ActionFailure(
        f"Error from server. Status Code: {response.status_code} Data from server: {response.text}"
    )


def process_response(response: requests.Response) -> dict[str, Any]:
    """Convert an IPinfo HTTP response to a JSON dict, raising ActionFailure on any error."""
    content_type = response.headers.get("Content-Type", "")

    if "json" in content_type:
        return _process_json_response(response)

    if "html" in content_type:
        return _process_html_response(response)

    if not response.text:
        return _process_empty_response(response)

    raise ActionFailure(
        f"Can't process response from server. Status Code: {response.status_code} Data from server: {response.text}"
    )


def make_rest_call(token: str | None, endpoint: str) -> dict[str, Any]:
    """Make a GET request to the IPinfo API and return the parsed JSON body."""
    url = f"{IPINFO_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(
            url, headers=auth_headers(token), timeout=IPINFO_DEFAULT_TIMEOUT
        )
    except Exception as e:
        raise ActionFailure(
            f"Error Connecting to server. Details: {redact(str(e), token)}"
        ) from e

    try:
        return process_response(response)
    except ActionFailure as e:
        raise ActionFailure(redact(e.message, token)) from None
