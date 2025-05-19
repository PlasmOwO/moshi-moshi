import asyncio
import websockets
import pyaudio

async def send_audio():
    uri = "ws://0.0.0.0:8500/transcribe"  # Remplacez par l'URL de votre API
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket API")

        # Configuration de PyAudio pour capturer l'audio en temps réel
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,  # Format audio 16 bits
                        channels=1,             # Mono
                        rate=16000,             # Taux d'échantillonnage 16 kHz
                        input=True,             # Mode entrée (micro)
                        frames_per_buffer=1024) # Taille des chunks

        print("Streaming audio from microphone...")
        try:
            while True:
                
                print('a')
                audio_chunk = stream.read(1024, exception_on_overflow=False)  # Lire un chunk audio
                await websocket.send(audio_chunk)  # Envoyer le chunk au serveur
                response = await websocket.recv()  # Recevoir la transcription
                print(f"Transcription: {response}")
                
        except KeyboardInterrupt:
            print("Audio streaming stopped.")
        finally:
            stream.stop_stream()
            stream.close()
            p.terminate()

# Exécuter le client
if __name__ == "__main__":
    asyncio.run(send_audio())