from fastapi import FastAPI, WebSocket
import asyncio, uvicorn
from translate_transcribe_fr import main # ta fonction existante
from asyncio import Queue

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API de transcription en temps réel en cours d'exécution."}

@app.websocket("/speech")
async def websocket_speech(websocket: WebSocket):
    await websocket.accept()
    print("🎤 Client connecté au WebSocket /speech")

    queue = Queue()

    async def receive_audio():
        try:
            while True:
                audio_chunk = await websocket.receive_bytes()
                await queue.put(audio_chunk)
        except Exception as e:
            print("❌ Déconnexion ou erreur :", e)
        finally:
            await queue.put(None)  # Fin du stream

    # On exécute la logique de transcription en parallèle de la réception
    # await asyncio.gather(
    #     receive_audio(),
    #     transcribe_stream(queue)
    # )
    asyncio.run(main())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7891)