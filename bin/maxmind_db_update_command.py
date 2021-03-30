import os
import shutil
import sys
import json
import requests
import tarfile

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration
from splunk import rest
import mmdb_utils



MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz'

LIMITS_CONF_STANZA = 'iplocation'
LIMITS_CONF_PARAMETER = 'db_path'

MMDB_PATH_DIR = 'mmdb'
MMDB_FILE_NAME = 'GeoLite2-City.mmdb'

import splunk.appserver.mrsparkle.lib.util as splunk_lib_util
APP_LOCAL_PATH = splunk_lib_util.make_splunkhome_path(["etc", "apps", mmdb_utils.APP_NAME, "local"])
DB_DIR_PATH = os.path.join(APP_LOCAL_PATH, MMDB_PATH_DIR)
DB_TEMP_DOWNLOAD = os.path.join(DB_DIR_PATH, "temp_file.tar.gz")
DB_PATH_TO_SET = os.path.join(DB_DIR_PATH, MMDB_FILE_NAME)


@Configuration(type='reporting')
class UpdateMaxMindDatabase(GeneratingCommand):

    def get_max_mind_license_key(self):
        sessionKey = self.search_results_info.auth_token
        return mmdb_utils.CredentialManager(sessionKey).get_credential(mmdb_utils.MaxMindLicenseKeyInPasswordStore)


    def get_mmdb_location(self):

        current_location = '/opt/splunk/share/'

        sessionKey = self.search_results_info.auth_token
        endpoint = '/servicesNS/nobody/{}/configs/conf-{}'.format(mmdb_utils.APP_NAME, 'limits')
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=sessionKey, getargs={'output_mode':'json'}, raiseAllErrors=True)
        data = json.loads(response_content)['entry']
        for i in data:
            if i['name'] == LIMITS_CONF_STANZA:
                current_location = i['content'][LIMITS_CONF_PARAMETER]
        
        return current_location


    def update_mmdb_location(self):
        current_location = self.get_mmdb_location()
        if current_location == DB_PATH_TO_SET:
            return
        
        # Update location in limits.conf
        sessionKey = self.search_results_info.auth_token
        postargs = {
            'name': LIMITS_CONF_STANZA,
            LIMITS_CONF_PARAMETER: DB_PATH_TO_SET
        }
        endpoint = '/servicesNS/nobody/{}/configs/conf-{}'.format(mmdb_utils.APP_NAME, 'limits')
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=sessionKey, getargs={'output_mode':'json'}, postargs=postargs, method='POST', raiseAllErrors=True)


    def download_mmdb_database(self, license_key):
        r = requests.get(MaxMindDatabaseDownloadLink.format(license_key), allow_redirects=True)
        if r.status_code == 200:
            open(DB_TEMP_DOWNLOAD, 'wb').write(r.content)
            try:
                # Extract the downloaded file
                tar = tarfile.open(DB_TEMP_DOWNLOAD, "r:gz")
                tar.extractall(path=DB_DIR_PATH)
                tar.close()
            except Exception as e:
                raise Exception("Unable to untar downloaded MaxMind database. {}".format(e))

            try:
                # Find untared folder
                downloaded_dir = None
                for filedir in os.listdir(DB_DIR_PATH):
                    if filedir.startswith("GeoLite2-City"):
                        downloaded_dir = os.path.join(DB_DIR_PATH, filedir)
                        break
                # Find downloaded file
                donwloaded_file = None
                for filedir in os.listdir(downloaded_dir):
                    if filedir.startswith("GeoLite2-City"):
                        donwloaded_file = os.path.join(downloaded_dir, filedir)
                        break
                # Move extracted file to correct location
                shutil.move(donwloaded_file, DB_PATH_TO_SET)
                # remove temp files
                shutil.rmtree(downloaded_dir)
                os.remove(DB_TEMP_DOWNLOAD)
            except Exception as e:
                raise Exception("Unable to perform file operations on MaxMind database file. {}".format(e))
        else:
            raise Exception("Unable to download Max Mind database. status_code={}, Content: {}".format(r.status_code, r.content))

 
    def generate(self):
        # Create necessary directory is not exist
        if not os.path.exists(APP_LOCAL_PATH):
            os.makedirs(APP_LOCAL_PATH)
        if not os.path.exists(DB_DIR_PATH):
            os.makedirs(DB_DIR_PATH)

        # Read MaxMind license key
        license_key = self.get_max_mind_license_key()

        if not license_key:
            yield {"Message": "Max Mind license key not found in password store. Please set the license key from the configuration page."}
            self.logger.error("Max Mind license key not found in password store.")
        
        else:
            try:
                # Download mmdb database in a appropriate directory
                self.download_mmdb_database(license_key)

                # Update limits.conf to change the MMDB location
                self.update_mmdb_location()

                # Return Success Message
                self.logger.info("Return Success Message.")
                yield {"Message": "Max Mind Database updated successfully."}
            except Exception as e:
                yield {"Message": str(e)}


dispatch(UpdateMaxMindDatabase, sys.argv, sys.stdin, sys.stdout, __name__)
