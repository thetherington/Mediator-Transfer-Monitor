import json
from MediatorTransferMonitor import MediatorTransferMon
from insite_plugin import InsitePlugin


class Plugin(InsitePlugin):
    def can_group(self):
        return False

    def fetch(self, hosts):

        host = hosts[-1]

        try:

            self.collector

        except Exception:

            params = {
                "host": host,
                "port": "8080",
                "insite": None,
                "hostname": "ip-10-127-17-94",
                "login": {"user": "evertz", "pass": "pharos1"},
                "system_name": "MAM_Production",
            }

            self.collector = MediatorTransferMon(**params)

        return json.dumps(self.collector.process())
