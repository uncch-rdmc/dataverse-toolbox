#!/usr/bin/env python3

import argparse
import json
import requests
import ssl

# default to dataverse-awstest.irss.unc.edu
parser = argparse.ArgumentParser(description='Pull desired metrics from Dataverse API')
parser.add_argument('-d', '--dataverse', default='https://dataverse-awstest.irss.unc.edu', help='Dataverse URL. Defaults to https://dataverse-awstest.irss.unc.edu')

args = parser.parse_args()
api_prefix = "/api/info/metrics/"

metrics = ['dataverses','datasets','files','downloads']

# function to call each aggregate API endpoint
def call_api(metric):
    url = args.dataverse + api_prefix + metric
    r = requests.get(url)
    j = r.json()
    result = j["data"]["count"]
    return result

# fire at will
for metric in metrics:
    result = call_api(metric)
    print("Total " + metric + ": " + str(result))
