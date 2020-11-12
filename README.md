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
3. Enter the mediator server running information center in the _Hosts_ tab (can use DNS if it's available.
4. From the _Input_ tab change the _Type_ to __Python__
5. From the _Input_ tab change the _Metric Set Name_ field to __mediator__
6. Select the _Script_ tab, then paste the contents of __scripts/poller_config.py__ into the script panel.
7. Save changes, then restart the poller program.

## Testing:
_todo.._

## Sample Data Output:

```
[
 {
  "fields": {
   "jobID": "4065077",
   "serviceHost": "aws-core02",
   "mediaName": "AsperaKMTC",
   "transferProgress": null,
   "jobStartTime": "2020-11-12T14:20:42.190",
   "mediaPendingTransfer": "0",
   "elapsed_seconds": 10,
   "destinationMatId": "BOBS1221FXX0224",
   "elapsed_minutes": 0,
   "serviceName": "Turbine",
   "mediaOffline": "false",
   "d_elapsed_hours": 0.0
  },
  "name": "transfers",
  "host": "aws-core02"
 },
 {
  "fields": {
   "jobID": "4065076",
   "serviceHost": "aws-core02",
   "mediaName": "AsperaWoodlands",
   "transferProgress": "100",
   "jobStartTime": "2020-11-12T14:20:42.190",
   "mediaPendingTransfer": "0",
   "elapsed_seconds": 10,
   "destinationMatId": "BOBS1221FXX0224",
   "elapsed_minutes": 0,
   "serviceName": "Turbine",
   "mediaOffline": "false",
   "d_elapsed_hours": 0.0
  },
  "name": "transfers",
  "host": "aws-core02"
 }
]
```