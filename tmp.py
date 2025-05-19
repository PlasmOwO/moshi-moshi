import asyncio
from fastapi import FastAPI, WebSocket
from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

app = FastAPI()

# AWS Transcribe client
transcribe_client = TranscribeStreamingClient(region="eu-central-1")

# Gestionnaire personnalisé pour traiter les résultats de transcription
class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.websocket = websocket

    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        # Traiter les résultats de transcription
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                original_text = alt.transcript
                print(f"Transcription (Japonais) : {original_text}")  # Afficher la transcription côté serveur
                # Envoyer la transcription au client
                await self.websocket.send_text(original_text)

# WebSocket endpoint pour la transcription en temps réel
@app.websocket("/transcribe")
async def transcribe_audio(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection accepted")

    # Démarrer le flux AWS Transcribe
    stream = await transcribe_client.start_stream_transcription(
        language_code="ja-JP",          # Langue : Japonais
        media_sample_rate_hz=16000,    # Taux d'échantillonnage
        media_encoding="pcm",          # Format audio : PCM
    )

    # Créer une instance du gestionnaire pour traiter les transcriptions
    handler = MyEventHandler(websocket)

    async def send_audio():
        try:
            while True:
                # Recevoir des données audio depuis le WebSocket
                audio_chunk = await websocket.receive_bytes()
                print(f"Received audio chunk of size: {len(audio_chunk)} bytes")  # Log pour vérifier les données reçues
                # Envoyer les chunks audio à AWS Transcribe
                await stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
        except Exception as e:
            print(f"WebSocket closed: {e}")
        finally:
            # Terminer le flux d'entrée
            await stream.input_stream.end_stream()

    # Gérer les événements de transcription et l'envoi des données audio en parallèle
    await asyncio.gather(send_audio(), handler.handle_events())