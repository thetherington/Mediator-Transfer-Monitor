import datetime
import json
from xml.dom import minidom
import copy

import requests


class findActiveTransferHost:
    def __init__(self):

        self.request_transfer_manager = {
            "uniqueid": None,
            "command": "TransferJobManager",
            "noxsl": None,
        }

        self.request_services_params = {
            "uniqueid": 0,
            "command": "getservices",
            "noxsl": None,
        }

        self.refresh_hostname_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=15)

        self.refresh_hostname()

    def refresh_hostname(self):

        try:

            dt_delta = datetime.datetime.utcnow() - self.refresh_hostname_time

            if dt_delta.total_seconds() > 300:

                hostname = self.insite_lookup() if self.insite else self.infocenter_lookup()

                if hostname:

                    self.request_params["hostname"] = hostname
                    self.refresh_hostname_time = datetime.datetime.utcnow()

                    print("updated refresh", self.refresh_hostname_time)

        except Exception:
            pass

    def infocenter_lookup(self):
        def get_element(node, name):

            try:
                return node.getElementsByTagName(name)[0].firstChild.data

            except Exception:
                return None

        active_hostname = None

        with requests.Session() as http_session:

            if self.logon:

                # exit out of function if login failed
                if not self.login(http_session):
                    return None

            try:

                # get the uniqueid first for the info center host
                resp = http_session.get(
                    self.url,
                    params=self.request_services_params,
                    headers=self.headers,
                    timeout=10.0,
                )

                doc = minidom.parseString(str(resp.text))

                # iterate through a large list of service registration hosts
                for service in doc.getElementsByTagName("ServiceReg"):

                    # match to the init info center host
                    if (
                        get_element(service, "Host") == self.host
                        and get_element(service, "Name") == "Turbine"
                    ):

                        self.request_transfer_manager["uniqueid"] = int(
                            get_element(service, "UniqueID")
                        )

                        # get the active hostname from the job center
                        resp_transfer_manager = http_session.get(
                            self.url,
                            params=self.request_transfer_manager,
                            headers=self.headers,
                            timeout=5.0,
                        )

                        doc_transfer_manager = minidom.parseString(str(resp_transfer_manager.text))

                        for service_reg in doc_transfer_manager.getElementsByTagName(
                            "ServiceRegistrationInfo"
                        ):

                            active_hostname = get_element(service_reg, "ActiveHostname")

                        # exit iteration of all services
                        break

            except Exception as e:
                print(e)

            if self.logon:
                self.logout(http_session)

        return active_hostname

    def insite_lookup(self):

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

            return resp["hits"]["hits"][-1]["_source"]["host"]

        except Exception:
            return None


class MediatorTransferMon(findActiveTransferHost):
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

        if self.findhostname:
            findActiveTransferHost.__init__(self)

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

            if self.findhostname:

                self.refresh_hostname()

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
        "host": "10.127.3.80",
        "port": "8080",
        "insite": None,
        "theshold": None,
        "hostname": "_auto_",
        "login": {"user": "evertz", "pass": "pharos1"},
        "system_name": "MAM_Production",
        # "local_file": "response.xml",
    }

    transfer = MediatorTransferMon(**params)

    inputQuit = False

    while inputQuit is not "q":

        print(json.dumps(transfer.process(), indent=1))

        inputQuit = input("\nType q to quit or just hit enter: ")


if __name__ == "__main__":
    # mediator
    main()
