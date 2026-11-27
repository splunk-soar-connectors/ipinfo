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
from soar_sdk.abstract import SOARClient
from soar_sdk.logging import getLogger

from .asset import Asset
from .consts import TEST_CONNECTIVITY_IP
from .ipinfo_client import ipinfo_get

logger = getLogger()


def run_test_connectivity(soar: SOARClient, asset: Asset) -> None:
    logger.progress("Connecting to endpoint")
    ipinfo_get(asset, f"{TEST_CONNECTIVITY_IP}/json")
    logger.progress("Test Connectivity Passed")
