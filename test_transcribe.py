import asyncio
import pyaudio

from amazon_transcribe.client import TranscribeStreamingClient
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from amazon_transcribe.model import TranscriptEvent

class MyEventHandler(TranscriptResultStreamHandler):
    def __init__(self, transcript_result_stream):
        super().__init__(transcript_result_stream)
        self.transcriptions = []

    def set_stream(self, stream):
        self._output_stream = stream
        
    async def handle_transcript_event(self, transcript_event: TranscriptEvent):
        results = transcript_event.transcript.results
        for result in results:
            for alt in result.alternatives:
                self.transcriptions.append(alt.transcript)
                print(alt.transcript)

async def transcribe_stream(queue, handler):
    # Créez le client AWS Transcribe EU (Francfort)
    client = TranscribeStreamingClient(region="eu-central-1")
    
    #starting stream transcription
    stream = await client.start_stream_transcription(
        language_code="ja-JP",
        media_sample_rate_hz=16000,
        media_encoding="pcm",
    )
    
    if stream is None:
        raise RuntimeError("Failed to start stream transcription")

    #envoyer chunks a AWS Transcribe (stream 1)
    async def send_audio():
        while True:
            audio_chunk = await queue.get()
            if audio_chunk is None:  #signal de fin ? (TODO)
                break
            print("Sending audio chunk")  # Debug statement
            await stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
        await stream.input_stream.end_stream()
    
    # Instanciez le gestionnaire d'événements pour traiter les transcriptions en sortie
    handler.set_stream(stream.output_stream)
    
    await asyncio.gather(send_audio(), handler.handle_events())

def start_microphone_stream(queue, loop):
    # Initialisation de PyAudio
    pa = pyaudio.PyAudio()
    
    # La fonction callback est appelée dans un thread séparé par PyAudio
    def callback(in_data, frame_count, time_info, status):
        print("Received audio data")  # Debug statement
        loop.call_soon_threadsafe(queue.put_nowait, in_data)
        return (None, pyaudio.paContinue)
    
    # Ouvre le flux audio du micro avec les paramètres adaptés
    # (a parametrer pour minimiser sons ambiants)
    stream = pa.open(
        format=pyaudio.paInt16,   # 16 bits
        channels=1,               # Mono
        rate=16000,               # 16 kHz (à adapter si besoin)
        input=True,
        frames_per_buffer=1024,   # Taille du chunk
        stream_callback=callback,
    )
    stream.start_stream()
    return stream, pa

async def main():
    queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    
    mic_stream, pa_instance = start_microphone_stream(queue, loop)
    try:
        # Start the transcription stream and instantiate the handler with the output stream
        client = TranscribeStreamingClient(region="eu-central-1")
        stream = await client.start_stream_transcription(
            language_code="ja-JP",
            media_sample_rate_hz=16000,
            media_encoding="pcm",
        )
        handler = MyEventHandler(stream.output_stream)
        await transcribe_stream(queue, handler)
    finally:
        # Arrête et ferme le flux audio, puis termine PyAudio (atm via un CTRL C)
        mic_stream.stop_stream()
        mic_stream.close()
        with open("japanese.txt", "a") as f:
            for transcription in handler.transcriptions:
                f.write(transcription + "\n")
        pa_instance.terminate()

if __name__ == "__main__":
    asyncio.run(main())