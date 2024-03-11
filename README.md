# Splunk-App-Auto-Update-MaxMind-Database
Splunk App that auto updates the max-mind database (used for `iplocation` command)

Note:- Do not use App version 2.0.0 and above for Splunk version below 9.0.0.


### Download from Splunkbase
https://splunkbase.splunk.com/app/5482/


OVERVIEW
--------
The Splunk app auto updates MaxMind database. The database update happens automatically every week. Also, user can update database just by running a search query.

* Author - CrossRealms International Inc.
* Creates Index - False
* Compatible with:
   * Splunk Enterprise version: 9.0.x
   * OS: Platform independent
   * Browser: Google Chrome, Mozilla Firefox, Safari


## What's inside the App

* No of XML Dashboards: **1**
* Approx Total Viz(Charts/Tables/Map) in XML dashboards: **1**
* No of Reports and Alerts: **1**
* No of Custom Commands: **1**



TOPOLOGY AND SETTING UP SPLUNK ENVIRONMENT
------------------------------------------
This app can be set up in two ways: 
  1. Standalone Mode: 
     * Install the `Auto Update MaxMind Database`.
     * App setup is required.
  2. Distributed Mode: 
     * Install the `Auto Update MaxMind Database` only on the search head.
     * App setup is required on SH.
     * App installation is not required on any other instance.


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
  * Create an Account on https://www.maxmind.com/en/geoip2-services-and-databases and generate a license key from going to Account icon on top right and "Manage License Keys".

* App Configuration
  * Open the App and configure Account ID and License Key.
  * See troubleshooting for more details.


DEV
---
* App now uses (from App version 3.0.0) same endpoint as [geoipupdate](https://github.com/maxmind/geoipupdate) utility to download the mmdb file.
  * App uses updates.maxmind.com to download the databases file which supports basic auth. (Prior to 3.0.0, It was using download.maxmind.com)


UNINSTALL APP
-------------
To uninstall app, user can follow below steps:
* SSH to the Splunk instance
* Go to folder apps($SPLUNK_HOME/etc/apps)
* Remove the `splunk_maxmind_db_auto_update` folder from apps directory
* Restart Splunk


KNOWN LIMITATION
----------------
* NA


RELEASE NOTES
-------------
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

* App Logs
  * Run `index=_internal sourcetype="auto_update_maxmind_db:logs"` in the search to see app's internal logs



CONTRIBUTORS
------------
* Visit GitHub page - https://github.com/CrossRealms/Splunk-App-Auto-Update-MaxMind-Database



SUPPORT
-------
* Contact - CrossRealms International Inc.
  * US: +1-312-2784445
* License Agreement - https://cdn.splunkbase.splunk.com/static/misc/eula.html
* Copyright - Copyright CrossRealms Internationals, 2024
