#!/usr/bin/python

from datetime import datetime
from os import listdir
from os.path import isfile, join
import argparse
import json
import os
import requests

# define arguments. persistentid, apitoken and file are required.
parser = argparse.ArgumentParser(description='Upload a file or directory of files to a given dataset.')
parser.add_argument('-d', '--dataverse', default='https://dataverse.unc.edu', help='Dataverse URL. Defaults to https://dataverse.unc.edu')
parser.add_argument('-p', '--persistentid', required=True, help='Persistent ID, in the format doi:authority/shoulder/identifier')
parser.add_argument('-t', '--apitoken', required=True, help='API token. Required.')
parser.add_argument('-f', '--file', required=True, help='File or directory to upload.')

# parse arguments
args = parser.parse_args()
dataverse = args.dataverse
persistentid = args.persistentid
apitoken = args.apitoken
file = args.file

def upload(file):

   # prepare file
   file_content = 'content: %s' % datetime.now()
   files = {'file': (file, file_content)}

   # construct url with persistent id
   url_persistent_id = '%s/api/datasets/:persistentId/add?persistentId=%s&key=%s' % (dataverse, persistentid, apitoken)

   # fire off request
   r = requests.post(url_persistent_id, files=files)
   print r.json()

if os.path.isfile(file):
   upload(file)

if os.path.isdir(file):
   filelist = [f for f in listdir(file) if isfile(join(file, f))]
   for file in filelist:
      upload(file)
