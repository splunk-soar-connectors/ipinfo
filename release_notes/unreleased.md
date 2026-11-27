**Unreleased**

* Migrated IPinfo to the Splunk SOAR SDK app layout
* Raised the minimum supported Splunk SOAR version to 7.0.0
* Removed Python 3.9 support; the app now supports Python 3.13 and 3.15
* lookup ip results are now shown in a custom widget with an offline world map and a details table, replacing the built-in map widget
* Added the make request action to call any ipinfo.io endpoint with the asset's token
* Added a 30 second timeout to ipinfo.io requests
* Error messages no longer include the raw ipinfo.io response, which could contain the API token
