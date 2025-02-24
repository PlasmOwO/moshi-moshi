import boto3
import time
import urllib
import json


job_name = 'job name'
job_uri = 'https://s3.amazonaws.com/bucket_name/file_name.mp3'
# try to use python voice
Transcribe = boto3.client('transcribe', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name='us-east-1')