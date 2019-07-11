#!/usr/bin/python

import argparse
import hashlib
import json
import os
import requests
import subprocess
import time

# arguments. persistentid and version are required, others optional.
parser = argparse.ArgumentParser(description='Download all files from a given dataset ID, in their original format.')
parser.add_argument('-d', '--dataverse', default='https://dataverse.unc.edu', help='Dataverse URL. Defaults to https://dataverse.unc.edu')
parser.add_argument('-p', '--persistentid', required=True, help='Persistent ID, in the format doi:authority/shoulder/identifier')
parser.add_argument('-v', '--version', required=True, help='Dataset version. Required: 1.0, 2.1, \":draft\", \":latest\", \":latest-published\"')
parser.add_argument('-o', '--outputdir', help='Output directory for dataset files, relative to CWD. Defaults to value of DatasetID.')
parser.add_argument('-t', '--apitoken', help='API token. Required for private/restricted datasets.')

args = parser.parse_args()
if args.outputdir is None:
   opd = args.persistentid.split('/')[-1]
else:
   opd = args.outputdir

cwd = os.getcwd()
fwd = cwd + '/' + opd
if os.path.exists(fwd) is False:
   os.mkdir(fwd)

# get file metadata from the dataset
url = args.dataverse + '/api/datasets/:persistentId/versions/' + args.version + '/files?persistentId=' + args.persistentid
print "Requesting file metadata from " + url

if args.apitoken is not None:
   api = args.apitoken
   url = url + '&key=' + api

r = requests.get(url)
j = r.json()

# iterate over file ids, download to outputdir
for i in range(len(j["data"])):
   fileid = j["data"][i]["dataFile"]["id"]
   filename = j["data"][i]["label"]
   fullpath = fwd + '/' + filename
   md5 = j["data"][i]["dataFile"]["md5"]
   #print str(fileid) + ': ' + filename

   # does file already exist? do md5s match?
   if os.path.isfile(fullpath) is True:
     hash = hashlib.md5()
     with open(str(fullpath), 'rb') as afile:
       buf = afile.read()
       hash.update(buf)
       prevmd5 = hash.hexdigest()
       if md5 == prevmd5:
          print("MD5 match: " + fullpath)
          continue
   else:
     # file not present or md5 mismatch.
     dlurl = args.dataverse + '/api/access/datafile/' + str(fileid) + '?format=original'
     if args.apitoken is not None:
        dlurl = dlurl + '&key=' + api
        print "downloading from " + dlurl

        # curl to present directory (sigh) but use filename.label as output
        # -s suppresses progress bar, -S shows errors, -L follows redirects, -o is the output path/file
        curlcmd = 'curl -s -S -L -o "' + fullpath + '" ' + '\"' + dlurl + '\"'
        subprocess.call(curlcmd, shell=True)

        # give slow disks a second
        time.sleep(1)

        # check md5 against downloaded file
        hash = hashlib.md5()
        with open(str(fullpath), 'rb') as afile:
          buf = afile.read()
          hash.update(buf)
          localmd5 = hash.hexdigest()

        if md5 == localmd5:
           print 'MD5 match: Dataverse ' + md5 + ' Local copy ' + localmd5
        else:
           print 'CHECKSUM ERROR: Dataverse ' + md5 + ' Local copy ' + localmd5

# Dataverse's JSON starts at zero like a proper count should.
count = i + 1
print str(count) + " files downloaded from dataset ID " + str(args.persistentid) + "."
