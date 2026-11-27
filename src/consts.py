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
IPINFO_BASE_URL = "https://ipinfo.io"
# Hosts the asset token may be sent to. api.ipinfo.io serves IPinfo's newer Lite/Core/Plus APIs.
IPINFO_ALLOWED_HOSTS = frozenset({"ipinfo.io", "api.ipinfo.io"})
IPINFO_DEFAULT_TIMEOUT = 30
IPINFO_TEST_CONNECTIVITY_IP = "8.8.8.8"
IPINFO_BAD_IP_ERROR = (
    "Error: The IP address is a bogon IP. No data for this IP address."
)
IPINFO_INVALID_IP_ERROR = (
    "Please provide a valid IP address in the 'ip' action parameter"
)
IPINFO_INVALID_ASN_ERROR = (
    "Please provide a valid ASN (for example 'AS15169') in the 'asn' action parameter"
)
