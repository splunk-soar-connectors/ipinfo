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
"""Checks how the actions are registered, which is what ends up in manifest.json."""

from src.app import app


def test_app_has_the_legacy_actions_plus_make_request() -> None:
    assert set(app.actions_manager.get_actions()) == {
        "test_connectivity",
        "lookup_ip",
        "lookup_asn",
        "make_request",
    }


def test_lookup_ip_uses_the_custom_map_view() -> None:
    action = app.actions_manager.get_action("lookup_ip")

    assert action.meta.render_as == "custom"
    assert action.meta.view_handler is not None
    assert action.meta.read_only is True
    assert action.meta.type == "investigate"


def test_lookup_asn_uses_a_table_widget() -> None:
    action = app.actions_manager.get_action("lookup_asn")

    assert action.meta.render_as == "table"
    assert action.meta.read_only is True
    assert action.meta.type == "investigate"


def test_make_request_is_a_generic_action() -> None:
    action = app.actions_manager.get_action("make_request")

    assert action.meta.action == "make request"
    assert action.meta.type == "generic"
    assert action.meta.read_only is False


def test_asset_token_is_sensitive() -> None:
    token_field = app.asset_cls.model_fields["token"]

    assert token_field.json_schema_extra["sensitive"] is True


def test_lookup_ip_accepts_ipv4_and_ipv6() -> None:
    # Legacy registered its own validator that accepted IPv6. Without "ipv6" here,
    # SOAR rejects addresses like 2001:4860:4860::8888 before the action runs
    # (app-tests lookup_ip_IPv6_000)
    action = app.actions_manager.get_action("lookup_ip")
    ip_param = action.meta.parameters._to_json_schema()["ip"]

    assert ip_param["contains"] == ["ip", "ipv6"]
