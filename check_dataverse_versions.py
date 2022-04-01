#!/usr/bin/env python3

import json
import requests
import ssl

# get current list of installations
all_installations = "https://raw.githubusercontent.com/IQSS/dataverse-metrics/master/global/all-dataverse-installations.json"
r = requests.get(all_installations)
j = r.json()

# get list of urls, iterate, retrieve version
for i in range(len(j["installations"])):
   hostname = j["installations"][i]["hostname"]
   url = "https://" + hostname + "/api/info/version"

   # if an installation throws an error/timeout, move on.
   try:
      ver = requests.get(url)
   except:
      pass

   # if an installation returns an invalid response, move on.
   try:
      verj = ver.json()
      version = verj["data"]["version"]
      print(hostname + "," + version)
   except:
      pass
