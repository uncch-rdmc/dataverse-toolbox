#!/usr/bin/env python3

import argparse
import requests
import sys
import math

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
    # strip out "size of this ... bytes"
    error = "Couldn't get storagesize for collection: " + collection
    try:
       message = j["data"]["message"]
    except Exception as ex:
       print(error)
    size = int(''.join(filter(str.isdigit, message)))
    return size

def get_filecount(dataverse,collection,token):
    dvfilecount = 0
    dvcontentsurl = dataverse + '/api/dataverses/' + collection + '/contents'
    dvcr = requests.get(dvcontentsurl)
    dvcj = dvcr.json()
    # iterate over collection contents json
    for i in range(len(dvcj["data"])):
        id = dvcj["data"][i]["id"]
        type = dvcj["data"][i]["type"]
        if (type == 'dataset'):
           dscontentsurl = dataverse + '/api/datasets/' + str(id) + '/versions/:latest/files'
           dscr = requests.get(dscontentsurl)
           dscj = dscr.json()
           try:
               dsfilecount = len(dscj["data"])
           except:
               dsfilecount = 0
           dvfilecount = dvfilecount + dsfilecount
    return dvfilecount

# Function for converting bytes to more human-readable B, KB, MB, etc
def format_size(byte_size):
   if byte_size == 0:
       return '0B'
   size_name = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')
   i = int(math.floor(math.log(byte_size, 1024)))
   p = math.pow(1024, i)
   s = round(byte_size / p, 2)
   return '%s %s' % (s, size_name[i])

# collection specified
if all is False:
   size = get_size(dataverse,collection,token)
   readablesize = format_size(size)
   dvfilecount = get_filecount(dataverse,collection,token)
   print(collection + ': ' + str(size) + ' bytes' + ' (' + readablesize + '), ' + str(dvfilecount) + ' files.')
   
else:
   # start with the root dataverse
   collection = 'root'
   size = get_size(dataverse,collection,token)
   dvfilecount = get_filecount(dataverse,collection,token)
   print(collection + ': ' + str(size) + ' bytes, ' + str(dvfilecount) + ' files.')
   # now iterate through sub-collections
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
          collection = aj["data"]["alias"]
          size = get_size(dataverse,collection,token)
          dvfilecount = get_filecount(dataverse,collection,token)
          print(collection + ': ' + str(size) + ' bytes' + ' (' + readablesize + '), ' + str(dvfilecount) + ' files.')
