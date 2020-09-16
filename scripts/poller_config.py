import json
from MediatorTransferMonitor import MediatorTransferMon
from insite_plugin import InsitePlugin


class Plugin(InsitePlugin):
    def can_group(self):
        return False

    def fetch(self, hosts):

        try:

            self.collector

        except Exception:

            params = {
                "host": "aws-core03.ironmam.mws.disney.com",
                "port": "8080",
                "insite": None,
                "theshold": None,
            }

            self.collector = MediatorTransferMon(**params)

        return json.dumps(self.collector.process)
