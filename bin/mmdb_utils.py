import os
import json
import requests
import tarfile
import shutil
from six.moves.urllib.parse import quote

import splunk.entity as entity
import splunk.appserver.mrsparkle.lib.util as splunk_lib_util
from splunk import rest

APP_NAME = 'splunk_maxmind_db_auto_update'

MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE = 'max_mind_license_key'

LIMITS_CONF_STANZA = 'iplocation'
LIMITS_CONF_PARAMETER = 'db_path'

MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz'

MMDB_PATH_DIR = 'mmdb'
MMDB_FILE_NAME = 'GeoLite2-City.mmdb'

APP_LOCAL_PATH = splunk_lib_util.make_splunkhome_path(["etc", "apps", APP_NAME, "local"])
DB_DIR_PATH = os.path.join(APP_LOCAL_PATH, MMDB_PATH_DIR)
DB_TEMP_DOWNLOAD = os.path.join(DB_DIR_PATH, "temp_file.tar.gz")
DB_PATH_TO_SET = os.path.join(DB_DIR_PATH, MMDB_FILE_NAME)




class CredentialManager(object):
    '''
    Credential manager to store and retrieve password
    '''
    def __init__(self, session_key):
        '''
        Init for credential manager
        :param session_key: Splunk session key
        '''
        self.session_key = session_key

    def get_credential(self, username):
        '''
        Searches passwords using username and returns tuple of username and password if credentials are found else tuple of empty string
        :param username: Username used to search credentials.
        :return: username, password
        '''
        # list all credentials
        entities = entity.getEntities(["admin", "passwords"], search=APP_NAME, count=-1, namespace=APP_NAME, owner="nobody",
                                    sessionKey=self.session_key)

        # return first set of credentials
        for _, value in list(entities.items()):
            # if str(value["eai:acl"]["app"]) == APP_NAME and value["username"] == username:
            if value['username'].partition('`')[0] == username and not value.get('clear_password', '`').startswith('`'):
                try:
                    return json.loads(value.get('clear_password', '{}').replace("'", '"'))
                except:
                    return value.get('clear_password', '')

    def store_credential(self, username, password):
        '''
        Updates password if password is already stored with given username else create new password.
        :param username: Username to be stored.
        :param password: Password to be stored.
        :return: None
        '''
        old_password = self.get_credential(username)
        username = username + "``splunk_cred_sep``1"

        if old_password:
            postargs = {
                "password": json.dumps(password) if isinstance(password, dict) else password
            }
            username = username.replace(":", r"\:")
            realm = quote(APP_NAME + ":" + username + ":", safe='')

            rest.simpleRequest(
                "/servicesNS/nobody/{}/storage/passwords/{}?output_mode=json".format(APP_NAME, realm),
                self.session_key, postargs=postargs, method='POST', raiseAllErrors=True)

            return True
        else:
            # when there is no existing password
            postargs = {
                "name": username,
                "password": json.dumps(password) if isinstance(password, dict) else password,
                "realm": APP_NAME
            }
            rest.simpleRequest("/servicesNS/nobody/{}/storage/passwords/?output_mode=json".format(APP_NAME),
                                    self.session_key, postargs=postargs, method='POST', raiseAllErrors=True)



class MaxMindDatabaseUtil(object):

    def __init__(self, session_key):
        self.session_key = session_key

        # Create necessary directory is not exist
        if not os.path.exists(APP_LOCAL_PATH):
            os.makedirs(APP_LOCAL_PATH)
        if not os.path.exists(DB_DIR_PATH):
            os.makedirs(DB_DIR_PATH)

        # Read MaxMind license key
        license_key = self.get_max_mind_license_key()

        if not license_key:
            raise Exception("Max Mind license key not found in password store. Please set the license key from the configuration page.")

        # Download mmdb database in a appropriate directory
        self.download_mmdb_database(license_key)

        # Update limits.conf to change the MMDB location
        self.update_mmdb_location()


    def get_max_mind_license_key(self):
        return CredentialManager(self.session_key).get_credential(MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE)


    def get_mmdb_location(self):

        current_location = '/opt/splunk/share/'

        endpoint = '/servicesNS/nobody/{}/configs/conf-{}'.format(APP_NAME, 'limits')
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=self.session_key, getargs={'output_mode':'json'}, raiseAllErrors=True)
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
        sessionKey = self.session_key
        postargs = {
            'name': LIMITS_CONF_STANZA,
            LIMITS_CONF_PARAMETER: DB_PATH_TO_SET
        }
        endpoint = '/servicesNS/nobody/{}/configs/conf-{}'.format(APP_NAME, 'limits')
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=sessionKey, getargs={'output_mode':'json'}, postargs=postargs, method='POST')
        if response_status.status == 201 or response_status.status == 201:
            return   # success or created
        elif response_status.status == 409:
            # When stanza is already exist
            postargs2 = {
                LIMITS_CONF_PARAMETER: DB_PATH_TO_SET
            }
            endpoint2 = '/servicesNS/nobody/{}/configs/conf-{}/'.format(APP_NAME, 'limits', LIMITS_CONF_STANZA)
            response_status2, response_content2 = rest.simpleRequest(endpoint2,
                    sessionKey=sessionKey, getargs={'output_mode':'json'}, postargs=postargs2, method='POST', raiseAllErrors=True)
        else:
            raise Exception("[HTTP {}] {}".format(response_status.status, response_content))


    def download_mmdb_database(self, license_key):
        # NOTE - Proxy Configuration
        # Remove '<username>:<password>@' part if using proxy without authentication (just use ip:port format)
        # Understand the risk of storing password in plain-text when using proxy with authentication
        proxies = {
            "http" : "<proxy-supported-schema http|https>://<username>:<password>@<ip-address>:<port>",
            "https" : "<proxy-supported-schema http|https>://<username>:<password>@<ip-address>:<port>"
        }

        # NOTE - Please visit GitHub page (https://github.com/VatsalJagani/Splunk-App-Auto-Update-MaxMind-Database), if you are developer and want to help improving this App in anyways

        r = requests.get(MaxMindDatabaseDownloadLink.format(license_key), allow_redirects=True, proxies=proxies)
        
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
                    if filedir.startswith("GeoLite2-City_"):
                        downloaded_dir = os.path.join(DB_DIR_PATH, filedir)
                        break
                # Find downloaded file
                downloaded_file = None
                for filedir in os.listdir(downloaded_dir):
                    if filedir.startswith("GeoLite2-City"):
                        downloaded_file = os.path.join(downloaded_dir, filedir)
                        break
                # Move extracted file to correct location
                shutil.move(downloaded_file, DB_PATH_TO_SET)
                # remove temp files
                shutil.rmtree(downloaded_dir)
                os.remove(DB_TEMP_DOWNLOAD)
            except Exception as e:
                raise Exception("Unable to perform file operations on MaxMind database file. {}".format(e))
        else:
            raise Exception("Unable to download Max Mind database. status_code={}, Content: {}".format(r.status_code, r.content))

