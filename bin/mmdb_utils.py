import import_lib

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
logger = logger_manager.setup_logging('mmdb_util', logging.DEBUG)


APP_NAME = 'splunk_maxmind_db_auto_update'

MMDB_CONF_FILE = 'mmdb_configuration'
MMDB_CONF_STANZA = 'mmdb'

MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE = 'max_mind_license_key'
MAXMIND_PROXY_URL_IN_PASSWORD_STORE = 'max_mind_proxy_url'

LIMITS_CONF_STANZA = 'iplocation'
LIMITS_CONF_PARAMETER = 'db_path'

MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/geoip/databases/{}-City/download?suffix=tar.gz'

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



def convert_to_bool_default_true(val):
    _val = str(val).lower()
    if _val in ["false", "f", "0"]:
        return False
    return True


def encode_username_password_in_proxy_url(proxy_url):
    _split_scheme = proxy_url.split("://")
    scheme = _split_scheme[0]
    rest_of_proxy_url = "://".join(_split_scheme[1:])

    username = None
    password = None
    if ":" in rest_of_proxy_url and "@" in rest_of_proxy_url:
        _split_username = rest_of_proxy_url.split(":")
        username = _split_username[0]
        rest_of_proxy_url = ":".join(_split_username[1:])

        _split_password = rest_of_proxy_url.split("@")
        password = "@".join(_split_password[:-1])
        rest_of_proxy_url = _split_password[-1]

    if username and password:
        encoded_username = quote(username, safe='')
        encoded_password = quote(password, safe='')
        return f"{scheme}://{encoded_username}:{encoded_password}@{rest_of_proxy_url}"
    else:
        return f"{scheme}://{rest_of_proxy_url}"


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
        logger.info(f"Getting the stored credential from passwords.conf. Username={username}")
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
                f"/servicesNS/nobody/{APP_NAME}/storage/passwords/{realm}?output_mode=json",
                self.session_key, postargs=postargs, method='POST', raiseAllErrors=True)

            return True
        else:
            # when there is no existing password
            postargs = {
                "name": username,
                "password": json.dumps(password) if isinstance(password, dict) else password,
                "realm": APP_NAME
            }
            rest.simpleRequest(f"/servicesNS/nobody/{APP_NAME}/storage/passwords/?output_mode=json",
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

        mmdb_config = self.get_max_mind_config()
        if not mmdb_config:
            msg = "Max Mind Account key not found. Please update config from Max Mind database configuration page."
            logger.error(msg)
            raise Exception(msg)

        if mmdb_config['maxmind_database_file'] not in ["GeoLite2", "GeoIP2"]:
            msg = f"Invalid database file: {mmdb_config['maxmind_database_file']}. Supported database files are 'GeoLite2' and 'GeoIP2'."
            logger.error(msg)
            raise Exception(msg)

        # Read MaxMind license key
        license_key = self.get_max_mind_license_key()
        if not license_key:
            msg = "Max Mind license key not found in password store. Please update config from Max Mind database configuration page."
            logger.error(msg)
            raise Exception(msg)

        # Read Proxy URL
        proxy_url = None
        try:
            proxy_url = self.get_max_mind_proxy_url()
        except Exception as e:
            logger.info(f"Exception in getting proxy_url. {e}")

        if not proxy_url or proxy_url == '******' or proxy_url.lower() == 'none':
            proxy_url = None
            msg = "Max Mind proxy_url not found in password store. Using no proxy."
            logger.info(msg)
        else:
            if proxy_url.startswith("https") or proxy_url.startswith("http") or \
                proxy_url.startswith("socks4") or proxy_url.startswith("socks5"):
                try:
                    proxy_url = encode_username_password_in_proxy_url(proxy_url)
                    logger.info("Using proxy_url provided by the user.")
                except Exception as e:
                    msg = "Unable to encode username and password in the proxy URL properly."
                    logger.error(msg + f" {e}")
                    raise Exception(msg)
            else:
                msg = "This App only supports http/https/socks4/socks5 proxy not any other proxy type."
                logger.error(msg)
                raise Exception(msg)

        # SSL certificate validation
        ssl_verify = convert_to_bool_default_true(mmdb_config['is_ssl_verify'])

        _custom_cert_path = os.path.join(os.path.dirname(__file__), "custom_cert.pem")
        if os.path.isfile(_custom_cert_path):
            ssl_verify = _custom_cert_path

        logger.info(f"Max Mind ssl_verify={ssl_verify}")

        # Download mmdb database in a appropriate directory
        self.download_mmdb_database(mmdb_config['account_id'], license_key, mmdb_config['maxmind_database_file'], proxy_url, ssl_verify)

        flag = self.is_lookup_present()
        logger.debug(f"is_lookup_present = {flag}")

        if flag:
            logger.debug("Updating the lookup")
            self.update_lookup()
        else:
            logger.debug("Creating the lookup")
            self.create_lookup()

        # The limits.conf is no longer required from Splunk version 9.x hence cleaning that up
        self.cleanup_old_version_limits_conf()

        logger.info("MaxMind Database file updated successfully.")


    def get_max_mind_config(self):
        _, serverContent = rest.simpleRequest(f"/servicesNS/nobody/{APP_NAME}/configs/conf-{MMDB_CONF_FILE}/{MMDB_CONF_STANZA}?output_mode=json", sessionKey=self.session_key)
        data = json.loads(serverContent)['entry']

        for i in data:
            if i['name'] == MMDB_CONF_STANZA:
                return i['content']

        return None


    def get_max_mind_license_key(self):
        return CredentialManager(self.session_key).get_credential(MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE)


    def get_max_mind_proxy_url(self):
        return CredentialManager(self.session_key).get_credential(MAXMIND_PROXY_URL_IN_PASSWORD_STORE)


    def get_mmdb_location(self):
        current_location = '/opt/splunk/share/'

        endpoint = f'/servicesNS/nobody/{APP_NAME}/configs/conf-limits'
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
            logger.debug(f"dbpath value from iplocation stanza = {current_location}")
            if current_location == OLD_DB_PATH:
                # set empty value in dbpath
                rest.simpleRequest(
                    f'/servicesNS/nobody/{APP_NAME}/configs/conf-limits/{LIMITS_CONF_STANZA}',
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


    def download_mmdb_database(self, account_id, license_key, database_file, proxy_url=None, ssl_verify=True):
        proxies = None
        if proxy_url:
            proxies = {
                "http" : proxy_url,
                "https" : proxy_url
            }

        logger.debug("Downloading the MaxMind DB file: {}.".format(database_file))
        try:
            r = requests.get(MaxMindDatabaseDownloadLink.format(database_file), auth=(account_id, license_key), allow_redirects=True, proxies=proxies, verify=ssl_verify)
        except Exception as err:
            logger.exception(f"Failed to download MaxMind DB file from {MaxMindDatabaseDownloadLink}")
            raise err

        if r.status_code == 200:
            with open(DB_TEMP_DOWNLOAD, 'wb') as fp:
                for chunk in r.iter_content(1024):
                    fp.write(chunk)

            try:
            # Extract the downloaded file
                with tarfile.open(DB_TEMP_DOWNLOAD, "r:gz") as tar:
                    tar.extractall(DB_DIR_TEMP_PATH)
            except tarfile.ReadError as e:
                msg = f"Unable to extract downloaded MaxMind database. {e}"
                logger.exception(msg)
                raise e

            logger.debug(f"Downloaded and extracted MaxMind DB folder: {DB_DIR_TEMP_PATH}")

            # Find untared folder
            downloaded_dir = None
            for filedir in os.listdir(DB_DIR_TEMP_PATH):
                if filedir.startswith("GeoLite2-City_"):
                    downloaded_dir = os.path.join(DB_DIR_TEMP_PATH, filedir)
                    break
                elif filedir.startswith("GeoIP2-City_"):
                    downloaded_dir = os.path.join(DB_DIR_TEMP_PATH, filedir)
                    break

            # Find downloaded file
            downloaded_file = None
            for filedir in os.listdir(downloaded_dir):
                if filedir.startswith("GeoLite2-City"):
                    downloaded_file = os.path.join(downloaded_dir, filedir)
                    logger.info(f"Downloaded MaxMind DB file: {downloaded_file}")
                    break
                elif filedir.startswith("GeoIP2-City"):
                    downloaded_file = os.path.join(downloaded_dir, filedir)
                    logger.info(f"Downloaded MaxMind DB file: {downloaded_file}")
                    break

            try:
                # Move extracted file to lookup_tmp location with updated file name
                shutil.move(downloaded_file, LOOKUP_FILE_LOCATION)
                logger.debug(f"MaxMind DB file added: {LOOKUP_FILE_LOCATION}")

                # Remove temp files
                logger.debug(f"Removing temp directories. {DB_DIR_TEMP_PATH} and {downloaded_dir}")
                shutil.rmtree(DB_DIR_TEMP_PATH)

            except Exception as e:
                logger.exception(f"Unable to perform file operations on MaxMind database file. {e}")
        else:
            err_msg = f"Unable to download Max Mind database. status_code={r.status_code}, Content: {r.content}"
            logger.error(err_msg)
            raise Exception(err_msg)

