import asyncio
import pyaudio
import boto3
import os
import aiofiles

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

# Client Amazon Translate
translate_client = boto3.client('translate', region_name="eu-central-1")

# Fichier pour stocker les transcriptions
TRANSCRIPTION_FILE = "transcriptions.txt"

# Gestionnaire personnalisé pour traiter et écrire les résultats de transcription
class MyEventHandler(TranscriptResultStreamHandler):
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                original_text = alt.transcript
                # Écrire dans le fichier
                async with aiofiles.open(TRANSCRIPTION_FILE, mode="a") as f:
                    await f.write(original_text + "\n")

async def transcribe_stream(queue):
    # Création client AWS Transcribe
    client = TranscribeStreamingClient(region="eu-central-1")
    
    stream = await client.start_stream_transcription(
        language_code="ja-JP",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )
    
    async def send_audio():
        while True:
            audio_chunk = await queue.get()
            if audio_chunk is None:  # Signal de fin
                break
            await stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
        await stream.input_stream.end_stream()
    
    handler = MyEventHandler(stream.output_stream)
    await asyncio.gather(send_audio(), handler.handle_events())

async def translate_file():
    """Lit le fichier de transcription et traduit son contenu."""
    already_translated = set()
    while True:
        if os.path.exists(TRANSCRIPTION_FILE):
            async with aiofiles.open(TRANSCRIPTION_FILE, mode="r") as f:
                lines = await f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and line not in already_translated:
                        # Traduire le texte
                        response = await asyncio.to_thread(
                            translate_client.translate_text,
                            Text=line,
                            SourceLanguageCode="ja",
                            TargetLanguageCode="fr"
                        )
                        translated_text = response.get("TranslatedText", "")
                        print(f"Original : {line}")
                        print(f"Traduction : {translated_text}\n")
                        already_translated.add(line)
        await asyncio.sleep(1)  # Pause pour éviter une boucle trop rapide

def start_microphone_stream(queue, loop):
    pa = pyaudio.PyAudio()
    
    def callback(in_data, frame_count, time_info, status):
        loop.call_soon_threadsafe(queue.put_nowait, in_data)
        return (None, pyaudio.paContinue)
    
    # Flux audio
    stream = pa.open(
        format=pyaudio.paInt16,   # 16 bits
        channels=1,               # Mono
        rate=16000,               # 16 kHz
        input=True,
        frames_per_buffer=1024,   # Taille du chunk
        stream_callback=callback,
    )
    stream.start_stream()
    return stream, pa

async def main():
    # Effacer le fichier de transcription au démarrage
    if os.path.exists(TRANSCRIPTION_FILE):
        os.remove(TRANSCRIPTION_FILE)
    
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    mic_stream, pa_instance = start_microphone_stream(queue, loop)
    try:
        # Lancer la transcription et la traduction en parallèle
        await asyncio.gather(
            transcribe_stream(queue),
            translate_file()
        )
    finally:
        mic_stream.stop_stream()
        mic_stream.close()
        pa_instance.terminate()

if __name__ == "__main__":
    asyncio.run(main())