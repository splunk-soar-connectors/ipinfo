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
"""Checks the lookup ip map widget: the view handler and the HTML template."""

from typing import Any

import pytest
from soar_sdk.action_results import ActionResult
from soar_sdk.models.view import ViewContext

from src.actions.lookup_ip import LookupIpOutput
from src.app import app
from src.views.lookup_ip import display_view

GOOGLE = {
    "ip": "8.8.8.8",
    "city": "Mountain View",
    "region": "California",
    "country": "US",
    "org": "AS15169 Google LLC",
    "loc": {"latitude": "37.4056", "longitude": "-122.0775"},
}
NO_LOCATION = {"ip": "203.0.113.9"}


def _context() -> ViewContext:
    return ViewContext(
        QS={}, container=123, app=456, no_connection=False, google_maps_key=False
    )


def test_view_handler_turns_location_into_map_pins() -> None:
    # Call the view function itself (without the SDK wrapper), like OneDrive's view test
    template_context = display_view.__wrapped__(_context(), [LookupIpOutput(**GOOGLE)])

    assert template_context["container_id"] == 123
    result = template_context["results"][0]
    assert result["ip"] == "8.8.8.8"
    assert result["city"] == "Mountain View"
    assert result["has_location"] is True
    # x = (lon + 180) * 2, y = (90 - lat) * 2
    assert result["x"] == pytest.approx((-122.0775 + 180) * 2)
    assert result["y"] == pytest.approx((90 - 37.4056) * 2)
    assert template_context["pins"] == [result]


def test_view_handler_keeps_rows_without_location_out_of_the_pins() -> None:
    template_context = display_view.__wrapped__(
        _context(), [LookupIpOutput(**GOOGLE), LookupIpOutput(**NO_LOCATION)]
    )

    assert len(template_context["results"]) == 2
    assert template_context["results"][1]["has_location"] is False
    assert template_context["results"][1]["x"] is None
    assert [pin["ip"] for pin in template_context["pins"]] == ["8.8.8.8"]


def _render_like_soar(rows: list[dict[str, Any]]) -> str:
    """Render the widget the way SOAR does: through the SDK wrapper, from stored results."""
    action = app.actions_manager.get_action("lookup_ip")
    runs = []
    for row in rows:
        result = ActionResult(status=True, message="", param={"ip": row["ip"]})
        # SOAR stores every output field, missing ones as None
        result.add_data(LookupIpOutput(**row).model_dump(by_alias=True))
        runs.append(({"total_objects": 1, "total_objects_successful": 1}, [result]))
    context = {
        "QS": {},
        "container": 123,
        "app": 456,
        "no_connection": False,
        "google_maps_key": False,
    }
    return action.meta.view_handler("lookup_ip", runs, context)


def test_template_renders_map_and_table() -> None:
    html = _render_like_soar([GOOGLE])

    assert "Rendering Failed" not in html
    assert "Error in view" not in html
    assert "<svg" in html
    assert "8.8.8.8" in html
    assert "Mountain View" in html


def test_template_renders_when_fields_are_missing() -> None:
    # Regression: on the lab box the view failed with "Data parsing failed"
    # when stored results had None for fields ipinfo did not return
    html = _render_like_soar([GOOGLE, NO_LOCATION])

    assert "Rendering Failed" not in html
    assert "Data parsing failed" not in html
    assert "203.0.113.9" in html
