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
            conf = bundle.getConf('app', sessionKey, namespace=mmdb_utils.APP_NAME, owner='nobody')
            stanza = conf.stanzas['install'].findKeys('is_configured')
            if stanza:
                if stanza["is_configured"] == "0" or stanza["is_configured"] == "false":
                    conf["install"]["is_configured"] = 'true'
                    rest.simpleRequest("/apps/local/{}/_reload".format(mmdb_utils.APP_NAME), sessionKey=sessionKey)
            else:
                conf["install"]["is_configured"] = 'true'
                rest.simpleRequest("/apps/local/{}/_reload".format(mmdb_utils.APP_NAME), sessionKey=sessionKey)
        except Exception as e:
            raise Exception('Unable to set is_configured parameter in local app.conf file. {}'.format(e))
    

    def handleEdit(self, conf_info):
        # Update the HoneyDB configuration
        try:
            data = json.loads(self.callerArgs['data'][0])
            maxmind_license_key = str(data['maxmind_database_license_key'])
        except Exception as e:
            conf_info['action']['error'] = 'Data is not in proper format. {} - {}'.format(e, self.callerArgs["data"])
            return

        try:
            # Store License Key
            mmdb_utils.CredentialManager(self.getSessionKey()).store_credential(mmdb_utils.MAXMIND_LICENSE_KEY_IN_PASSWORD_STORE, maxmind_license_key)

            self.app_configured()

            conf_info['action']['success'] = "MaxMind License key is stored successfully."

        except Exception as e:
            conf_info['action']['error'] = 'Error while storing license key. {}'.format(e)


if __name__ == "__main__":
    admin.init(MaxMindDBConfRestcall, admin.CONTEXT_APP_AND_USER)
