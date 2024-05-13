import json
import splunk.admin as admin
import splunk.rest as rest
import mmdb_utils


import logging
import logger_manager
logger = logger_manager.setup_logging('rh', logging.DEBUG)



class MaxMindDBConfRestcall(admin.MConfigHandler):
    '''
    Set up supported arguments
    '''

    # Static variables
    def setup(self):
        """
        Sets the input arguments
        :return:
        """

        # Set up the valid parameters
        for arg in ['data']:
            self.supportedArgs.addOptArg(arg)


    def app_configured(self):
        sessionKey = self.getSessionKey()
        try:
            logger.info("Configuring app.conf is_configured.")
            # set is_configure=true in app.conf
            rest.simpleRequest(
                f'/servicesNS/nobody/{mmdb_utils.APP_NAME}/configs/conf-app/install',
                sessionKey=sessionKey,
                getargs={'output_mode':'json'},
                postargs={"is_configured": "true"},
                method='POST', raiseAllErrors=True)

            rest.simpleRequest(f"/apps/local/{mmdb_utils.APP_NAME}/_reload", sessionKey=sessionKey)
        except Exception as e:
            err_msg = f'Unable to set is_configured parameter in local app.conf file. {e}'
            logger.error(err_msg)
            raise Exception(err_msg)


    def handleList(self, conf_info):
        # Get MaxMindDB Account ID
        try:
            logger.info("MaxMind Account details GET request.")

            _, serverContent = rest.simpleRequest(f"/servicesNS/nobody/{mmdb_utils.APP_NAME}/configs/conf-{mmdb_utils.MMDB_CONF_FILE}/{mmdb_utils.MMDB_CONF_STANZA}?output_mode=json", sessionKey=self.getSessionKey())
            data = json.loads(serverContent)['entry']

            account_id = ''
            license_key = '******'
            mmdb_config_proxy_url = 'None'
            # is_ssl_verify = True

            try:
                logger.info("MaxMind getting the proxy url from passwords.conf")
                mmdb_config_proxy_url = mmdb_utils.CredentialManager(self.getSessionKey())\
                    .get_credential(mmdb_utils.MAXMIND_PROXY_URL_IN_PASSWORD_STORE)
            except:
                logger.info("There is no proxy details found in passwords.conf")

            for i in data:
                if i['name'] == mmdb_utils.MMDB_CONF_STANZA:
                    account_id = i['content']['account_id']
                    # is_ssl_verify = i['content']['is_ssl_verify']
                    break
            conf_info['action']['maxmind_database_account_id'] = account_id
            conf_info['action']['maxmind_database_license_key'] = license_key
            conf_info['action']['mmdb_config_proxy_url'] = mmdb_config_proxy_url
            # conf_info['action']['mmdb_config_is_ssl_verify'] = is_ssl_verify
        except Exception as e:
            err_msg = f'Unable to fetch the Account ID. {e}'
            logger.exception(err_msg)
            conf_info['action']['error'] = err_msg


    def handleEdit(self, conf_info):
        # Update the MaxMindDB configuration
        try:
            logger.info("MaxMind Account details POST request.")

            data = json.loads(self.callerArgs['data'][0])
            maxmind_account_id = str(data['maxmind_database_account_id'])
            maxmind_license_key = str(data['maxmind_database_license_key'])
            mmdb_config_proxy_url = str(data['mmdb_config_proxy_url'])
            # mmdb_config_is_ssl_verify = data['mmdb_config_is_ssl_verify']
        except Exception as e:
            err_msg = f'Data is not in proper format. {e}'
            logger.error(err_msg)
            conf_info['action']['error'] = err_msg
            return

        try:
            logger.info("Storing the Account ID.")
            # Store Account ID
            rest.simpleRequest(f"/servicesNS/nobody/{mmdb_utils.APP_NAME}/configs/conf-{mmdb_utils.MMDB_CONF_FILE}/{mmdb_utils.MMDB_CONF_STANZA}?output_mode=json",
                               postargs={'account_id': maxmind_account_id},   # , 'is_ssl_verify': mmdb_config_is_ssl_verify},
                               method='POST',
                               sessionKey=self.getSessionKey()
                            )

            logger.info("Storing the License Key in passwords.conf.")
            # Store License Key
            mmdb_utils.CredentialManager(self.getSessionKey()).store_credential(mmdb_utils.MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE, maxmind_license_key)

            logger.info("Storing the Proxy URL in passwords.conf.")
            # Store Proxy URL
            if mmdb_config_proxy_url != '******':
                mmdb_utils.CredentialManager(self.getSessionKey()).store_credential(mmdb_utils.MAXMIND_PROXY_URL_IN_PASSWORD_STORE, mmdb_config_proxy_url)

            self.app_configured()

            success_msg = "MaxMind License key is stored successfully."
            logger.info(success_msg)
            conf_info['action']['success'] = success_msg

        except Exception as e:
            err_msg = f'Error while storing license key. {e}'
            logger.exception(err_msg)
            conf_info['action']['error'] = err_msg


if __name__ == "__main__":
    admin.init(MaxMindDBConfRestcall, admin.CONTEXT_APP_AND_USER)
