import sys

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration, Option
import mmdb_utils

import os, time, shutil, requests, tarfile
import splunk.appserver.mrsparkle.lib.util as splunk_lib_util

import logging
import logger_manager
logger = logger_manager.setup_logging('debugger', logging.DEBUG)


SPLUNK_ETC_APPS = splunk_lib_util.make_splunkhome_path(["etc", "apps"])

LICENSE_KEY = 'dlQTkFchOoJbYVOZ'

MaxMindDatabaseDownloadLink = 'https://download.maxmind.com/app/geoip_download?edition_id=GeoLite2-City&license_key={}&suffix=tar.gz'
App_Local_Path = os.path.join(SPLUNK_ETC_APPS, 'splunk_maxmind_db_auto_update', 'local')
DB_DIR_PATH = os.path.join(App_Local_Path, 'mmdb')
DB_TEMP_DOWNLOAD = os.path.join(DB_DIR_PATH, "temp_file.tar.gz")

search_lookup_dir = os.path.join(SPLUNK_ETC_APPS, 'search', 'lookups')
max_mind_db_lookup_dir = os.path.join(SPLUNK_ETC_APPS, 'splunk_maxmind_db_auto_update', 'lookups')



@Configuration(type='reporting')
class UpdateMaxMindDatabase(GeneratingCommand):

    command = Option(name="command", require=False, default="print")

    def download_mmdb_database(self, path_to_put_file):
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

        # Create necessary directory is not exist
        if not os.path.exists(App_Local_Path):
            os.makedirs(App_Local_Path)
        if not os.path.exists(DB_DIR_PATH):
            os.makedirs(DB_DIR_PATH)

        # NOTE - Please visit GitHub page (https://github.com/VatsalJagani/Splunk-App-Auto-Update-MaxMind-Database), if you are developer and want to help improving this App in anyways

        r = requests.get(MaxMindDatabaseDownloadLink.format(LICENSE_KEY), allow_redirects=True, proxies=proxies)
        
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
                shutil.move(downloaded_file, path_to_put_file)
                # remove temp files
                shutil.rmtree(downloaded_dir)
                os.remove(DB_TEMP_DOWNLOAD)
            except Exception as e:
                raise Exception("Unable to perform file operations on MaxMind database file. {}".format(e))
        else:
            raise Exception("Unable to download Max Mind database. status_code={}, Content: {}".format(r.status_code, r.content))


    def list_files(self, dir):
        files_str = ''
        for file in os.listdir(dir):
            if file.endswith(".mmdb"):
                files_str += 'File:{}, Modification-Date:{} || '.format(os.path.join(dir, file), time.ctime(os.path.getctime(os.path.join(dir, file))))
        return files_str


    def remove_file_if_exists(self, filePath):
        if os.path.exists(filePath):
            os.remove(filePath)
        

    def cleanup(self):

        for file in os.listdir(max_mind_db_lookup_dir):
            if file.endswith(".mmdb"):
                logger.info('Removing {} || '.format(file))
                self.remove_file_if_exists(os.path.join(max_mind_db_lookup_dir, file))
        
        for file in os.listdir(search_lookup_dir):
            if file.endswith(".mmdb"):
                logger.info('Removing {} || '.format(file))
                self.remove_file_if_exists(os.path.join(search_lookup_dir, file))


    def generate(self):
        try:
            # mmdb_utils.MaxMindDatabaseUtil(self.search_results_info.auth_token)

            logger.debug("command: {}".format(self.command))

            if self.command == 'print':
                max_mind_db_lookup_dir_files = self.list_files(max_mind_db_lookup_dir)
                logger.info("max_mind_db_lookup_dir_files: {}".format(max_mind_db_lookup_dir_files))

                max_mind_db_local_dir = os.path.join(SPLUNK_ETC_APPS, 'splunk_maxmind_db_auto_update', 'local')
                max_mind_db_local_dir_files = self.list_files(max_mind_db_local_dir)
                logger.info("max_mind_db_local_dir_files: {}".format(max_mind_db_local_dir_files))

                local_limits_conf = os.path.join(max_mind_db_local_dir, 'limits.conf')
                if os.path.isfile(local_limits_conf):
                    content = ''
                    with open(local_limits_conf, 'r') as f:
                        content = f.read()
                    logger.info('local limits.conf present: {}'.format(content))

                search_lookup_dir_files = self.list_files(search_lookup_dir)
                logger.info("search_lookup_dir_files: {}".format(search_lookup_dir_files))

            elif self.command == 'cleanup':
                self.cleanup()

            elif self.command == 'db_to_search_lookups':
                self.download_mmdb_database(search_lookup_dir)

            elif self.command == 'db_to_maxmind_lookups':
                self.download_mmdb_database(max_mind_db_lookup_dir)


            # Return Success Message
            logger.info("Return Success Message.")
            yield {"Message": "Max Mind Database updated successfully."}

        except Exception as e:
            yield {"Message": "{}".format(e)}
            logger.exception("{}".format(e))


dispatch(UpdateMaxMindDatabase, sys.argv, sys.stdin, sys.stdout, __name__)
