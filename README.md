# IPinfo

Publisher: Splunk <br>
Connector Version: 2.0.6 <br>
Product Vendor: ipinfo.io <br>
Product Name: ipinfo.io <br>
Minimum Product Version: 7.0.0

Uses ipinfo.io to lookup IP addresses and Autonomous System Numbers

### Configuration variables

This table lists the configuration variables required to operate IPinfo. These variables are specified when configuring a ipinfo.io asset in Splunk SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** | optional | password | IPinfo API token |

### Supported Actions

[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration. <br>
[lookup ip](#action-lookup-ip) - Lookup the details of an IP address <br>
[lookup asn](#action-lookup-asn) - Lookup the details of an Autonomous System Number <br>
[make request](#action-make-request) - Make an HTTP request to any IPinfo API endpoint using the asset token.

## action: 'test connectivity'

Validate the asset configuration for connectivity using supplied configuration.

Type: **test** <br>
Read only: **True**

Basic test for app.

#### Action Parameters

No parameters are required for this action

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'lookup ip'

Lookup the details of an IP address

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**ip** | required | IP to lookup | string | `ip` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.ip | string | `ip` | |
action_result.data.\*.status | string | | success failed |
action_result.data.\*.anycast | boolean | | True False |
action_result.data.\*.asn.asn | string | `asn` | AS15169 |
action_result.data.\*.asn.domain | string | `domain` | google.com |
action_result.data.\*.asn.name | string | | Google LLC |
action_result.data.\*.asn.route | string | | 8.8.8.0/24 |
action_result.data.\*.asn.type | string | | hosting |
action_result.data.\*.carrier.mcc | string | | 310 |
action_result.data.\*.carrier.mnc | string | | 150 |
action_result.data.\*.carrier.name | string | | AT&T |
action_result.data.\*.city | string | | Mountain View |
action_result.data.\*.company.domain | string | `domain` | google.com |
action_result.data.\*.company.name | string | | Google LLC |
action_result.data.\*.company.type | string | | hosting |
action_result.data.\*.country | string | | US |
action_result.data.\*.hostname | string | `host name` | google-public-dns-a.google.com |
action_result.data.\*.ip | string | `ip` | 8.8.8.8 |
action_result.data.\*.loc.latitude | string | | 37.3860 |
action_result.data.\*.loc.longitude | string | | -122.0840 |
action_result.data.\*.org | string | | AS15169 Google LLC |
action_result.data.\*.phone | string | | 650 |
action_result.data.\*.postal | string | | 94035 |
action_result.data.\*.readme | string | | https://ipinfo.io/missingauth |
action_result.data.\*.region | string | | California |
action_result.data.\*.timezone | string | | America/Los_Angeles |
action_result.summary.city | string | | Mountain View |
action_result.summary.region | string | | California |
action_result.summary.country | string | | US |
action_result.summary.company_domain | string | `domain` | google.com |
action_result.summary.company_name | string | | Google LLC |
action_result.summary.company_type | string | | hosting |
action_result.summary.carrier_name | string | | AT&T |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'lookup asn'

Lookup the details of an Autonomous System Number

Type: **investigate** <br>
Read only: **True**

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**asn** | required | ASN to lookup | string | `asn` |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.asn | string | `asn` | |
action_result.data.\*.status | string | | success failed |
action_result.data.\*.name | string | | Comcast Cable Communications, LLC |
action_result.data.\*.domain | string | `domain` | comcast.net |
action_result.data.\*.registry | string | | arin |
action_result.data.\*.country | string | | US |
action_result.data.\*.allocated | string | | 1997-02-14 |
action_result.data.\*.asn | string | `asn` | AS7922 |
action_result.data.\*.num_ips | numeric | | 71211264 |
action_result.data.\*.prefixes.\*.country | string | | US |
action_result.data.\*.prefixes.\*.domain | string | | ccselink.com |
action_result.data.\*.prefixes.\*.id | string | | AKAMAI |
action_result.data.\*.prefixes.\*.name | string | | Akamai Technologies, Inc. |
action_result.data.\*.prefixes.\*.netblock | string | | 104.109.53.0/24 |
action_result.data.\*.prefixes.\*.size | string | | 256 |
action_result.data.\*.prefixes.\*.status | string | | REASSIGNMENT |
action_result.data.\*.prefixes6.\*.country | string | | US |
action_result.data.\*.prefixes6.\*.domain | string | | comcast.com |
action_result.data.\*.prefixes6.\*.id | string | | COMCAST6NET |
action_result.data.\*.prefixes6.\*.name | string | | Comcast Cable Communications, LLC |
action_result.data.\*.prefixes6.\*.netblock | string | | 2001:558::/29 |
action_result.data.\*.prefixes6.\*.size | string | | 633825300114114700748351602688 |
action_result.data.\*.prefixes6.\*.status | string | | ALLOCATION |
action_result.data.\*.type | string | | isp |
action_result.summary.name | string | | Comcast Cable Communications, LLC |
action_result.summary.num_ips | numeric | | 71211264 |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

## action: 'make request'

Make an HTTP request to any IPinfo API endpoint using the asset token.

Type: **generic** <br>
Read only: **False**

'make request' action for the app. Used to handle arbitrary HTTP requests with the app's asset

#### Action Parameters

PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**http_method** | required | The HTTP method to use for the request. | string | |
**endpoint** | required | The endpoint to send the request to. | string | |
**headers** | optional | The headers to send with the request (JSON object). An example is {'Content-Type': 'application/json'} | string | |
**query_parameters** | optional | Parameters to append to the URL (JSON object or query string). An example is ?key=value&key2=value2 | string | |
**body** | optional | The body to send with the request (JSON object). An example is {'key': 'value', 'key2': 'value2'} | string | |
**timeout** | optional | The timeout for the request in seconds. | numeric | |
**verify_ssl** | optional | Whether to verify the SSL certificate. Default is True. | boolean | |

#### Action Output

DATA PATH | TYPE | CONTAINS | EXAMPLE VALUES
--------- | ---- | -------- | --------------
action_result.status | string | | success failure |
action_result.message | string | | |
action_result.parameter.http_method | string | | |
action_result.parameter.endpoint | string | | |
action_result.parameter.headers | string | | |
action_result.parameter.query_parameters | string | | |
action_result.parameter.body | string | | |
action_result.parameter.timeout | numeric | | |
action_result.parameter.verify_ssl | boolean | | |
action_result.data.\*.status_code | numeric | | 200 404 500 |
action_result.data.\*.response_body | string | | {"key": "value"} |
summary.total_objects | numeric | | 1 |
summary.total_objects_successful | numeric | | 1 |

______________________________________________________________________

Auto-generated Splunk SOAR Connector documentation.

Copyright 2026 Splunk Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and limitations under the License.
