# Mediator Transfer Monitor

Mediator Transfer Monitoring collection module for the inSITE poller program. Module uses the Mediator Information Center web page to collect all the active transfers in the entire system.  Module uses the CGItoXML.exe API program for collecting information.

The transfer monitor collection module has the below distinct abilities and features:

1. Discovers automatically all the active transfers.
2. Calculates the time duration in seconds, minutes and hours of each active transfers.
3. Collects transfer progress.

## Minimum Requirements:

- inSITE Version 10.3 and service pack 6
- Python3.7 (_already installed on inSITE machine_)
- Python3.7 xml.dom (_already installed on inSITE machine_)

## Installation:

Installation of the transfer monitoring module requires copying the main script into the poller modules folder:

1. Copy __MediatorTransferMonitor.py__ script to the poller python modules folder:

   ```
    cp scripts/MediatorTransferMonitor.py /opt/evertz/insite/parasite/applications/pll-1/data/python/modules/
   ```
2. Restart the poller application

## Configuration:

To configure a poller to use the module start a new python poller configuration outlined below

1. Click the create a custom poller from the poller application settings page.
2. Enter a Name, Summary and Description information.
3. Enter the mediator server running information center in the _Hosts_ tab (can use DNS if it's available).
4. From the _Input_ tab change the _Type_ to __Python__
5. From the _Input_ tab change the _Metric Set Name_ field to __mediator__
6. Select the _Script_ tab, then paste the contents of __scripts/poller_config.py__ into the script panel.
7. Update the parameters "system_name" and "login" with the correct information.  
   __Insert the correct hostname for the mediator node running the transfer service.__

```
            params = {
                "host": host,
                "port": "8080",
                "insite": None,
                "hostname": "ip-10-127-17-94",
                "login": {"user": "evertz", "pass": "pharos1"},
                "system_name": "MAM_Production",
            }
```

      Note: If the Mediator Information center does not require a user credentials, remove the "login" parameter from the params dictionary.

      Note: You can use the value "_auto_" in the hostname to have the script figure out the correct hostname of the node running the transfer service.  Update the "insite" parameter with the ip address of the insite system for auto hostname lookup mode to work. For this to work, the mediator metrics collection has to be fully working

8. Save changes, then restart the poller program.

## Testing:
_todo.._

## Sample Data Output:

```
[
 {
  "fields": {
   "serviceName": "Turbine",
   "serviceHost": "aws-core02",
   "mediaName": "CommercialStaging",
   "mediaOffline": "false",
   "mediaPendingTransfer": "1",
   "system": "MAM_Production",
   "destinationMatId": "MEDX-CM81339",
   "jobID": "1856634",
   "jobStartTime": "2020-07-29T21:34:20.808",
   "transferProgress": null,
   "executor": "CommercialStagingExecutor-0",
   "status": "In Use",
   "elapsed_seconds": 19341354,
   "elapsed_minutes": 322355,
   "d_elapsed_hours": 5372.6
  },
  "host": "aws-core02",
  "name": "transfers"
 },
 {
  "fields": {
   "serviceName": "Turbine",
   "serviceHost": "aws-core02",
   "mediaName": "S3Browse",
   "mediaOffline": "false",
   "mediaPendingTransfer": "1",
   "system": "MAM_Production",
   "destinationMatId": "MEDX_PJCP0450100H",
   "jobID": "2028953",
   "jobStartTime": "2020-08-04T17:41:34.672",
   "transferProgress": "59",
   "executor": "S3BrowseExecutor-0",
   "status": "In Use",
   "d_transferProgress_pct": 0.59,
   "elapsed_seconds": 18836920,
   "elapsed_minutes": 313948,
   "d_elapsed_hours": 5232.5
  },
  "host": "aws-core02",
  "name": "transfers"
 },
 {
  "fields": {
   "serviceName": "Turbine",
   "serviceHost": "aws-core02",
   "mediaName": "StoreStaging",
   "mediaOffline": "false",
   "mediaPendingTransfer": "2",
   "system": "MAM_Production",
   "destinationMatId": "MEDX_PJCP0450100H",
   "jobID": "2028954",
   "jobStartTime": "2020-08-04T17:41:34.675",
   "transferProgress": null,
   "executor": "StoreStagingExecutor-0",
   "status": "In Use",
   "elapsed_seconds": 18836920,
   "elapsed_minutes": 313948,
   "d_elapsed_hours": 5232.5
  },
  "host": "aws-core02",
  "name": "transfers"
 }
]
```