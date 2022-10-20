import os
import json
import requests
import tarfile
import shutil
from six.moves.urllib.parse import quote

import splunk.entity as entity
import splunk.appserver.mrsparkle.lib.util as splunk_lib_util
from splunk import rest


import logging
import logger_manager
logger = logger_manager.setup_logging('log', logging.DEBUG)


APP_NAME = 'splunk_maxmind_db_auto_update'

MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE = 'max_mind_license_key'

LIMITS_CONF_STANZA = 'iplocation'
LIMITS_CONF_PARAMETER = 'db_path'

MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz'

MMDB_PATH_DIR = 'mmdb'
MMDB_FILE_NAME = 'GeoLite2-City.mmdb'

ACCEPTED_LOOKUP_NAME = 'GeoIP2-City.mmdb'
LOOKUP_FILE_LOCATION = splunk_lib_util.make_splunkhome_path(['var', 'run','splunk', 'lookup_tmp', MMDB_FILE_NAME])


APP_PATH = splunk_lib_util.make_splunkhome_path(["etc", "apps", APP_NAME])
APP_LOCAL_PATH = os.path.join(APP_PATH, 'local')
APP_LOOKUP_PATH = os.path.join(APP_PATH, 'lookups')

MMDB_FILE_NEW_PATH = APP_LOOKUP_PATH

'''
# Enable below if App's lookup directory does not work
SEARCH_APP_LOOKUP_PATH = splunk_lib_util.make_splunkhome_path(["etc", "apps", 'search', 'lookups'])
MMDB_FILE_NEW_PATH = SEARCH_APP_LOOKUP_PATH
'''

DB_DIR_TEMP_PATH = os.path.join(APP_LOCAL_PATH, MMDB_PATH_DIR)
DB_TEMP_DOWNLOAD = os.path.join(DB_DIR_TEMP_PATH, "temp_file.tar.gz")


APP_LOCAL_LIMITS_CONF_PATH = os.path.join(APP_LOCAL_PATH, 'limits.conf')




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
        logger.info("Getting the stored license-key from passwords.conf")
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
        logger.info("Storing the license-key in passwords.conf in encrypted form.")
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
        logger.info("Initialized MaxMindDatabaseUtil")

        self.session_key = session_key

        # Create necessary directory is not exist
        if not os.path.exists(APP_LOCAL_PATH):
            os.makedirs(APP_LOCAL_PATH)
        if not os.path.exists(DB_DIR_TEMP_PATH):
            os.makedirs(DB_DIR_TEMP_PATH)

        # Read MaxMind license key
        license_key = self.get_max_mind_license_key()

        if not license_key:
            msg = "Max Mind license key not found in password store. Please set the license key from the configuration page."
            logger.error(msg)
            raise Exception(msg)

        # Updating limits.conf is no longer require from Splunk version 9.x hence cleaning that up
        self.cleaning_old_version_limits_conf()

        # Download mmdb database in a appropriate directory
        self.download_mmdb_database(license_key)

        flag = self.is_lookup_present()
        logger.debug("is_lookup_present = {}".format(flag))

        if flag:
            logger.debug("Updating the lookup")
            self.update_lookup()
        else:
            logger.debug("Creating the lookup")
            self.create_lookup()

        logger.info("MaxMind Database file updated successfully.")


    def get_max_mind_license_key(self):
        return CredentialManager(self.session_key).get_credential(MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE)


    def cleaning_old_version_limits_conf(self):
        if os.path.exists(APP_LOCAL_LIMITS_CONF_PATH):
            logger.info("Removing app-local/limits.conf")
            os.remove(APP_LOCAL_LIMITS_CONF_PATH)
            self.reload_limits_conf()


    def reload_limits_conf(self):
        rest.simpleRequest(
                "/servicesNS/-/-/admin/limits/_reload",
                self.session_key,
                getargs= {'output_mode': 'json', 'count': '0'},
                method='GET', raiseAllErrors=True)


    def is_lookup_present(self):
        _, content = rest.simpleRequest(
                "/servicesNS/nobody/search/data/lookup-table-files",
                self.session_key,
                getargs= {'output_mode': 'json', 'count': '0'},
                method='GET', raiseAllErrors=True)

        data = json.loads(content)['entry']
        for item in data:
            if item['name'] == ACCEPTED_LOOKUP_NAME:
                return True
        else:
            return False


    def create_lookup(self):
        rest.simpleRequest(
                "/servicesNS/nobody/search/data/lookup-table-files",
                self.session_key,
                getargs= {'output_mode': 'json', 'count': '0'},
                postargs= {'name': ACCEPTED_LOOKUP_NAME, 'eai:data': LOOKUP_FILE_LOCATION},
                method='POST', raiseAllErrors=True)


    def update_lookup(self):
        rest.simpleRequest(
                "/servicesNS/nobody/search/data/lookup-table-files/" + ACCEPTED_LOOKUP_NAME,
                self.session_key,
                getargs= {'output_mode': 'json', 'count': '0'},
                postargs= {'eai:data': LOOKUP_FILE_LOCATION},
                method='POST', raiseAllErrors=True)


    def download_mmdb_database(self, license_key):
        # NOTE - Proxy Configuration
        # Remove '<username>:<password>@' part if using proxy without authentication (just use ip:port format)
        # Understand the risk of storing password in plain-text when using proxy with authentication
        proxies = None
        '''
        proxies = {
            "http" : "<proxy-supported-schema http|https>://<username>:<password>@<ip-address>:<port>",
            "https" : "<proxy-supported-schema http|https>://<username>:<password>@<ip-address>:<port>"
        }
        '''

        # NOTE - Please visit GitHub page (https://github.com/VatsalJagani/Splunk-App-Auto-Update-MaxMind-Database), if you are developer and want to help improving this App in anyways

        logger.debug("Downloading the MaxMind DB file.")
        r = requests.get(MaxMindDatabaseDownloadLink.format(license_key), allow_redirects=True, proxies=proxies)
        
        if r.status_code == 200:
            open(DB_TEMP_DOWNLOAD, 'wb').write(r.content)
            try:
                # Extract the downloaded file
                tar = tarfile.open(DB_TEMP_DOWNLOAD, "r:gz")
                tar.extractall(path=DB_DIR_TEMP_PATH)
                tar.close()
            except Exception as e:
                msg = "Unable to untar downloaded MaxMind database. {}".format(e)
                logger.exception(msg)

            try:
                # Find untared folder
                downloaded_dir = None
                for filedir in os.listdir(DB_DIR_TEMP_PATH):
                    if filedir.startswith("GeoLite2-City_"):
                        downloaded_dir = os.path.join(DB_DIR_TEMP_PATH, filedir)
                        break

                # Find downloaded file
                downloaded_file = None
                for filedir in os.listdir(downloaded_dir):
                    if filedir.startswith("GeoLite2-City"):
                        downloaded_file = os.path.join(downloaded_dir, filedir)
                        logger.debug("Downloaded MaxMind DB file: {}".format(downloaded_file))
                        break

                # Move extracted file to lookup_tmp location with updated file name
                shutil.move(downloaded_file, LOOKUP_FILE_LOCATION)
                logger.debug("MaxMind DB file added: {}".format(LOOKUP_FILE_LOCATION))

                # remove temp files
                shutil.rmtree(downloaded_dir)
                os.remove(DB_TEMP_DOWNLOAD)

            except Exception as e:
                logger.exception("Unable to perform file operations on MaxMind database file. {}".format(e))
        else:
            logger.error("Unable to download Max Mind database. status_code={}, Content: {}".format(r.status_code, r.content))

