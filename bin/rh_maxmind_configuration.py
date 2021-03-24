import json
import splunk.admin as admin
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
            mmdb_utils.CredentialManager(self.getSessionKey()).store_credential(mmdb_utils.MaxMindLicenseKeyInPasswordStore, maxmind_license_key)

            conf_info['action']['success'] = "MaxMind License key is stored successfully."

        except Exception as e:
            conf_info['action']['error'] = 'Error while storing license key. {}'.format(e)


if __name__ == "__main__":
    admin.init(MaxMindDBConfRestcall, admin.CONTEXT_APP_AND_USER)
