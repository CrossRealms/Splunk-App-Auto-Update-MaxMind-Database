# Splunk-App-Auto-Update-MaxMind-Database
Splunk App that auto updates the max-mind database (used for `iplocation` command)

Note:- Do not use App version 2.0.0 and above for Splunk version below 9.0.0.


### Download from Splunkbase
https://splunkbase.splunk.com/app/5482/


OVERVIEW
--------
The Splunk app auto updates MaxMind database. The database update happens automatically every day. Also, user can update database just by running a search query.

* Author - CrossRealms International Inc.
* Creates Index - False
* Compatible with:
   * Splunk Enterprise version: 10.2.x, 10.4.x
   * OS: Platform independent
   * Browser: Google Chrome, Mozilla Firefox, Safari


## What's inside the App

* No of XML Dashboards: **1**
* Approx Total Viz(Charts/Tables/Map) in XML dashboards: **1**
* No of Reports and Alerts: **1**
* No of Custom Commands: **1**



TOPOLOGY AND SETTING UP SPLUNK ENVIRONMENT
------------------------------------------
Install the app **only on the search tier (search head)**. It never needs to be installed on indexers.

  1. **Standalone (single instance)**
     * Install the `Auto Update MaxMind Database` app.
     * Complete the app setup (see CONFIGURATION).

  2. **Distributed (separate search head and indexers)**
     * Install the app on the search head only.
     * Complete the app setup on the search head.
     * No installation is required on indexers or any other instance.

  3. **Search Head Cluster (SHC)** — install through the deployer:
     1. Copy the app package to the SHC **deployer** and extract it into `$SPLUNK_HOME/etc/shcluster/apps/`.
     2. Push it to the members from the deployer:
        `splunk apply shcluster-bundle -target https://<any-member>:8089 -auth <admin>:<password>`
     3. Complete the app setup (Account ID + License Key) on **any one** member. The configuration and stored credentials replicate to the other members automatically.
     4. The scheduled update runs on the cluster **captain**, and the resulting `GeoIP2-City.mmdb` lookup replicates to every member automatically.


INSTALLATION
------------
Follow the below-listed steps to install an App from the bundle:

* Download the App package.
* From the UI navigate to `Apps > Manage Apps`.
* In the top right corner select `Install app from file`.
* Select `Choose File` and select the App package.
* Select `Upload` and follow the prompts.



CONFIGURATION
-------------
* Get Account ID and License Key
  * Create an Account on https://www.maxmind.com/en/geoip2-services-and-databases and generate a license key from going to Account icon on top right and "Manage License Keys". (For more details, refer [HOW TO GENERATE NEW LICENSE KEY FOR FREE](https://github.com/CrossRealms/Splunk-App-Auto-Update-MaxMind-Database/tree/Add-steps-to-generate-license-key?tab=readme-ov-file#how-to-generate-new-license-key-for-free) section)

* App Configuration
  * Open the App and configure Account ID and License Key.
  * Select Database File you want to update (GeoLite2 (free tier) or GeoIP2 (paid tier)). default:GeoLite2.
  * Optionally you can configure Proxy URL from UI:
      * if your Splunk instance cannot reach the internet directly, you can use proxy url as well.
      * Proxy URL will be stored in encrypted format, so you don't have to worry if in case your proxy URL contains proxy username and password.

  * Advanced Guide:
    * Provide custom certificate file:
      * Create a new file called `custom_cert.pem` with the content as public certificate you need inside the `bin` directory of the App.
    * Disable ssl validation
      * Only disable ssl validation in case it is absolutely needed.
      * Update the local version of `mmdb_configuration.conf` file and add `is_ssl_verify = false` parameter under `mmdb` stanza. And restart the Splunk service.
      * Note: if you have created `custom_cert.pem` inside the `bin` folder, this parameter will be ignored.

  * See troubleshooting for more details.


HOW THE DATABASE IS APPLIED
---------------------------
This app **does not** overwrite the database that ships with Splunk under `$SPLUNK_HOME/share/`. Instead, it uploads the freshly downloaded database as a Splunk **lookup table file** in the `search` app:

```
$SPLUNK_HOME/etc/apps/search/lookups/GeoIP2-City.mmdb
```

Splunk's `iplocation` command uses this file **automatically** — no `limits.conf` change is required. Per the Splunk documentation, a `.mmdb` added this way "is treated as a lookup table by the Splunk software" and "takes precedence over manual updates to the .mmdb file path in `limits.conf`."

What this gives you:
* **Automatic use:** `iplocation` reads the uploaded lookup table ahead of the bundled `$SPLUNK_HOME/share/` database, so the weekly update is applied with no further configuration.
* **Automatic replication:** because it is a lookup in the `search` app, the file is distributed through knowledge-bundle replication — to indexers in distributed search, and to every member of a search head cluster.
* **Naming:** the file is always named `GeoIP2-City.mmdb`, even when you selected the free **GeoLite2** tier. This is the name `iplocation` expects.

References (Splunk documentation):
* `iplocation` command — "Updating the IP geolocation database file" and "Storing the .mmdb file in a different file path" (lookup-table treatment and `limits.conf` precedence):
  * [Splunk Enterprise 9.3](https://help.splunk.com/en/splunk-enterprise/search/spl-search-reference/9.3/search-commands/iplocation)
  * [Splunk Enterprise 10.4](https://help.splunk.com/en/splunk-enterprise/search/spl-search-reference/10.4/search-commands/iplocation)


HOW TO GENERATE NEW LICENSE KEY FOR FREE
----------------------------------------
  * Create free account on https://www.maxmind.com/en/geolite2/signup?utm_source=kb&utm_medium=kb-link&utm_campaign=kb-create-account
    ![alt](https://github.com/CrossRealms/Splunk-App-Auto-Update-MaxMind-Database/blob/master/images/license_key_generation_1.png)
  * Generate a license key from going to Account icon on top right and "Manage License Keys"
    ![alt](https://github.com/CrossRealms/Splunk-App-Auto-Update-MaxMind-Database/blob/master/images/license_key_generation_2.png)
  * Copy the AccountID from this page and Click on the "Generate new license key" and copy it.
    ![alt](https://github.com/CrossRealms/Splunk-App-Auto-Update-MaxMind-Database/blob/master/images/license_key_generation_3.png)



UNINSTALL APP
-------------
To uninstall app, user can follow below steps:
* SSH to the Splunk instance
* Go to folder apps($SPLUNK_HOME/etc/apps)
* Remove the `splunk_maxmind_db_auto_update` folder from apps directory
* Restart Splunk



RELEASE NOTES
-------------

Version 4.2.0 (July 2026)
* Added compatibility with Python 3.13 while retaining Python 3.9 / existing Splunk support.
    * Replaced the `six` compatibility shim with the standard library `urllib.parse`.
    * MaxMind database archive extraction uses the `data` filter on Python 3.12+ and falls back gracefully on older interpreters.
* Dependencies pinned to versions compatible with both Python 3.9 and 3.13 (Splunk Python SDK 2.1.1, requests 2.32.5).

Version 4.1.0 (April 2025)
* Added support for downloading the MaxMind GeoIP2 database file (paid tier).

Version 4.0.1 (December 2024)
* Splunk-python-sdk updated to the latest version.

Version 4.0.0 (May 2024)
* Added support for `Proxy` from UI.
* Fixed issue when App run in Splunk environment with Python2 as default.
    * Syntax error with code - "Error in 'maxminddbupdate' command: External search command exited unexpectedly with non-zero error code 1."
* Provided support to explicitly disable `SSL cert` validation from mmdb_configuration.conf file. (Caution: User is not recommend to disable the cert validation unless it is absolutely necessary.)
* Splunk-python-sdk updated to the latest version.


Version 3.3.1 / Version 3.3.2 (April/May 2024)
* Only a patch release. See the release notes under version 4.0.0.


Version 3.2.0 (March 2024)
* Updated MaxMind Download URL based on the announcement `We're transitioning to R2 presigned URLs` from MaxMind on `12th of March, 2024`.


Version 3.1.1 (March 2024)
* Splunk Python SDK has been updated to the latest version 1.7.4.
* Minor logging improvement.


Version 3.1.0 (July 2023)
* Now it MaxMind database updates every day instead of every week.
* (FYI, actual MaxMind DB updates only once a week or twice a week, but this change will bring the new database quickly.)


Version 3.0.0 (May 2023)
* Fixed the security issue - Earlier the App was using an API endpoint with exposed LicenseKey in the URL, not it is using a proper authentication mechanism instead.
* Fixed Splunk Cloud compatibility issue (check_for_secret_disclosure).

Upgrade Guide for version 3.0.0 from previous Version
* User has to reconfigure the `Account ID` and `License Key` in the MaxMind Database Configuration Page. (Prior to 3.0.0, only License Key was required)
* Post configuration please execute the validation steps:
  * Run `| maxminddbupdate` search from the `Auto Update MaxMind Database` App.
    * In ideal scenario, it should show message `Max Mind Database updated successfully.`


Version 2.0.0 (November 2022)
* Support for distributed environment without installing App on the Indexers.
* Support for Search head cluster without running the process on the all the search head by replicating the file through lookups folder.
* Support for Splunk Cloud Classic stacks by removing inputs.conf and the whole process runs by custom command in a scheduled savedsearch.


Upgrade Guide for version 2.0.0 from previous Version
* On-Prem Environment: Remove the App installed on Indexers separately. Upgrade the App on the SHs.
* Cloud: Just upgrade the App from Splunk Cloud UI.
* Post upgrade (for both On-Prem and Cloud) please execute the validation steps:
  * Run `| maxminddbupdate` search from the `Auto Update MaxMind Database` App.
    * In ideal scenario, it should show message `Max Mind Database updated successfully.`



Version 1.1.0 (June 2022)
* Provided support for search head cluster and resolve cloud app-inspect issue.


Version 1.0.4 (Dec 2021)
* Added app.manifest file for Splunk-cloud.


Version 1.0.3 (Aug 2021)
* Changes to make compatible with the latest Splunk AppInspect - Dashboards version changed to 1.1.


Version 1.0.2 (June 2021)
* Fixed the small issue in python custom command.


Version 1.0.1 (April 2021)
* Added better error handling.


Version 1.0.0 (March 2021)
* App created based on URL from March 2021 on MaxMind to download the database.



OPEN SOURCE COMPONENTS AND LICENSES
------------------------------
* NA


TROUBLESHOOTING
---------------

* Update database manually.
  * Run `| maxminddbupdate` search from the `Auto Update MaxMind Database` App.
  * In ideal scenario, it should show message `Max Mind Database updated successfully.`.

* "The file in `$SPLUNK_HOME/share/` still shows an old date, so the update isn't working."
  * This is expected — the app never modifies `$SPLUNK_HOME/share/`. It uploads the updated file to `$SPLUNK_HOME/etc/apps/search/lookups/GeoIP2-City.mmdb`, which `iplocation` uses automatically (see **HOW THE DATABASE IS APPLIED**). Don't judge the update by the `share/` file's timestamp.
  * Confirm the lookup file exists and has a recent timestamp at `$SPLUNK_HOME/etc/apps/search/lookups/GeoIP2-City.mmdb`.

* The update fails, or you do not get the `Max Mind Database updated successfully.` message.
  * Check the app logs (below) for the specific error, then verify:
    * The **Account ID** and **License Key** are correct — re-enter them on the configuration page if unsure.
    * The selected **tier matches your license** — choosing **GeoIP2 (paid)** without a paid subscription makes the download fail (e.g. HTTP 401).
    * If the instance has no direct internet access, a valid **Proxy URL** is configured, and your **SSL/certificate** settings are correct (see CONFIGURATION → Advanced Guide).

* App Logs
  * Run `index=_internal sourcetype="auto_update_maxmind_db:logs"` in the search to see app's internal logs


KNOWN LIMITATION
----------------
* **Search Head Cluster — the setup page may reappear on other members.** After you configure the app on one member, the configuration replicates to the other members, but opening the app on a different member can still show the setup (configuration) page as if it were not configured. This is display-only — the app *is* configured and the scheduled update runs on the captain. You do not need to re-enter the Account ID and License Key on each member.



CONTRIBUTORS
------------
* Visit GitHub page - https://github.com/CrossRealms/Splunk-App-Auto-Update-MaxMind-Database



SUPPORT
-------
* Contact - CrossRealms International Inc.
  * US: +1-312-2784445
  * splunkteam@crossrealms.com
* License Agreement - https://cdn.splunkbase.splunk.com/static/misc/eula.html
* Copyright - Copyright CrossRealms Internationals, 2026
