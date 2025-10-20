import { useState, useRef, useCallback } from "react";

interface VoiceConfig {
  sampleRate?: number;
  timeSlice?: number;
  bufferSize?: number;
  numberOfChannels?: number;
  bitsPerSecond?: number;
  onAudioData?: (data: Blob) => void;
}

const vadFilter = (analyser: React.MutableRefObject<AnalyserNode | null>): boolean => {
  if (!analyser.current) return false;

  const dataArray = new Uint8Array(analyser.current.frequencyBinCount);
  analyser.current.getByteFrequencyData(dataArray);

  const sum = dataArray.reduce((acc, value) => acc + value, 0);
  const average = sum / dataArray.length;

  return average > 5;
};

export const useVoiceRecorder = ({
  sampleRate = 16000,
  timeSlice = 125,        // 250ms chunks
  bufferSize = 2048,      // Processing buffer size
  numberOfChannels = 1,   // Mono audio
  bitsPerSecond = 128000, // Target bitrate
  onAudioData,
}: VoiceConfig) => {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioContext = useRef<AudioContext | null>(null);
  const analyser = useRef<AnalyserNode | null>(null);
  const workletNode = useRef<AudioWorkletNode | null>(null);
  const sourceNode = useRef<MediaStreamAudioSourceNode | null>(null);
  const stream = useRef<MediaStream | null>(null);

  const startRecording = async () => {
    try {
      // Stop any existing recording
      await stopRecording();

      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate,
          channelCount: numberOfChannels,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      audioContext.current = new AudioContext({ 
        sampleRate,
        latencyHint: 'interactive'
      });

      analyser.current = audioContext.current.createAnalyser();
      analyser.current.fftSize = 2048;
      analyser.current.smoothingTimeConstant = 0.8;

      sourceNode.current = audioContext.current.createMediaStreamSource(stream.current);
      sourceNode.current.connect(analyser.current);

      await audioContext.current.audioWorklet.addModule("processor.js");
      workletNode.current = new AudioWorkletNode(audioContext.current, "processor", {
        processorOptions: {
          sampleRate,
          timeSlice,        // Pass timeSlice to processor
          bufferSize,       // Pass bufferSize to processor
          numberOfChannels,
          bitsPerSecond,
          // Calculate chunk size based on timeSlice
          // timeSlice(ms) * sampleRate(Hz) / 1000ms = samples per chunk
          chunkSize: Math.floor((timeSlice * sampleRate) / 1000),
        },
      });

      sourceNode.current.connect(workletNode.current);
      workletNode.current.connect(audioContext.current.destination);

      workletNode.current.port.onmessage = (event) => {
        const audioData = event.data;
        if (audioData && audioData.length > 0) {
          if (vadFilter(analyser)) {
            // Convert Float32 to Int16 with proper bit depth
            const pcmData = new Int16Array(audioData.length);
            for (let i = 0; i < audioData.length; i++) {
              const s = Math.max(-1, Math.min(1, audioData[i]));
              pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
            }

            // Calculate actual bit rate
            // const bitsPerSample = 16;
            // const actualBitRate = sampleRate * bitsPerSample * numberOfChannels;
            
            // Create PCM blob with specified format
            const pcmBlob = new Blob([pcmData.buffer], { 
              type: "audio/pcm" 
            });

            onAudioData?.(pcmBlob);
          }
        }
      };

      setIsRecording(true);
      setError(null);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start recording");
      console.error("Recording error:", err);
    }
  };

  const stopRecording = useCallback(async () => {
    try {
      if (stream.current) {
        stream.current.getTracks().forEach(track => track.stop());
        stream.current = null;
      }

      if (sourceNode.current) {
        sourceNode.current.disconnect();
        sourceNode.current = null;
      }

      if (workletNode.current) {
        workletNode.current.disconnect();
        workletNode.current = null;
      }

      if (analyser.current) {
        analyser.current.disconnect();
        analyser.current = null;
      }

      if (audioContext.current?.state !== 'closed') {
        await audioContext.current?.close();
        audioContext.current = null;
      }

      setIsRecording(false);
    } catch (err) {
      console.error("Error stopping recording:", err);
      setError("Failed to stop recording");
    }
  }, []);

  return {
    isRecording,
    error,
    startRecording,
    stopRecording,
  };
};