import argparse
import httplib2
import os
import sys
import json
import time
import datetime
import io
import hashlib
from random import randint
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from apiclient.http import MediaIoBaseDownload
from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Cipher import Blowfish
import binascii

password='googlecloud'
file_name='D:\\j.jpg'
key=hashlib.sha256(password).digest()


def pad(s):
    
    return s + b"\0" * (AES.block_size - len(s) % AES.block_size)



def PKCS5Padding(string):
    byteNum = len(string)
    packingLength = 8 - byteNum % 8
    appendage = chr(packingLength) * packingLength
    return string + appendage

def encrypt(message, key):
    c1  = Blowfish.new(key, Blowfish.MODE_ECB)
    packedString = PKCS5Padding(message)
    return c1.encrypt(packedString)

def decrypt(ciphertext, key):
    iv=ciphertext[:AES.block_size]
    cipher= AES.new(key, AES.MODE_CBC, iv)
    plaintext= cipher.decrypt(ciphertext[AES.block_size:])
   # print "pi:"+plaintext
    #print iv
    #print plaintext.rstrip(b"\0")
    return plaintext.rstrip(b"\0")

def encrypt_file(file_name, key):
    with open(file_name, "rb") as f:
        fi=f.read()
        print fi
    encry= encrypt(fi,key)
    with open(file_name,"wb") as f1:
        f1.write(encry)
    f.close()
    return file_name
   # print encry
    

def decrypt_file(file_name, key):
    with open(file_name, "rb") as f:
        fi=f.read()
    #print fi
    decry= decrypt(fi,key)
    with open(file_name.split(".")[0]+".dec","wb") as f1:
        f1.write(decry)
    f.close()
    #print decry

_BUCKET_NAME='barae'
_API_VERSION='v1'


parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

CLIENT_SECRETS= os.path.join(os.path.dirname(__file__),'client_secret.json')
FLOW= client.flow_from_clientsecrets(CLIENT_SECRETS,
    scope=[
        'https://www.googleapis.com/auth/devstorage.full_control',
        'https://www.googleapis.com/auth/devstorage.read_only',
        'https://www.googleapis.com/auth/devstorage.read_write',
    ],

    message=tools.message_if_missing(CLIENT_SECRETS))

def get(service):
  #User can be prompted to input file name(using raw_input) that needs to be be downloaded, 
  #as an example file name is hardcoded for this function.
  try:
# Get Metadata
        print 'inside get'
        fn= raw_input('Enter the filename:')
        req = service.objects().get(
                bucket=_BUCKET_NAME,
                object= fn,
                fields='bucket,name,metadata(my-key)',    
        
            )                   
        resp = req.execute()
        print json.dumps(resp, indent=2)

# Get Payload Data
        req = service.objects().get_media(
                bucket=_BUCKET_NAME,
                object=fn,
                )    
# The BytesIO object may be replaced with any io.Base instance.
        fh = io.BytesIO()
        decodefile=fn
        downloader = MediaIoBaseDownload(fh, req, chunksize=1024*1024) #show progress at download
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print 'Download %d%%.' % int(status.progress() * 100)
            print 'Download Complete!'
            print fh.getvalue()
            dec = decrypt(fh.getvalue(),key)
            with open(decodefile, 'wb') as fo:
                fo.write(dec)
        print json.dumps(resp, indent=2)
        
  except client.AccessTokenRefreshError:
    print ("Error in the credentials")

    #Puts a object into file after encryption and deletes the object from the local PC.
def put(service):
    
    
    with open('keys.fish', "r") as f:
        fi=f.read()
        strin= fi.split(',')
        filetobeenc=strin[0]
        keytobeenc=strin[1]    
        req = service.objects().insert(media_body=filetobeenc,name=filetobeenc,bucket=_BUCKET_NAME)
        resp = req.execute()
        print '> Uploaded source file %s' 
        print json.dumps(resp, indent=2)
    with open('keys.fish', "r") as f:
        fi=f.read()
        strin= fi.split(',')
        filetobeenc=strin[0]
        keytobeenc=strin[1]
        print 'inside enc'
        filename=encrypt_file(filetobeenc,keytobeenc)
    
        
    

#Lists all the objects from the given bucket name
def listobj(service):
    req = service.buckets().get(bucket=_BUCKET_NAME)
    resp = req.execute()
    print json.dumps(resp, indent=2)

    # Create a request to objects.list to retrieve a list of objects.
    fields_to_return = \
        'nextPageToken,items(name,size,contentType,metadata(my-key))'
    req = service.objects().list(bucket=_BUCKET_NAME, fields=fields_to_return)

    # If you have too many items to list in one request, list_next() will
    # automatically handle paging with the pageToken.
    while req is not None:
        resp = req.execute()
        print json.dumps(resp, indent=2)
        req = service.objects().list_next(req, resp)
    

#This deletes the object from the bucket
def deleteobj(service):
    obj=raw_input('enter the obj to be deleted')
    req = service.objects().delete(
    bucket=_BUCKET_NAME,
    object=obj,
           
    )                   
    resp = req.execute()

	
def main(argv):
  # Parse the command-line flags.
  flags = parser.parse_args(argv[1:])
  print argv[0]
  
  #sample.dat file stores the short lived access tokens, which your application requests user data, attaching the access token to the request.
  #so that user need not validate through the browser everytime. This is optional. If the credentials don't exist 
  #or are invalid run through the native client flow. The Storage object will ensure that if successful the good
  # credentials will get written back to the file (sample.dat in this case). 
  storage = file.Storage('sample.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(FLOW, storage, flags)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Construct the service object for the interacting with the Cloud Storage API.
  service = discovery.build('storage', _API_VERSION, http=http)

  #This is kind of switch equivalent in C or Java.
  #Store the option and name of the function as the key value pair in the dictionary.
  options = {1: put, 2: get, 3:listobj, 4:deleteobj}
  
  
  while True:

      op= raw_input('give path to list all files in it:')
      lis=os.listdir(op)
      print lis
      leng= len(lis)
      for l in range(leng):
          maskey= raw_input('enter a key for the file: -'+lis[l])
          random= randint(10000, 99999)
          randmas=maskey+str(random)
          print randmas
          
          with open('keys.fish', 'a') as fo:
                fo.write(lis[l]+','+randmas+'\n')
          
      option = int (raw_input('Enter the option: '))
  #Take the input from the user to perform the required operation.
  #for example if user gives the option 1, then it executes the below line as put(service) which calls the put function defined above.
      
  
      options[option](service)
  #if option not in options:
   #   print "enter valid option"

 # deleteobj(service)


if __name__ == '__main__':
  main(sys.argv)
# [END all]
    






