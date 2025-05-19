from flask import Flask, jsonify, send_from_directory
import boto3
import datetime
import urllib.parse
import hashlib
import hmac
import asyncio
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

app = Flask(__name__, static_url_path='', static_folder='.')

REGION = 'eu-central-1'
LANGUAGE_CODE = 'ja-JP'
SAMPLE_RATE = 16000

# session = boto3.Session()
# credentials = session.get_credentials().get_frozen_credentials()

# Client amazon translate
translate_client = boto3.client('translate', region_name="eu-central-1")


# def sign(key, msg):
#     return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

# def get_signature_key(key, date_stamp, region_name, service_name):
#     k_date = sign(('AWS4' + key).encode('utf-8'), date_stamp)
#     k_region = sign(k_date, region_name)
#     k_service = sign(k_region, service_name)
#     k_signing = sign(k_service, 'aws4_request')
#     return k_signing
# Gestionnaire personnalisé pour traiter et traduire les résultats de transcription
class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                original_text = alt.transcript
                #Executer la trad en parallele
                response = await asyncio.to_thread(
                    translate_client.translate_text,
                    Text=original_text,
                    SourceLanguageCode="ja",
                    TargetLanguageCode="fr"
                )
                translated_text = response.get("TranslatedText", "")
                print(f"Original : {original_text}")
                print(f"Traduction : {translated_text}\n")

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/get-transcribe-url')
async def transcribe_stream(queue):
    #Creation client AWS Transcribe
    client = TranscribeStreamingClient(region="eu-central-1")
    
    stream = await client.start_stream_transcription(
        language_code="ja-JP",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )
    
    async def send_audio():
        while True:
            audio_chunk = await queue.get()
            if audio_chunk is None:  # Signal de fin (TODO)
                break
            await stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
        await stream.input_stream.end_stream()
    
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(send_audio(), handler.handle_events())
# def get_transcribe_url():
    # service = 'transcribe'
    # host = f'transcribestreaming.{REGION}.amazonaws.com:8443'
    # endpoint = f'wss://{host}/stream-transcription-websocket'
    # query = f'language-code={LANGUAGE_CODE}&media-encoding=pcm&sample-rate={SAMPLE_RATE}'

    # method = 'GET'
    # t = datetime.datetime.utcnow()
    # amz_date = t.strftime('%Y%m%dT%H%M%SZ')
    # date_stamp = t.strftime('%Y%m%d')

    # canonical_uri = '/stream-transcription-websocket'
    # canonical_querystring = f'{query}&X-Amz-Algorithm=AWS4-HMAC-SHA256'
    # canonical_querystring += f'&X-Amz-Credential={urllib.parse.quote_plus(credentials.access_key + "/" + date_stamp + "/" + REGION + "/" + service + "/aws4_request")}'
    # canonical_querystring += f'&X-Amz-Date={amz_date}&X-Amz-Expires=300&X-Amz-SignedHeaders=host'

    # canonical_headers = f'host:{host}'
    # signed_headers = 'host'
    # payload_hash = hashlib.sha256(('').encode('utf-8')).hexdigest()

    # canonical_request = '\n'.join([
    #     method,
    #     canonical_uri,
    #     canonical_querystring,
    #     canonical_headers,
    #     signed_headers,
    #     payload_hash
    # ])

    # algorithm = 'AWS4-HMAC-SHA256'
    # credential_scope = f'{date_stamp}/{REGION}/{service}/aws4_request'
    # string_to_sign = '\n'.join([
    #     algorithm,
    #     amz_date,
    #     credential_scope,
    #     hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
    # ])

    # signing_key = get_signature_key(credentials.secret_key, date_stamp, REGION, service)
    # signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # canonical_querystring += f'&X-Amz-Signature={signature}'

    # if credentials.token:
    #     canonical_querystring += f'&X-Amz-Security-Token={urllib.parse.quote_plus(credentials.token)}'

    # request_url = f'{endpoint}?{canonical_querystring}'
    # return jsonify({ 'url': request_url })

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    # try:
    await transcribe_stream(queue)
    # finally:
    #     mic_stream.stop_stream()
    #     mic_stream.close()
    #     pa_instance.terminate()

if __name__ == '__main__':
    app.run(port=3000)
