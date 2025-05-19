from fastapi import FastAPI, WebSocket
import asyncio
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent
import boto3

app = FastAPI()

# AWS Transcribe client
transcribe_client = TranscribeStreamingClient(region="eu-central-1")

# AWS Translate client
translate_client = boto3.client('translate', region_name="eu-central-1")

# Gestionnaire personnalisé pour traiter les résultats de transcription
class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, transcript_result_stream, websocket: WebSocket):
        super().__init__(transcript_result_stream)
        self.websocket = websocket

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                original_text = alt.transcript
                print(f"Transcription (Japonais) : {original_text}")  # Afficher la transcription côté serveur

                # Traduire le texte en français
                response = translate_client.translate_text(
                    Text=original_text,
                    SourceLanguageCode="ja",
                    TargetLanguageCode="fr"
                )
                translated_text = response.get("TranslatedText", "")
                print(f"Traduction (Français) : {translated_text}")  # Afficher la traduction côté serveur

                # Envoyer la transcription et la traduction au client
                await self.websocket.send_text(f"Japonais : {original_text}\nFrançais : {translated_text}")

# WebSocket endpoint pour la transcription et la traduction en temps réel
@app.websocket("/transcribe")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")

    # Démarrer le flux AWS Transcribe
    stream = await transcribe_client.start_stream_transcription(
        language_code="ja-JP",          # Langue : Japonais
        media_sample_rate_hz=16000,    # Taux d'échantillonnage
        media_encoding="pcm",          # Format audio : PCM
    )

    # Créer une instance du gestionnaire pour traiter les transcriptions
    handler = MyEventHandler(stream.output_stream, websocket)

    async def send_audio():
        try:
            while True:
                # Recevoir des données audio depuis le WebSocket
                audio_chunk = await websocket.receive_bytes()
                #print(f"Received audio chunk of size: {len(audio_chunk)} bytes")  # Log pour vérifier les données reçues
                # Envoyer les chunks audio à AWS Transcribe
                await stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
        except Exception as e:
            print(f"WebSocket closed: {e}")
        finally:
            # Terminer le flux d'entrée
            await stream.input_stream.end_stream()

    # Gérer les événements de transcription et l'envoi des données audio en parallèle
    await asyncio.gather(send_audio(), handler.handle_events())