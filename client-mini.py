import asyncio
import websockets
import pyaudio
import wave

async def send_audio():
    uri = "ws://0.0.0.0:8500/transcribe"  # Remplacez par l'URL de votre serveur
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket API")

        print("Streaming audio from microphone...")

        # Initialiser la file d'attente pour les chunks audio
        queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        # Liste pour stocker les chunks audio
        audio_chunks = []

        # Fonction pour démarrer le flux audio
        def start_microphone_stream(queue, loop):
            pa = pyaudio.PyAudio()

            def callback(in_data, frame_count, time_info, status):
                # Ajouter les chunks audio à la file d'attente
                loop.call_soon_threadsafe(queue.put_nowait, in_data)
                # Stocker les chunks dans la liste
                audio_chunks.append(in_data)
                return (None, pyaudio.paContinue)

            # Configurer le flux audio
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

        # Démarrer le flux audio
        stream, pa = start_microphone_stream(queue, loop)

        try:
            while True:
                # Récupérer un chunk audio depuis la file d'attente
                audio_chunk = await queue.get()
                # Envoyer le chunk audio au serveur via WebSocket
                await websocket.send(audio_chunk)

                # response = await websocket.recv()
                # print(f"Résultat reçu du serveur : {response}")

        except KeyboardInterrupt:
            print("Audio streaming stopped.")
        finally:
            # Fermer le flux audio
            stream.stop_stream()
            stream.close()
            pa.terminate()

            # Écrire les chunks audio dans un fichier WAV
            with wave.open("output.wav", "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(pa.get_sample_size(pyaudio.paInt16))  # Taille d'échantillon 16 bits
                wav_file.setframerate(16000)  # Taux d'échantillonnage 16 kHz
                wav_file.writeframes(b"".join(audio_chunks))  # Écrire tous les chunks
            print("Fichier WAV enregistré sous 'output.wav'.")

# Exécuter le client
if __name__ == "__main__":
    asyncio.run(send_audio())