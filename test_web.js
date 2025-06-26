const startBtn = document.getElementById("start");
const outputDiv = document.getElementById("api-output");
const statusDiv = document.getElementById("status");

startBtn.onclick = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new AudioContext({ sampleRate: 44100 });
  const source = audioContext.createMediaStreamSource(stream);
  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  source.connect(processor);
  processor.connect(audioContext.destination);

  // Récupération dynamique de l'URL WS
  const res = await fetch('/get-transcribe-url');
  const data = await res.json();
  const socketUrl = data.url;

  const socket = new WebSocket(socketUrl);

  socket.onopen = () => {
    statusDiv.innerText = "Enregistrement...";
    console.log("WebSocket connecté à FastAPI /transcribe");
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "log") {
        outputDiv.innerText += `[LOG] ${data.message}\n`;
      }
    } catch {
      // Texte brut : transcription/traduction
      outputDiv.innerText += `${event.data}\n`;
    }
    outputDiv.scrollTop = outputDiv.scrollHeight;
  };

  processor.onaudioprocess = (e) => {
    const input = e.inputBuffer.getChannelData(0);
    const pcmData = downsampleBuffer(input, audioContext.sampleRate, 16000);
    const int16 = convertFloat32ToInt16(pcmData);
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(int16);
    }
  };
};

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
