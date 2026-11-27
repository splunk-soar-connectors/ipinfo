**Unreleased**

* Converted the app to the Splunk SOAR SDK (Python 3.13+)
* The minimum supported SOAR version is now 7.0.0
* New 'make request' action to call any IPinfo API endpoint (for example /batch, /me, /ranges, /domains, single-field lookups and api.ipinfo.io) with the asset token
* lookup ip: results now render as a table (IP, Status) because the SDK does not support the legacy map widget
* lookup ip and lookup asn: the Status table column is now read from action_result.data.\*.status
* lookup ip and lookup asn: requests to IPinfo now time out after 30 seconds
