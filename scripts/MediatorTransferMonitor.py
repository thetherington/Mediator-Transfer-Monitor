import datetime
import json
from xml.dom import minidom

import requests


class MediatorTransferMon:
    def __init__(self, **kwargs):

        self.host = None
        self.port = "8080"
        self.insite = None
        self.threshold = None
        self.route = "info/scripts/CGItoXML.exe/servicerequest"
        self.offline_doc = None
        self.findhostname = None

        self.request_params = {
            # "uniqueid": 535880,
            "hostname": None,
            "name": "turbine",
            "command": "TransferJobManager",
            "menuItem": "getActiveExecutors",
            "noxsl": None,
        }

        for key, value in kwargs.items():

            if "host" == key and value:
                self.host = value

            if "hostname" == key and value:

                if value == "_auto_":
                    self.findhostname = True
                else:
                    self.request_params["hostname"] = value

            if "port" in key and value:
                self.port = value

            if "insite" in key and value:
                self.insite = value

            if "threshold" in key and value:
                self.threshold = value

            if "local_file" in key:

                with open("config/" + value) as f:
                    content = [x for x in f.readlines()]

                self.offline_doc = minidom.parseString("".join(content))

        self.url = "http://{}:{}/{}".format(self.host, self.port, self.route)

    def findhost(self):

        query = {
            "size": 1,
            "query": {
                "bool": {
                    "must": [
                        {"match_phrase": {"metricset.module": {"query": "mediator_transfers"}}},
                        {"range": {"@timestamp": {"from": "now-5m", "to": "now"}}},
                    ]
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
        }

        url = "http://{}:9200/log-metric-*/_search".format(self.insite)

        try:

            resp = requests.get(url, data=json.dumps(query), timeout=30.0).json()

            self.request_params["hostname"] = resp["hits"]["hits"][-1]["_source"]["host"]

        except Exception:
            return None

    def fetch(self):

        if self.findhostname:
            self.findhost()

        try:

            resp = requests.get(
                self.url, params=self.request_params, headers={"Accept": "application/xml"}
            )
            resp.close()

            doc = minidom.parseString(str(resp.text))

            return doc

        except Exception:
            return None

    def process(self):
        def get_element(node, name):

            try:
                return node.getElementsByTagName(name)[0].firstChild.data

            except Exception:
                return None

        documents = []

        if not self.offline_doc:

            doc = self.fetch()

            if not doc:
                return documents

        else:
            doc = self.offline_doc

        for serviceInfo in doc.getElementsByTagName("ServiceInfo"):

            for executor in serviceInfo.getElementsByTagName("ExecutorMedia"):

                fields = {
                    "serviceName": get_element(serviceInfo, "ServiceName"),
                    "serviceHost": get_element(serviceInfo, "ServiceHostName"),
                    "mediaName": get_element(executor, "MediaName"),
                    "mediaOffline": get_element(executor, "MediaOffline"),
                    "mediaPendingTransfer": get_element(executor, "NumberOfPendingTransfers"),
                }

                for execinfo in executor.getElementsByTagName("ExecutorInfo"):

                    fields.update(
                        {
                            "destinationMatId": get_element(execinfo, "DestinationMatId"),
                            "jobID": get_element(execinfo, "JobId"),
                            "jobStartTime": get_element(execinfo, "JobStartTime"),
                            "transferProgress": get_element(execinfo, "TransferProgress"),
                        }
                    )

                for dt_format in [
                    "%Y-%m-%dT%H:%M:%S.%f",
                    "%Y-%m-%dT%H:%M:%S",
                ]:

                    try:

                        dt = datetime.datetime.strptime(fields["jobStartTime"], dt_format)
                        dt_delta = datetime.datetime.utcnow() - dt

                        fields.update(
                            {
                                "elapsed_seconds": int(dt_delta.total_seconds()),
                                "elapsed_minutes": int(dt_delta.total_seconds() / 60),
                                "d_elapsed_hours": round(dt_delta.total_seconds() / 60 / 60, 1),
                            }
                        )

                    except Exception:
                        continue

                document = {
                    "fields": fields,
                    "host": self.host,
                    "name": "transfers",
                }

                documents.append(document)

        # print(doc.toprettyxml())

        return documents


def main():

    params = {
        "host": "aws-core03.ironmam.mws.disney.com",
        "port": "8080",
        "insite": None,
        "theshold": None,
        "hostname": "_auto_",
        "local_file": "response.xml",
    }

    transfer = MediatorTransferMon(**params)

    print(json.dumps(transfer.process(), indent=1))


if __name__ == "__main__":
    # mediator
    main()

