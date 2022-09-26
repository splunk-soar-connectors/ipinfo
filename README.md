[comment]: # "Auto-generated SOAR connector documentation"
# IPinfo

Publisher: Splunk  
Connector Version: 2\.0\.1  
Product Vendor: ipinfo\.io  
Product Name: ipinfo\.io  
Product Version Supported (regex): "\.\*"  
Minimum Product Version: 5\.3\.3  

Uses ipinfo\.io to lookup IP addresses and Autonomous System Numbers

### Configuration Variables
The below configuration variables are required for this Connector to operate.  These variables are specified when configuring a ipinfo\.io asset in SOAR.

VARIABLE | REQUIRED | TYPE | DESCRIPTION
-------- | -------- | ---- | -----------
**token** |  optional  | password | IPinfo API token

### Supported Actions  
[test connectivity](#action-test-connectivity) - Validate the asset configuration for connectivity using supplied configuration  
[lookup ip](#action-lookup-ip) - Lookup the details of an IP address  
[lookup asn](#action-lookup-asn) - Lookup the details of an Autonomous System Number  

## action: 'test connectivity'
Validate the asset configuration for connectivity using supplied configuration

Type: **test**  
Read only: **True**

#### Action Parameters
No parameters are required for this action

#### Action Output
No Output  

## action: 'lookup ip'
Lookup the details of an IP address

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**ip** |  required  | IP to lookup | string |  `ip` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.ip | string |  `ip` 
action\_result\.data\.\*\.anycast | boolean | 
action\_result\.data\.\*\.asn\.asn | string |  `asn` 
action\_result\.data\.\*\.asn\.domain | string |  `domain` 
action\_result\.data\.\*\.asn\.name | string | 
action\_result\.data\.\*\.asn\.route | string | 
action\_result\.data\.\*\.asn\.type | string | 
action\_result\.data\.\*\.carrier\.mcc | string | 
action\_result\.data\.\*\.carrier\.mnc | string | 
action\_result\.data\.\*\.carrier\.name | string | 
action\_result\.data\.\*\.city | string | 
action\_result\.data\.\*\.company\.domain | string |  `domain` 
action\_result\.data\.\*\.company\.name | string | 
action\_result\.data\.\*\.company\.type | string | 
action\_result\.data\.\*\.country | string | 
action\_result\.data\.\*\.hostname | string |  `host name` 
action\_result\.data\.\*\.ip | string |  `ip` 
action\_result\.data\.\*\.loc\.latitude | string | 
action\_result\.data\.\*\.loc\.longitude | string | 
action\_result\.data\.\*\.org | string | 
action\_result\.data\.\*\.phone | string | 
action\_result\.data\.\*\.postal | string | 
action\_result\.data\.\*\.readme | string | 
action\_result\.data\.\*\.region | string | 
action\_result\.data\.\*\.timezone | string | 
action\_result\.summary\.carrier\_name | string | 
action\_result\.summary\.city | string | 
action\_result\.summary\.company\_domain | string |  `domain` 
action\_result\.summary\.company\_name | string | 
action\_result\.summary\.company\_type | string | 
action\_result\.summary\.country | string | 
action\_result\.summary\.region | string | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric |   

## action: 'lookup asn'
Lookup the details of an Autonomous System Number

Type: **investigate**  
Read only: **True**

#### Action Parameters
PARAMETER | REQUIRED | DESCRIPTION | TYPE | CONTAINS
--------- | -------- | ----------- | ---- | --------
**asn** |  required  | ASN to lookup | string |  `asn` 

#### Action Output
DATA PATH | TYPE | CONTAINS
--------- | ---- | --------
action\_result\.status | string | 
action\_result\.parameter\.asn | string |  `asn` 
action\_result\.data\.\*\.allocated | string | 
action\_result\.data\.\*\.asn | string |  `asn` 
action\_result\.data\.\*\.country | string | 
action\_result\.data\.\*\.domain | string |  `domain` 
action\_result\.data\.\*\.name | string | 
action\_result\.data\.\*\.num\_ips | numeric | 
action\_result\.data\.\*\.prefixes\.\*\.country | string | 
action\_result\.data\.\*\.prefixes\.\*\.domain | string | 
action\_result\.data\.\*\.prefixes\.\*\.id | string | 
action\_result\.data\.\*\.prefixes\.\*\.name | string | 
action\_result\.data\.\*\.prefixes\.\*\.netblock | string | 
action\_result\.data\.\*\.prefixes\.\*\.size | string | 
action\_result\.data\.\*\.prefixes\.\*\.status | string | 
action\_result\.data\.\*\.prefixes6\.\*\.country | string | 
action\_result\.data\.\*\.prefixes6\.\*\.domain | string | 
action\_result\.data\.\*\.prefixes6\.\*\.id | string | 
action\_result\.data\.\*\.prefixes6\.\*\.name | string | 
action\_result\.data\.\*\.prefixes6\.\*\.netblock | string | 
action\_result\.data\.\*\.prefixes6\.\*\.size | string | 
action\_result\.data\.\*\.prefixes6\.\*\.status | string | 
action\_result\.data\.\*\.registry | string | 
action\_result\.data\.\*\.type | string | 
action\_result\.summary\.name | string | 
action\_result\.summary\.num\_ips | numeric | 
action\_result\.message | string | 
summary\.total\_objects | numeric | 
summary\.total\_objects\_successful | numeric | 