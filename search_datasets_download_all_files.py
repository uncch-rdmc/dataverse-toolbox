#!/usr/bin/env python

import argparse
import json
import os
import urllib2
import subprocess
import sys
import time

rows = 10
start = 0
page = 1
condition = True # emulate do-while

parser = argparse.ArgumentParser(description='Search a given Dataverse API for a given term, under an optional Dataverse alias')
parser.add_argument('-d', '--dataverse', default='https://dataverse-test.irss.unc.edu', help='Dataverse URL. Defaults to https://dataverse.unc.edu')
parser.add_argument('-q', '--query', default='*', help='Query term. Defaults to wildcard.')
parser.add_argument('-t', '--apitoken', help='API token. Required for searching.')
parser.add_argument('-s', '--subdataverse', help='Limit search to a sub-dataverse. Defaults to root.')
parser.add_argument('-o', '--outputdir', help='Output directory for dataset files, relative to CWD. Defaults to value of DatasetID.')

args = parser.parse_args()
# if no specified outputdir, construct from query and subdataverse (if provided)
if args.outputdir is None:
   args.outputdir = args.query
   if args.subdataverse is not None:
      args.outputdir = args.subdataverse+'_'+args.query
if args.apitoken is None:
   sys.exit ("An API token is required to call the search API.")
print "outputdir is "+args.outputdir

# construct search url
url = args.dataverse + '/api/search' + '?q=' + args.query + '&type=dataset&show_entity_ids=true&key=' + str(args.apitoken)
if args.subdataverse is not None:
   url = url + '&subtree=' + str(args.subdataverse)
print url

# create parent output directory
cwd = sys.path[0]
opd = str(args.outputdir)
fwd = cwd + '/' + opd
if os.path.exists(fwd) is False:
   os.mkdir(fwd)
print "using outputdir " + fwd

# dictionary for global_id/entity_id pairs as search results aren't necessarily unique
d = {}

# search API returns 10 entries at a time.
while (condition):
   url = url + "&start=" + str(start)
   data = json.load(urllib2.urlopen(url))
   total = data['data']['total_count']

   # iterate through result pages.
   for i in data['data']['items']:
      global_id = str(i['global_id'])
      entity_id = i['entity_id']
      id_array = global_id.split("/")
      identifier = str(id_array[1])
      subdir = fwd+'/'+identifier

      # only process each dataset once
      if d.get(entity_id) is None:
         # add identifier/entity_id key/value pair
         d[entity_id] = identifier
         # create dataset output directory
         dsoutput = fwd + '/' + identifier
         if os.path.exists(dsoutput) is False:
            os.mkdir(dsoutput)

         # get file metadata from the dataset. version should be :latest per mandy.
         dataseturl = args.dataverse + '/api/datasets/' + str(i['entity_id']) + '/versions/:latest/files'
         metadata = json.load(urllib2.urlopen(dataseturl))

         # iterate over metadata file ids
         for i in range(len(metadata["data"])):
            fileid = metadata["data"][i]["dataFile"]["id"]
            filename = metadata["data"][i]["label"]
            md5 = metadata["data"][i]["dataFile"]["md5"]
            #print str(fileid) + ': ' + filename

            # construct download URL
            fileurl = args.dataverse + '/api/access/datafile/' + str(fileid) + '?format=original&key='+str(args.apitoken)
            #print 'downloading from '+ fileurl

            # curl to present directory (sigh) but use filename.label as output
            # -s suppresses progress bar, -S shows errors, -o is the output path/file
            filepath = dsoutput + '/' + filename
            curlcmd = 'curl -s -S -o "' + filepath + '" ' + '\"' + fileurl + '\"'
            print 'performing '+curlcmd
            subprocess.call(curlcmd, shell=True)

            # give the disk a second
            time.sleep(1)

   start = start + rows
   condition = start < total
