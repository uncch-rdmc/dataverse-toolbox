#!/usr/bin/python

import argparse
import hashlib
import json
import os
import requests
import subprocess
import time

# arguments. datasetid and version are required, others optional.
parser = argparse.ArgumentParser(description='Download all files from a given dataset ID, in their original format.')
parser.add_argument('-d', '--dataverse', default='https://dataverse.unc.edu', help='Dataverse URL. Defaults to https://dataverse.unc.edu')
parser.add_argument('-i', '--datasetid', type=int, required=True, help='Dataset ID, may be looked-up graphically via Files=>Upload dataset widget.')
parser.add_argument('-v', '--version', required=True, help='Dataset version. Required: 1.0, 2.1, \":draft\", \":latest\", \":latest-published\"')
parser.add_argument('-o', '--outputdir', help='Output directory for dataset files, relative to CWD. Defaults to value of DatasetID.')
parser.add_argument('-t', '--apitoken', help='API token. Required for private/restricted datasets.')

args = parser.parse_args()
if args.outputdir is None:
   args.outputdir = args.datasetid

cwd = os.getcwd()
opd = str(args.outputdir)
fwd = cwd + '/' + opd
if os.path.exists(fwd) is False:
   os.mkdir(fwd)

# get file metadata from the dataset
url = args.dataverse + '/api/datasets/' + str(args.datasetid) + '/versions/' + args.version + '/files'
#print "Requesting file metadata from " + url

if args.apitoken is not None:
   api = args.apitoken
   url = url + '?key=' + api

r = requests.get(url)
j = r.json()

# iterate over file ids, download to outputdir
for i in range(len(j["data"])):
   fileid = j["data"][i]["dataFile"]["id"]
   filename = j["data"][i]["label"]
   md5 = j["data"][i]["dataFile"]["md5"]
   #print str(fileid) + ': ' + filename

   # construct download URL
   dlurl = args.dataverse + '/api/access/datafile/' + str(fileid) + '?format=original'
   if args.apitoken is not None:
      dlurl = dlurl + '&key=' + api
   print "downloading from " + dlurl

   # curl to present directory (sigh) but use filename.label as output
   # -s suppresses progress bar, -S shows errors, -o is the output path/file
   fullpath = fwd + '/' + filename
   curlcmd = 'curl -s -S -o "' + fullpath + '" ' + '\"' + dlurl + '\"'
   print curlcmd
   subprocess.call(curlcmd, shell=True)

   # give the disk a second
   time.sleep(1)
   # check MD5z
   hash = hashlib.md5()
   with open(str(fullpath), 'rb') as afile:
      buf = afile.read()
      hash.update(buf)
      localmd5 = hash.hexdigest()

   if md5 == localmd5:
      print 'MD5 sums match: Dataverse ' + md5 + ' Local copy ' + localmd5
   else:
      print 'CHECKSUM ERROR: Dataverse ' + md5 + ' Local copy ' + localmd5

# Dataverse's JSON starts at zero like a proper count should.
count = i + 1
print str(count) + " files downloaded from dataset ID " + str(args.datasetid) + "."
