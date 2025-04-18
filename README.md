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


KNOWN LIMITATION
----------------
* NA


RELEASE NOTES
-------------

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
* Copyright - Copyright CrossRealms Internationals, 2025
