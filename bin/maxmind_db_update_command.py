import sys

from splunklib.searchcommands import dispatch, GeneratingCommand, Configuration
import mmdb_utils


@Configuration(type='reporting')
class UpdateMaxMindDatabase(GeneratingCommand):

    def generate(self):
        try:
            mmdb_utils.MaxMindDatabaseUtil(self.search_results_info.auth_token)

            # Return Success Message
            self.logger.info("Return Success Message.")
            yield {"Message": "Max Mind Database updated successfully."}

        except Exception as e:
            yield {"Message": "{}".format(e)}
            self.logger.error("{}".format(e))


dispatch(UpdateMaxMindDatabase, sys.argv, sys.stdin, sys.stdout, __name__)
