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
from pydantic import ConfigDict
from soar_sdk.action_results import ActionOutput


class IpinfoOutput(ActionOutput):
    """Base for outputs built from ipinfo.io responses.

    Legacy stored the whole ipinfo response, so playbooks may read fields that are
    not declared here, such as privacy.vpn or abuse.email on paid plans. Keep
    undeclared fields instead of dropping them.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")
