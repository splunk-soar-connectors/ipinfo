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
from soar_sdk.models.view import ViewContext

from ..actions.lookup_ip import LookupIpOutput

# The world map in templates/ipinfo_lookup_ip.html is drawn with
# 2 SVG units per degree (equirectangular projection), so a point at
# longitude/latitude sits at x = (lon + 180) * 2, y = (90 - lat) * 2.
MAP_UNITS_PER_DEGREE = 2


def _to_float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except ValueError:
        return None


def display_view(context: ViewContext, outputs: list[LookupIpOutput]) -> dict:
    """Render the lookup ip widget: a world map with a pin per IP, plus a details table."""
    results = []
    for output in outputs:
        lat = _to_float(output.loc.latitude) if output.loc else None
        lon = _to_float(output.loc.longitude) if output.loc else None
        has_location = lat is not None and lon is not None
        results.append(
            {
                "ip": output.ip,
                "city": output.city,
                "region": output.region,
                "country": output.country,
                "org": output.org,
                "latitude": lat,
                "longitude": lon,
                "has_location": has_location,
                "x": (lon + 180) * MAP_UNITS_PER_DEGREE if has_location else None,
                "y": (90 - lat) * MAP_UNITS_PER_DEGREE if has_location else None,
            }
        )

    return {
        "container_id": context.container,
        "results": results,
        "pins": [r for r in results if r["has_location"]],
    }
