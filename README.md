# Splunk-App-Auto-Update-MaxMind-Database
Splunk App that auto updates the max-mind database (used for `iplocation` command)

### Download from Splunkbase
https://splunkbase.splunk.com/app/5482/


OVERVIEW
--------
The Splunk app auto updates MaxMind database. The database update happens automatically every week. Also, user can update database just by running a search query. This is automation of steps mentioned here - https://docs.splunk.com/Documentation/Splunk/8.1.3/SearchReference/Iplocation#Updating_the_MMDB_file


* Author - Vatsal Jagani
* Creates Index - False
* Compatible with:
   * Splunk Enterprise version: 8.1, 8.0, 7.3, 7.2
   * OS: Platform independent
   * Browser: Google Chrome, Mozilla Firefox, Safari



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
* Open the App and perform the configuration.
* The complete details about configuration is present on the dashboard directly.
* See troubleshooting for more details.


INSTALLATION AND CONFIGURATION FOR INDEXER CLUSTER
--------------------------------------------------
* `iplocation` is distributed command, so based on search queries Splunk will decide whether the command is executed on SH or indexers. So it is recommended to deploy the App on Search Head as well as on indexers.
* Follow below steps to deploy App on indexers.

### Way-1: Deploy on all indexers from cluster master.
Note - If you do not want to add Max Mind License key in plain text, use `Way-2`.

* App will be pushed from cluster master so, you don't have to deploy App manually on each indexer separately.
* Download the App build from Splunkbase.
* Extract the downloaded app build on Cluster master's `$SPLUNK_HOME/etc/master-apps/` directory.
* Create `local` directory under `$SPLUNK_HOME/etc/master-apps/splunk_maxmind_db_auto_update/`.
* Add `app.conf` file in the newly created local folder.
```
[install]
is_configured = 1
```
* Add `passwords.conf` file in the newly created local folder. And replace `<LICENSE_KEY>` in the below code with your MaxMind license key.
```
[credential:splunk_maxmind_db_auto_update:max_mind_license_key``splunk_cred_sep``1:]
password = <LICENSE_KEY>
```

### Way-2: Deploy on each indexer manually
Follow `INSTALLATION` and `CONFIGURATION` section from above to install and deploy app on indexer. The process is same as hwo you deploy App on Search Head.


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
* Confirm that the database location has been updated:
  * Run `| rest /services/configs/conf-limits splunk_server=local | search title="iplocation" | table title, db_path`.
  * The results should show `/opt/splunk/etc/apps/splunk_maxmind_db_auto_update/local/mmdb/GeoLite2-City.mmdb`. Where `/opt/splunk` is your Splunk home path, it could be different in your environment.



SUPPORT
-------
* Contact - CrossRealms International Inc.
  * US: +1-312-2784445
* License Agreement - https://d38o4gzaohghws.cloudfront.net/static/misc/eula.html
* Copyright - Copyright CrossRealms Internationals, 2021
