import datetime
import json
from xml.dom import minidom
import copy

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
        self.logon = None
        self.headers = {"Accept": "application/xml"}
        self.system_name = None

        self.request_params = {
            # "uniqueid": 535880,
            "hostname": None,
            "name": "turbine",
            "command": "TransferJobManager",
            "menuItem": "getActiveExecutors",
            "noxsl": None,
        }

        for key, value in kwargs.items():

            if key == "host" and value:
                self.host = value

            if key == "hostname" and value:

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

            if "system_name" in key and value:
                self.system_name = value

            if "local_file" in key:

                with open("_files\\" + value, "r") as f:
                    content = [x for x in f.readlines()]

                self.offline_doc = minidom.parseString("".join(content))

        if "login" in kwargs.keys():

            self.login_params = {
                "uniqueid": 0,
                "command": "login",
                "noxsl": None,
                "user": kwargs["login"]["user"],
                "pass": kwargs["login"]["pass"],
                "successrequest": "",
            }

            self.logout_params = {
                "uniqueid": 0,
                "command": "logout",
                "noxsl": None,
            }

            self.logon = True

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

    def login(self, http_session):

        try:

            resp = http_session.post(
                self.url,
                data=self.login_params,
                headers={
                    "Accept": "application/xml",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=10.0,
            )

            if (
                "<Error>Username or password not recognized</Error>" not in resp.text
                or resp.status_code != 200
            ):

                return resp.status_code

        except Exception as e:
            print(e)

        print(resp.status_code)
        print(resp.text)

        return None

    def logout(self, http_session):

        try:

            http_session.get(
                self.url, params=self.logout_params, headers=self.headers, timeout=10.0
            )

        except Exception as e:
            print(e)

    def fetch(self):

        if self.findhostname:
            self.findhost()

        try:

            with requests.Session() as http_session:

                if self.logon:

                    # exit out of function if login failed
                    if not self.login(http_session):
                        return None

                resp = http_session.get(
                    self.url, params=self.request_params, headers=self.headers, timeout=20.0
                )

                doc = minidom.parseString(str(resp.text))

                if self.logon:
                    self.logout(http_session)

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

        for service_info in doc.getElementsByTagName("ServiceInfo"):

            for executor in service_info.getElementsByTagName("ExecutorMedia"):

                fields = {}

                fields = {
                    "serviceName": get_element(service_info, "ServiceName"),
                    "serviceHost": get_element(service_info, "ServiceHostName"),
                    "mediaName": get_element(executor, "MediaName"),
                    "mediaOffline": get_element(executor, "MediaOffline"),
                    "mediaPendingTransfer": get_element(executor, "NumberOfPendingTransfers"),
                }

                if self.system_name:
                    fields.update({"system": self.system_name})

                for execinfo in executor.getElementsByTagName("ExecutorInfo"):

                    executor_fields = {}

                    executor_fields.update(
                        {
                            "destinationMatId": get_element(execinfo, "DestinationMatId"),
                            "jobID": get_element(execinfo, "JobId"),
                            "jobStartTime": get_element(execinfo, "JobStartTime"),
                            "transferProgress": get_element(execinfo, "TransferProgress"),
                        }
                    )

                    for transferNodeExecutor in execinfo.getElementsByTagName(
                        "TransferNodeExecutor"
                    ):

                        executor_fields.update(
                            {
                                "executor": get_element(transferNodeExecutor, "Name"),
                                "status": get_element(transferNodeExecutor, "Status"),
                            }
                        )

                    try:

                        executor_fields["d_transferProgress_pct"] = (
                            int(executor_fields["transferProgress"]) / 100
                        )

                    except Exception:
                        pass

                    for dt_format in [
                        "%Y-%m-%dT%H:%M:%S.%f",
                        "%Y-%m-%dT%H:%M:%S",
                    ]:

                        try:

                            dt = datetime.datetime.strptime(
                                executor_fields["jobStartTime"], dt_format
                            )

                            dt_delta = datetime.datetime.utcnow() - dt

                            executor_fields.update(
                                {
                                    "elapsed_seconds": int(dt_delta.total_seconds()),
                                    "elapsed_minutes": int(dt_delta.total_seconds() / 60),
                                    "d_elapsed_hours": round(dt_delta.total_seconds() / 60 / 60, 1),
                                }
                            )

                        except Exception:
                            continue

                    _fields = copy.deepcopy(fields)

                    _fields.update(executor_fields)

                    document = {
                        "fields": _fields,
                        "host": _fields["serviceHost"],
                        "name": "transfers",
                    }

                    documents.append(document)

        # print(doc.toprettyxml())

        return documents


def main():

    params = {
        "host": "10.127.17.94",
        "port": "8080",
        "insite": None,
        "theshold": None,
        "hostname": "ip-10-127-17-94",
        "login": {"user": "evertz", "pass": "pharos1"},
        "system_name": "MAM_Production",
        # "local_file": "multiple_Executors.xml",
    }

    transfer = MediatorTransferMon(**params)

    print(json.dumps(transfer.process(), indent=1))


if __name__ == "__main__":
    # mediator
    main()
