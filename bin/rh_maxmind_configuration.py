import json
import splunk.admin as admin
import splunk.bundle as bundle
import splunk.rest as rest
import mmdb_utils



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
            # set is_configure=true in app.conf
            rest.simpleRequest(
                '/servicesNS/nobody/{}/configs/conf-app/install'.format(mmdb_utils.APP_NAME),
                sessionKey=sessionKey,
                getargs={'output_mode':'json'},
                postargs={"is_configured": "true"},
                method='POST', raiseAllErrors=True)

            rest.simpleRequest("/apps/local/{}/_reload".format(mmdb_utils.APP_NAME), sessionKey=sessionKey)
        except Exception as e:
            raise Exception('Unable to set is_configured parameter in local app.conf file. {}'.format(e))


    def handleList(self, conf_info):
        # Get MaxMindDB Account ID
        try:
            _, serverContent = rest.simpleRequest("/servicesNS/nobody/{}/configs/conf-{}/{}?output_mode=json".format(mmdb_utils.APP_NAME, mmdb_utils.MMDB_CONF_FILE, mmdb_utils.MMDB_CONF_STANZA), sessionKey=self.getSessionKey())
            data = json.loads(serverContent)['entry']

            account_id = ''
            license_key = '******'
            for i in data:
                if i['name'] == mmdb_utils.MMDB_CONF_STANZA:
                    account_id = i['content']['account_id']
                    break
            conf_info['action']['maxmind_database_account_id'] = account_id
            conf_info['action']['maxmind_database_license_key'] = license_key
        except Exception as e:
            conf_info['action']['error'] = 'Unable to fetch the Account ID. {}'.format(e)    


    def handleEdit(self, conf_info):
        # Update the MaxMindDB configuration
        try:
            data = json.loads(self.callerArgs['data'][0])
            maxmind_account_id = str(data['maxmind_database_account_id'])
            maxmind_license_key = str(data['maxmind_database_license_key'])
        except Exception as e:
            conf_info['action']['error'] = 'Data is not in proper format. {} - {}'.format(e, self.callerArgs["data"])
            return

        try:
            # Store Account ID
            rest.simpleRequest("/servicesNS/nobody/{}/configs/conf-{}/{}?output_mode=json".format(mmdb_utils.APP_NAME, mmdb_utils.MMDB_CONF_FILE, mmdb_utils.MMDB_CONF_STANZA), postargs={'account_id': maxmind_account_id}, method='POST', sessionKey=self.getSessionKey())

            # Store License Key
            mmdb_utils.CredentialManager(self.getSessionKey()).store_credential(mmdb_utils.MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE, maxmind_license_key)

            self.app_configured()

            conf_info['action']['success'] = "MaxMind License key is stored successfully."

        except Exception as e:
            conf_info['action']['error'] = 'Error while storing license key. {}'.format(e)


if __name__ == "__main__":
    admin.init(MaxMindDBConfRestcall, admin.CONTEXT_APP_AND_USER)
