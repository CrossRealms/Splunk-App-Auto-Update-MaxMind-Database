import os
import json
import requests
import gzip
import shutil
from six.moves.urllib.parse import quote

import splunk.entity as entity
import splunk.appserver.mrsparkle.lib.util as splunk_lib_util
from splunk import rest


import logging
import logger_manager
logger = logger_manager.setup_logging('log', logging.DEBUG)


APP_NAME = 'splunk_maxmind_db_auto_update'

MMDB_CONF_FILE = 'mmdb_configuration'
MMDB_CONF_STANZA = 'mmdb'

MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE = 'max_mind_license_key'

LIMITS_CONF_STANZA = 'iplocation'
LIMITS_CONF_PARAMETER = 'db_path'

MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/geoip/databases/GeoLite2-City/download?suffix=tar.gz'

MMDB_PATH_DIR = 'mmdb'
MMDB_FILE_NAME = 'GeoLite2-City.mmdb'

ACCEPTED_LOOKUP_NAME = 'GeoIP2-City.mmdb'
LOOKUP_DIR_LOCATION = splunk_lib_util.make_splunkhome_path(['var', 'run','splunk', 'lookup_tmp'])
LOOKUP_FILE_LOCATION = os.path.join(LOOKUP_DIR_LOCATION, MMDB_FILE_NAME)


APP_PATH = splunk_lib_util.make_splunkhome_path(["etc", "apps", APP_NAME])
APP_LOCAL_PATH = os.path.join(APP_PATH, 'local')


DB_DIR_TEMP_PATH = os.path.join(APP_LOCAL_PATH, MMDB_PATH_DIR)
DB_TEMP_DOWNLOAD = os.path.join(DB_DIR_TEMP_PATH, "temp_file.gz")

OLD_DB_PATH = os.path.join(DB_DIR_TEMP_PATH, MMDB_FILE_NAME)
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
        if not os.path.exists(LOOKUP_DIR_LOCATION):
            os.makedirs(LOOKUP_DIR_LOCATION)

        account_id = self.get_max_mind_account_id()
        if not account_id:
            msg = "Max Mind Account key not found. Please update config from Max Mind database configuration page."
            logger.error(msg)
            raise Exception(msg)

        # Read MaxMind license key
        license_key = self.get_max_mind_license_key()
        if not license_key:
            msg = "Max Mind license key not found in password store. Please update config from Max Mind database configuration page.."
            logger.error(msg)
            raise Exception(msg)

        # Download mmdb database in a appropriate directory
        self.download_mmdb_database(account_id, license_key)

        flag = self.is_lookup_present()
        logger.debug("is_lookup_present = {}".format(flag))

        if flag:
            logger.debug("Updating the lookup")
            self.update_lookup()
        else:
            logger.debug("Creating the lookup")
            self.create_lookup()

        # The limits.conf is no longer required from Splunk version 9.x hence cleaning that up
        self.cleanup_old_version_limits_conf()

        logger.info("MaxMind Database file updated successfully.")


    def get_max_mind_account_id(self):
        _, serverContent = rest.simpleRequest("/servicesNS/nobody/{}/configs/conf-{}/{}?output_mode=json".format(APP_NAME, MMDB_CONF_FILE, MMDB_CONF_STANZA), sessionKey=self.session_key)
        data = json.loads(serverContent)['entry']

        account_id = ''
        for i in data:
            if i['name'] == MMDB_CONF_STANZA:
                account_id = i['content']['account_id']
                break
        return account_id


    def get_max_mind_license_key(self):
        return CredentialManager(self.session_key).get_credential(MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE)


    def get_mmdb_location(self):
        current_location = '/opt/splunk/share/'

        endpoint = '/servicesNS/nobody/{}/configs/conf-{}'.format(APP_NAME, 'limits')
        response_status, response_content = rest.simpleRequest(endpoint,
                sessionKey=self.session_key, getargs={'output_mode':'json', 'count': '0'}, raiseAllErrors=True)
        data = json.loads(response_content)['entry']
        for i in data:
            if i['name'] == LIMITS_CONF_STANZA:
                current_location = i['content'][LIMITS_CONF_PARAMETER]

        return current_location


    def cleanup_old_version_limits_conf(self):
        if os.path.exists(APP_LOCAL_LIMITS_CONF_PATH):
            current_location = self.get_mmdb_location()
            logger.debug("dbpath value from iplocation stanza = {}".format(current_location))
            if current_location == OLD_DB_PATH:
                # set empty value in dbpath
                rest.simpleRequest(
                    '/servicesNS/nobody/{}/configs/conf-{}/{}'.format(APP_NAME, 'limits', LIMITS_CONF_STANZA),
                    sessionKey=self.session_key,
                    getargs={'output_mode':'json'},
                    postargs={LIMITS_CONF_PARAMETER: ''},
                    method='POST', raiseAllErrors=True)

            logger.info("Removing app-local/limits.conf")
            os.remove(APP_LOCAL_LIMITS_CONF_PATH)


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


    def download_mmdb_database(self, account_id, license_key):
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
        try:
            r = requests.get(MaxMindDatabaseDownloadLink, auth=(account_id, license_key), allow_redirects=True, proxies=proxies)
        except Exception as err:
            logger.exception("Failed to download MaxMind DB file from {}".format(MaxMindDatabaseDownloadLink))
            raise err

        if r.status_code == 200:
            with open(DB_TEMP_DOWNLOAD, 'wb') as fp:
                fp.write(r.content)

            downloaded_file = os.path.join(DB_DIR_TEMP_PATH, 'GeoLite2-City.mmdb')
            try:
                # Extract the downloaded file
                with gzip.open(DB_TEMP_DOWNLOAD, 'rb') as s_file, open(downloaded_file, 'wb') as d_file:
                    shutil.copyfileobj(s_file, d_file, 65536)
            except Exception as e:
                msg = "Unable to extract downloaded MaxMind database. {}".format(e)
                logger.exception(msg)
                raise e

            logger.debug("Downloaded MaxMind DB file: {}".format(downloaded_file))

            try:
                # Move extracted file to lookup_tmp location with updated file name
                shutil.move(downloaded_file, LOOKUP_FILE_LOCATION)
                logger.debug("MaxMind DB file added: {}".format(LOOKUP_FILE_LOCATION))

                # remove temp files
                shutil.rmtree(DB_DIR_TEMP_PATH)

            except Exception as e:
                logger.exception("Unable to perform file operations on MaxMind database file. {}".format(e))
        else:
            err_msg = "Unable to download Max Mind database. status_code={}, Content: {}".format(r.status_code, r.content)
            logger.error(err_msg)
            raise Exception(err_msg)

