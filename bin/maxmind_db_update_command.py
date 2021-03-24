import os
import sys
import json
import requests

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration
from splunk import rest
import mmdb_utils



MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-ASN&license_key={}&suffix=tar.gz.sha256'

LIMITS_CONF_STANZA = 'iplocation'
LIMITS_CONF_PARAMETER = 'db_path'

MMDB_PATH_DIR = 'mmdb'
MMDB_FILE_NAME = 'GeoLite2-City.mmdb'

import splunk.appserver.mrsparkle.lib.util as splunk_lib_util
APP_LOCAL_PATH = splunk_lib_util.make_splunkhome_path(["etc", "apps", mmdb_utils.APP, "local"])
DB_DIR_PATH = os.path.join(APP_LOCAL_PATH, MMDB_PATH_DIR)
DB_PATH_TO_SET = os.path.join(DB_DIR_PATH, MMDB_FILE_NAME)


@Configuration()
class UpdateMaxMindDatabase(GeneratingCommand):

    def get_max_mind_license_key(self):
        sessionKey = self.search_results_info.auth_token
        return mmdb_utils.CredentialManager(sessionKey).get_credential(mmdb_utils.MaxMindLicenseKeyInPasswordStore)


    def get_mmdb_location(self):

        current_location = '/opt/splunk/share/'

        sessionKey = self.search_results_info.auth_token
        endpoint = '/servicesNS/nobody/{}/configs/conf-{}/{}'.format(mmdb_utils.APP, 'limits', LIMITS_CONF_STANZA)
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=sessionKey, getargs={'output_mode':'json'}, raiseAllErrors=True)
        # TODO - Need to check this
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
            LIMITS_CONF_PARAMETER: DB_PATH_TO_SET
        }
        endpoint = '/servicesNS/nobody/{}/configs/conf-{}/{}'.format(mmdb_utils.APP, 'limits', LIMITS_CONF_STANZA)
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=sessionKey, getargs={'output_mode':'json'}, postargs=postargs, method='POST', raiseAllErrors=True)
        # TODO - check if the path is updated or not


    def download_mmdb_database(self, license_key):
        r = requests.get(MaxMindDatabaseDownloadLink.format(license_key), allow_redirects=True)
        open(DB_PATH_TO_SET, 'wb').write(r.content)
        # Check if the file is saved

 
    def generate(self):
        # Create necessary directory is not exist
        if not os.path.exists(APP_LOCAL_PATH):
            os.makedir(APP_LOCAL_PATH)
        if not os.path.exists(DB_DIR_PATH):
            os.makedir(DB_DIR_PATH)

        # Read MaxMind license key
        license_key = self.get_max_mind_license_key()

        if not license_key:
            self.logger.info("Max Mind license key not found in password store.")
        

        # Download mmdb database in a appropriate directory
        self.download_mmdb_database(license_key)

        # Update limits.conf to change the MMDB location
        self.update_mmdb_location()

        # Return Success Message
        self.logger.info("Return Success Message.")
        yield {"Message": "Max Mind Database updated successfully."}


dispatch(UpdateMaxMindDatabase, sys.argv, sys.stdin, sys.stdout, __name__)
