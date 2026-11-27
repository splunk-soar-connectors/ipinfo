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

# Used by src/ipinfo_client.py to build every request URL.
IPINFO_BASE_URL = "https://ipinfo.io/"
IPINFO_DEFAULT_TIMEOUT = 30

# Used by src/test_connectivity.py as the lookup that proves the asset works.
TEST_CONNECTIVITY_IP = "8.8.8.8"

# Used by src/actions/lookup_ip.py when ipinfo marks an IP as private/reserved.
IPINFO_BAD_IP_ERROR = (
    "Error: The IP address is a bogon IP. No data for this IP address."
)

# Used by src/actions/make_request.py.
MAKE_REQUEST_INVALID_ENDPOINT = (
    "Invalid endpoint: {endpoint}. Provide an ipinfo.io path such as '/8.8.8.8/json' "
    "or '/me' and do not include the base URL."
)
