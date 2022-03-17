#!/usr/bin/env python3

import argparse
import csv
import json
from pyDataverse.api import NativeApi
import sys

# arguments. persistentid and version are required, others optional.
parser = argparse.ArgumentParser(description='Download all files from a given dataset ID, in their original format.')
parser.add_argument('-d', '--dataverse', required=False, default='https://dataverse-awstest.irss.unc.edu', help='Dataverse URL. Defaults to https://dataverse-awstest.irss.unc.edu')
parser.add_argument('-l', '--list', required=False, help='file containing List of persistent IDs')
parser.add_argument('-p', '--persistentid', required=False, help='Persistent ID, in the format doi:authority/shoulder/identifier')
parser.add_argument('-o', '--output-file', required=True, help='Output file')
parser.add_argument('-v', '--version', required=False, help='Dataset version: 1.0, 2.1, \":draft\", \":latest\", \":latest-published\"')
parser.add_argument('-t', '--apitoken', required=False, help='API token. Required for unpublished/restricted datasets.')

# parse arguments
args = parser.parse_args()

#print(args)
#sys.exit()

BASE_URL = args.dataverse

if args.apitoken is None:
   API_TOKEN=''
else:
   API_TOKEN = args.apitoken

if args.persistentid is None:
    PID = ''
if (args.list is None) and (args.persistentid is None):
   sys.exit('Please provide either a persistentID or a file containing a list of persistentIDs.')

with open(args.output_file, 'w') as of:
    def export_dataset(BASE_URL, API_TOKEN, PID):
        api = NativeApi(BASE_URL, API_TOKEN)
        resp = api.get_dataset(PID)
        print(resp.json())
        #of.write(of)

if args.persistentid is not None:
    PID = args.persistentid
    export_dataset(BASE_URL, API_TOKEN, PID)

if args.list is not None:
   with open(args.list) as pid_file:
       pid_list = pid_file.readlines()
       for pid in pid_list:
           export_dataset(BASE_URL, API_TOKEN, PID)
of.close()