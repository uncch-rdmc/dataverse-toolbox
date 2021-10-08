#!/usr/bin/env python3

import argparse
import requests
import sys

parser = argparse.ArgumentParser(description='Search a given Dataverse API for a given term, under an optional Dataverse alias')
parser.add_argument('-d', '--dataverse', default='https://dataverse-awstest.irss.unc.edu', help='Dataverse URL. Defaults to https://dataverse-awstest.irss.unc.edu')
parser.add_argument('-c', '--collection', help='Sum the size of datasets in the given Dataverse collection.')
parser.add_argument('-a', '--all_collections', help='Report the sizes of all collections in the given Dataverse.', action='store_true')
parser.add_argument('-t', '--api_token', help='API token of an admin user.')

args = parser.parse_args()
if (args.collection is None) and (args.all_collections is False):
   sys.exit('Please specify a collection with -c, or -a for All collections.')

if args.api_token is None:
   sys.exit('Please provide the API token of an admin user with -t.')

if (args.collection is not None) and (args.all_collections is True):
   sys.exit('Please specify a collection or all collections, but not both.')

dataverse = args.dataverse
collection = args.collection
all = args.all_collections
token = args.api_token

def get_size(dataverse,collection,token):
    # throws I/O errors in TRSA case
    #dvurl = dataverse + '/api/dataverses/' + collection + '/storagesize?includeCached=true&key=' + token
    dvurl = dataverse + '/api/dataverses/' + collection + '/storagesize?key=' + token
    r = requests.get(dvurl)
    j = r.json()
    message = j["data"]["message"]
    # strip out "size of this ... bytes"
    size = int(''.join(filter(str.isdigit, message)))
    print(collection + ': ' + str(size))

# collection specified
if all is False:
   get_size(dataverse,collection,token)
else:
   # iterate through collections
   instanceurl = dataverse + '/api/dataverses/root/contents'
   r = requests.get(instanceurl)
   j = r.json()
   for i in range(len(j["data"])):
       collectionid = j["data"][i]["id"]
       type = j["data"][i]["type"]
       if (type == 'dataverse'):
          # get collection alias
          aliasurl = dataverse + '/api/dataverses/' + str(collectionid)
          ar = requests.get(aliasurl)
          aj = ar.json()
          alias = aj["data"]["alias"]
          # throws I/O errors in TRSA case
          #dvurl = dataverse + '/api/dataverses/' + alias + '/storagesize?includeCached=true&key=' + token
          dvurl = dataverse + '/api/dataverses/' + alias + '/storagesize?key=' + token
          dr = requests.get(dvurl)
          dj = dr.json()
          message = dj["data"]["message"]
          size = int(''.join(filter(str.isdigit, message)))
          print(alias + ': ' + str(size))
