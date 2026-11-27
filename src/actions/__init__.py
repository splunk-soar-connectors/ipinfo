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
from soar_sdk.app import App

from .lookup_asn import LookupAsnSummary, lookup_asn
from .lookup_ip import LookupIpSummary, lookup_ip
from .make_request import make_request
from ..views.lookup_ip import display_view as display_lookup_ip_view


def register_actions(app: App) -> App:
    """Register every IPinfo action on the given app and return it."""
    app.make_request()(make_request)
    app.register_action(
        action=lookup_ip,
        description="Lookup the details of an IP address",
        action_type="investigate",
        read_only=True,
        summary_type=LookupIpSummary,
        view_handler=display_lookup_ip_view,
        view_template="ipinfo_lookup_ip.html",
    )
    app.register_action(
        action=lookup_asn,
        description="Lookup the details of an Autonomous System Number",
        action_type="investigate",
        read_only=True,
        summary_type=LookupAsnSummary,
        render_as="table",
    )
    return app
