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
from unittest.mock import MagicMock

import pytest
import requests
from soar_sdk.exceptions import ActionFailure
from soar_sdk.params import MakeRequestParams

from src import app as ipinfo_app, helper, make_request as make_request_module


IP_RESPONSE = {
    "ip": "8.8.8.8",
    "hostname": "dns.google",
    "anycast": True,
    "city": "Mountain View",
    "region": "California",
    "country": "US",
    "loc": "37.4056,-122.0775",
    "org": "AS15169 Google LLC",
    "postal": 94043,
    "timezone": "America/Los_Angeles",
    "asn": {"asn": "AS15169", "name": "Google LLC", "domain": "google.com"},
    "company": {"name": "Google LLC", "domain": "google.com", "type": "hosting"},
    "privacy": {"vpn": False, "proxy": False},
    "domains": {"total": 2, "domains": ["a.com", "b.com"]},
}

ASN_RESPONSE = {
    "asn": "AS7922",
    "name": "Comcast Cable Communications, LLC",
    "country": "US",
    "allocated": "1997-02-14",
    "registry": "arin",
    "domain": "comcast.net",
    "num_ips": 71211264,
    "type": "isp",
    "prefixes": [{"netblock": "104.109.53.0/24", "size": 256, "status": "ASSIGNED"}],
    "prefixes6": [],
    "peers": ["1299", "174"],
}


def _response(
    status_code=200, content_type="application/json", json_body=None, text=None
):
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.headers = {"Content-Type": content_type} if content_type else {}
    response.text = (
        text if text is not None else ("{}" if json_body is None else str(json_body))
    )
    if isinstance(json_body, Exception):
        response.json.side_effect = json_body
    else:
        response.json.return_value = json_body
    return response


@pytest.fixture
def asset():
    return ipinfo_app.Asset(token="secret-token")


@pytest.fixture
def soar():
    return MagicMock()


# helper


def test_process_json_success():
    assert helper.process_response(_response(json_body={"a": 1})) == {"a": 1}


@pytest.mark.parametrize(
    ("response", "match"),
    [
        (
            _response(status_code=429, json_body={"status": 429}, text="rate limited"),
            "Status Code: 429 Data from server: rate limited",
        ),
        (
            _response(json_body={"error": {"title": "Wrong ip", "message": "x"}}),
            "API returned an error. Error: .*Wrong ip",
        ),
        (_response(json_body=ValueError("bad")), "Unable to parse JSON response"),
        (_response(json_body=[1, 2]), "expected an object, got list"),
        (
            _response(
                content_type="text/html",
                text="<html><script>x</script><p>Bad gateway</p></html>",
                status_code=502,
            ),
            "Bad gateway",
        ),
        (
            _response(content_type="text/plain", text="oops", status_code=500),
            "Can't process response",
        ),
        (_response(status_code=500, content_type=None, text=""), "Empty response"),
    ],
)
def test_process_response_errors(response, match):
    with pytest.raises(ActionFailure, match=match):
        helper.process_response(response)


def test_process_empty_200():
    assert helper.process_response(_response(content_type=None, text="")) == {}


def test_make_rest_call_sends_token_as_header(mocker):
    get = mocker.patch.object(
        helper.requests, "get", return_value=_response(json_body={"ip": "8.8.8.8"})
    )
    helper.make_rest_call("secret-token", "8.8.8.8/json")
    get.assert_called_once_with(
        "https://ipinfo.io/8.8.8.8/json",
        headers={"Authorization": "Bearer secret-token"},
        timeout=30,
    )


def test_make_rest_call_without_token(mocker):
    get = mocker.patch.object(
        helper.requests, "get", return_value=_response(json_body={})
    )
    helper.make_rest_call(None, "AS15169/json")
    assert get.call_args.kwargs["headers"] == {}


def test_make_rest_call_redacts_token(mocker):
    mocker.patch.object(
        helper.requests,
        "get",
        return_value=_response(
            status_code=403, json_body={}, text="bad token secret-token"
        ),
    )
    with pytest.raises(ActionFailure) as exc:
        helper.make_rest_call("secret-token", "8.8.8.8/json")
    assert "secret-token" not in str(exc.value)
    assert "[REDACTED]" in str(exc.value)


def test_make_rest_call_connection_error(mocker):
    mocker.patch.object(
        helper.requests, "get", side_effect=requests.ConnectionError("boom")
    )
    with pytest.raises(
        ActionFailure, match=r"Error Connecting to server\. Details: boom"
    ):
        helper.make_rest_call(None, "8.8.8.8/json")


def test_summary_message():
    assert (
        helper.summary_message({"num_ips": 5, "name": "Comcast", "skip": None})
        == "Num ips: 5, Name: Comcast"
    )


# test connectivity


def test_test_connectivity_success(mocker, soar, asset):
    call = mocker.patch.object(ipinfo_app, "make_rest_call", return_value=IP_RESPONSE)
    ipinfo_app.test_connectivity.__wrapped__(soar, asset)
    call.assert_called_once_with("secret-token", "8.8.8.8/json")


def test_test_connectivity_failure(mocker, soar, asset):
    mocker.patch.object(ipinfo_app, "make_rest_call", side_effect=ActionFailure("nope"))
    with pytest.raises(ActionFailure, match="nope"):
        ipinfo_app.test_connectivity.__wrapped__(soar, asset)


# lookup ip


def test_lookup_ip(mocker, soar, asset):
    call = mocker.patch.object(
        ipinfo_app, "make_rest_call", return_value=dict(IP_RESPONSE)
    )
    params = ipinfo_app.LookupIpParams(ip="8.8.8.8")

    result = ipinfo_app.lookup_ip.__wrapped__(params, soar=soar, asset=asset)

    call.assert_called_once_with("secret-token", "8.8.8.8/json")
    assert result.status == "success"
    assert result.loc.latitude == "37.4056"
    assert result.loc.longitude == "-122.0775"
    assert result.postal == "94043"
    assert result.company.type == "hosting"
    dumped = result.model_dump()
    assert dumped["privacy"] == {"vpn": False, "proxy": False}
    assert dumped["domains"]["total"] == 2

    summary = soar.set_summary.call_args.args[0]
    assert summary.city == "Mountain View"
    assert summary.company_name == "Google LLC"
    assert summary.carrier_name is None
    soar.set_message.assert_called_once_with(
        "City: Mountain View, Region: California, Country: US, "
        "Company domain: google.com, Company name: Google LLC, Company type: hosting"
    )


def test_lookup_ip_minimal_response(mocker, soar, asset):
    mocker.patch.object(
        ipinfo_app,
        "make_rest_call",
        return_value={"ip": "2001:4860:4860::8888", "carrier": {"name": "AT&T"}},
    )
    params = ipinfo_app.LookupIpParams(ip="2001:4860:4860::8888")

    result = ipinfo_app.lookup_ip.__wrapped__(params, soar=soar, asset=asset)

    assert result.loc is None
    assert result.carrier.name == "AT&T"
    soar.set_message.assert_called_once_with("Carrier name: AT&T")


def test_lookup_ip_bogon(mocker, soar, asset):
    mocker.patch.object(
        ipinfo_app, "make_rest_call", return_value={"ip": "10.0.0.1", "bogon": True}
    )
    with pytest.raises(ActionFailure, match="bogon IP"):
        ipinfo_app.lookup_ip.__wrapped__(
            ipinfo_app.LookupIpParams(ip="10.0.0.1"), soar=soar, asset=asset
        )


@pytest.mark.parametrize("value", ["not-an-ip", "8.8.8.8/json", "../me", "8.8.8.8 "])
def test_lookup_ip_invalid(mocker, soar, asset, value):
    call = mocker.patch.object(ipinfo_app, "make_rest_call")
    with pytest.raises(ActionFailure, match="valid IP address"):
        ipinfo_app.lookup_ip.__wrapped__(
            ipinfo_app.LookupIpParams(ip=value), soar=soar, asset=asset
        )
    call.assert_not_called()


# lookup asn


def test_lookup_asn(mocker, soar, asset):
    call = mocker.patch.object(
        ipinfo_app, "make_rest_call", return_value=dict(ASN_RESPONSE)
    )
    params = ipinfo_app.LookupAsnParams(asn="as7922")

    result = ipinfo_app.lookup_asn.__wrapped__(params, soar=soar, asset=asset)

    call.assert_called_once_with("secret-token", "AS7922/json")
    assert result.status == "success"
    assert result.registry == "arin"
    assert result.prefixes[0].size == "256"
    assert result.model_dump()["peers"] == ["1299", "174"]
    summary = soar.set_summary.call_args.args[0]
    assert summary.num_ips == 71211264
    soar.set_message.assert_called_once_with(
        "Name: Comcast Cable Communications, LLC, Num ips: 71211264"
    )


@pytest.mark.parametrize("value", ["7922", "AS", "AS79x", "AS7922/json", "AS7922\n"])
def test_lookup_asn_invalid(mocker, soar, asset, value):
    call = mocker.patch.object(ipinfo_app, "make_rest_call")
    with pytest.raises(ActionFailure, match="valid ASN"):
        ipinfo_app.lookup_asn.__wrapped__(
            ipinfo_app.LookupAsnParams(asn=value), soar=soar, asset=asset
        )
    call.assert_not_called()


def test_lookup_asn_through_sdk_wrapper(mocker, asset):
    """Run the registered action through the SDK wrapper to check result adaptation."""
    mocker.patch.object(ipinfo_app, "make_rest_call", return_value=dict(ASN_RESPONSE))
    actions_manager = ipinfo_app.app.actions_manager
    mocker.patch.object(
        ipinfo_app.app,
        "_build_magic_args",
        side_effect=lambda fn, soar, **kw: {"soar": soar, "asset": asset},
    )
    added = mocker.patch.object(actions_manager, "add_result")

    status = ipinfo_app.lookup_asn(ipinfo_app.LookupAsnParams(asn="AS7922"))

    assert status is True
    result = added.call_args.args[0]
    data = result.get_data()[0]
    assert data["status"] == "success"
    assert data["name"] == "Comcast Cable Communications, LLC"
    assert data["peers"] == ["1299", "174"]
    assert result.get_summary()["num_ips"] == 71211264


def test_lookup_ip_through_sdk_wrapper(mocker, asset):
    mocker.patch.object(ipinfo_app, "make_rest_call", return_value=dict(IP_RESPONSE))
    actions_manager = ipinfo_app.app.actions_manager
    mocker.patch.object(
        ipinfo_app.app,
        "_build_magic_args",
        side_effect=lambda fn, soar, **kw: {"soar": soar, "asset": asset},
    )
    added = mocker.patch.object(actions_manager, "add_result")

    status = ipinfo_app.lookup_ip(ipinfo_app.LookupIpParams(ip="8.8.8.8"))

    assert status is True
    result = added.call_args.args[0]
    data = result.get_data()[0]
    assert data["loc"] == {"latitude": "37.4056", "longitude": "-122.0775"}
    assert data["privacy"] == {"vpn": False, "proxy": False}
    assert result.get_summary()["city"] == "Mountain View"


# make request


def _mr_params(**kwargs):
    kwargs.setdefault("http_method", "GET")
    return MakeRequestParams(**kwargs)


def test_make_request_relative_endpoint(mocker, asset):
    req = mocker.patch.object(
        make_request_module.requests,
        "request",
        return_value=_response(text='{"total": 1}'),
    )
    out = make_request_module.make_request(
        _mr_params(
            endpoint="/ranges/comcast.net",
            headers='{"Accept": "application/json", "Authorization": "Bearer evil"}',
            query_parameters='{"limit": 1}',
        ),
        asset,
    )
    assert out.status_code == 200
    assert out.response_body == '{"total": 1}'
    args, kwargs = req.call_args
    assert args == ("GET", "https://ipinfo.io/ranges/comcast.net")
    assert kwargs["headers"] == {
        "Accept": "application/json",
        "Authorization": "Bearer secret-token",
    }
    assert kwargs["params"] == {"limit": 1}
    assert kwargs["timeout"] == 30


def test_make_request_batch_post_json_body(mocker, asset):
    req = mocker.patch.object(
        make_request_module.requests, "request", return_value=_response(text="{}")
    )
    make_request_module.make_request(
        _mr_params(http_method="POST", endpoint="batch", body='["8.8.8.8/country"]'),
        asset,
    )
    assert req.call_args.args == ("POST", "https://ipinfo.io/batch")
    assert req.call_args.kwargs["json"] == ["8.8.8.8/country"]


def test_make_request_api_host_absolute_url(mocker, asset):
    req = mocker.patch.object(
        make_request_module.requests, "request", return_value=_response(text="{}")
    )
    make_request_module.make_request(
        _mr_params(endpoint="https://api.ipinfo.io/lite/8.8.8.8"), asset
    )
    assert req.call_args.args == ("GET", "https://api.ipinfo.io/lite/8.8.8.8")


@pytest.mark.parametrize(
    "endpoint",
    [
        "",
        "https://evil.example.com/8.8.8.8",
        "http://ipinfo.io/8.8.8.8",
        "//evil.example.com/x",
        "https://ipinfo.io.evil.com/x",
        "https://user@ipinfo.io/x",
        "https://ipinfo.io:8443/x",
        "ftp://ipinfo.io/x",
        "\\\\evil.example.com/x",
    ],
)
def test_make_request_rejects_foreign_hosts(mocker, asset, endpoint):
    req = mocker.patch.object(make_request_module.requests, "request")
    with pytest.raises(ActionFailure, match="endpoint must be"):
        make_request_module.make_request(_mr_params(endpoint=endpoint), asset)
    req.assert_not_called()


@pytest.mark.parametrize("query", ['{"token": "x"}', "?a=1&token=x", "TOKEN=x"])
def test_make_request_rejects_token_query(mocker, asset, query):
    req = mocker.patch.object(make_request_module.requests, "request")
    with pytest.raises(ActionFailure, match="Authorization header"):
        make_request_module.make_request(
            _mr_params(endpoint="/me", query_parameters=query), asset
        )
    req.assert_not_called()


def test_make_request_query_string(mocker, asset):
    req = mocker.patch.object(
        make_request_module.requests, "request", return_value=_response(text="x")
    )
    make_request_module.make_request(
        _mr_params(endpoint="/8.8.8.8/city", query_parameters="?a=1"), asset
    )
    assert req.call_args.kwargs["params"] == "a=1"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"headers": "not json"}, "must be a JSON object"),
        ({"headers": '{"a": 1}'}, "string keys and values"),
        ({"query_parameters": "[1]"}, "JSON object or a query string"),
        ({"timeout": 0}, "greater than zero"),
    ],
)
def test_make_request_invalid_params(mocker, asset, kwargs, match):
    req = mocker.patch.object(make_request_module.requests, "request")
    with pytest.raises(ActionFailure, match=match):
        make_request_module.make_request(_mr_params(endpoint="/me", **kwargs), asset)
    req.assert_not_called()


def test_make_request_error_status_redacts_token(mocker, asset):
    mocker.patch.object(
        make_request_module.requests,
        "request",
        return_value=_response(status_code=403, text="token secret-token is invalid"),
    )
    with pytest.raises(ActionFailure, match="Status Code: 403") as exc:
        make_request_module.make_request(_mr_params(endpoint="/me"), asset)
    assert "secret-token" not in str(exc.value)


def test_make_request_connection_error(mocker, asset):
    mocker.patch.object(
        make_request_module.requests,
        "request",
        side_effect=requests.ConnectionError("boom secret-token"),
    )
    with pytest.raises(ActionFailure, match="Error Connecting") as exc:
        make_request_module.make_request(_mr_params(endpoint="/me"), asset)
    assert "secret-token" not in str(exc.value)


def test_make_request_without_token(mocker):
    req = mocker.patch.object(
        make_request_module.requests, "request", return_value=_response(text="{}")
    )
    make_request_module.make_request(
        _mr_params(endpoint="/8.8.8.8/json"), ipinfo_app.Asset()
    )
    assert "Authorization" not in req.call_args.kwargs["headers"]
