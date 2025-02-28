import asyncio
import boto3
import json
import websockets
import pyaudio

def lambda_handler(event, context):
    source_region = 'eu-central-1'
    transcribe = boto3.client('transcribe', region_name=source_region)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }