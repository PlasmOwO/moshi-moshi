const startBtn = document.getElementById("start");
const transcriptDiv = document.getElementById("transcript");

startBtn.onclick = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const audioContext = new AudioContext({ sampleRate: 44100 });
  const source = audioContext.createMediaStreamSource(stream);

  const processor = audioContext.createScriptProcessor(4096, 1, 1);
  source.connect(processor);
  processor.connect(audioContext.destination);

  const res = await fetch("/get-transcribe-url");
  const { url } = await res.json();
  const socket = new WebSocket(url);

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    const results = msg.Transcript?.Results || [];
    if (results.length > 0 && results[0].Alternatives.length > 0) {
      const transcript = results[0].Alternatives[0].Transcript;
      transcriptDiv.innerText = transcript;
    }
  };

  socket.onopen = () => {
    console.log("WebSocket connected to AWS Transcribe");
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
    buf[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
  }
  return buf.buffer;
}
