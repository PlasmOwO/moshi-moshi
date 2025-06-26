const startBtn = document.getElementById("start");
const outputDiv = document.getElementById("api-output");
const statusDiv = document.getElementById("status");

let socket = null;
let audioContext = null;
let processor = null;
let source = null;
let stream = null;

startBtn.onclick = async () => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    // Arrêter l'enregistrement
    stopRecording();
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    statusDiv.innerText = "Erreur accès microphone";
    console.error(err);
    return;
  }

  audioContext = new AudioContext({ sampleRate: 44100 });
  source = audioContext.createMediaStreamSource(stream);
  processor = audioContext.createScriptProcessor(4096, 1, 1);

  source.connect(processor);
  processor.connect(audioContext.destination);

  socket = new WebSocket("ws://13.38.29.146:8500/transcribe");
  socket.binaryType = "arraybuffer";

  socket.onopen = () => {
    statusDiv.innerText = "Enregistrement...";
    startBtn.innerText = "Arrêter";
    console.log("WebSocket connecté à FastAPI /transcribe");
  };

  socket.onmessage = (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      data = event.data; // texte brut
    }

    if (data && typeof data === "object" && data.type === "log") {
      outputDiv.innerText += `[LOG] ${data.message}\n`;
    } else if (typeof data === "string") {
      outputDiv.innerText += `${data}\n`;
    } else {
      outputDiv.innerText += `[Message non reconnu] ${event.data}\n`;
    }

    outputDiv.scrollTop = outputDiv.scrollHeight;
  };

  socket.onerror = (e) => {
    statusDiv.innerText = "Erreur WebSocket";
    console.error("WebSocket erreur :", e);
  };

  socket.onclose = () => {
    statusDiv.innerText = "Connexion WebSocket fermée";
    startBtn.innerText = "Démarrer";
    stopRecording();
  };

  processor.onaudioprocess = (e) => {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;

    const input = e.inputBuffer.getChannelData(0);
    const pcmData = downsampleBuffer(input, audioContext.sampleRate, 16000);
    const int16 = convertFloat32ToInt16(pcmData);
    socket.send(int16);
  };
};

function stopRecording() {
  if (processor) {
    processor.disconnect();
    processor.onaudioprocess = null;
    processor = null;
  }
  if (source) {
    source.disconnect();
    source = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (stream) {
    stream.getTracks().forEach(track => track.stop());
    stream = null;
  }
  if (socket) {
    if (socket.readyState === WebSocket.OPEN) socket.close();
    socket = null;
  }
  startBtn.innerText = "Démarrer";
  statusDiv.innerText = "Arrêté";
}

// Fonctions existantes
function downsampleBuffer(buffer, inputRate, outputRate) {
  if (outputRate === inputRate) return buffer;
  const sampleRateRatio = inputRate / outputRate;
  const newLength = Math.round(buffer.length / sampleRateRatio);
  const result = new Float32Array(newLength);
  for (let i = 0, j = 0; i < newLength; i++, j += sampleRateRatio) {
    result[i] = buffer[Math.floor(j)];
  }
  return result;
}

function convertFloat32ToInt16(buffer) {
  const l = buffer.length;
  const buf = new Int16Array(l);
  for (let i = 0; i < l; i++) {
    const s = Math.max(-1, Math.min(1, buffer[i]));
    buf[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return buf.buffer;
}
